/* Survey Hunter — frontend renderer (vanilla JS, no build step). */
"use strict";

const TABS = [
  { id: "nigeria_open", label: "🟢 Open to Nigeria" },
  { id: "restricted", label: "🔴 Restricted" },
  { id: "uncertain", label: "❔ Uncertain" },
];
const VERTICALS = [
  { id: "all", label: "All streams" },
  { id: "survey", label: "💰 Surveys" },
  { id: "affiliate", label: "🤝 Affiliate" },
  { id: "freelance", label: "💼 Freelance" },
];
const VBADGE = { survey: "💰 Surveys", affiliate: "🤝 Affiliate", freelance: "💼 Freelance" };
const FIELDS = ["type", "min_payout", "payout_methods", "payout_via", "earn_model", "ref_program", "notes", "name"];

let ALL = null;
let currentTab = "nigeria_open";
let verticalFilter = "all";
let query = "";

const $cards = document.getElementById("cards");
const $tabs = document.getElementById("tabs");
const $vchips = document.getElementById("vchips");
const $stats = document.getElementById("stats");
const $search = document.getElementById("search");
const $updated = document.getElementById("updated");

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function whenLabel(iso) {
  if (!iso) return "not checked yet";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "unknown";
  const mins = Math.max(1, Math.round((Date.now() - then) / 60000));
  if (mins < 60) return `checked ${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `checked ${hours}h ago`;
  return `checked ${Math.round(hours / 24)}d ago`;
}

function dotClass(status) {
  return status === "ok" ? "ok" : status === "error" ? "err" : "unchecked";
}

function cardHTML(p) {
  const link = p.your_ref_url || p.url;
  const isRef = Boolean(p.your_ref_url);
  const vBadge = VBADGE[p.vertical || "survey"] || "";
  const errNote = p.status === "error" && p.check_detail
    ? `<div class="warn">⚠ Today's check failed (${esc(p.check_detail)}) — the site may be down, geo-blocking bots, or moving.</div>`
    : "";
  return `
  <article class="card">
    <div class="head">
      <a href="${esc(link)}" target="_blank" rel="noopener">${esc(p.name)}</a>
      <span class="dot ${dotClass(p.status)}" title="${esc(whenLabel(p.checked_at))}"></span>
    </div>
    <div class="badges">
      <span class="badge type">${esc(p.type)}</span>
      <span class="badge v-${esc(p.vertical || "survey")}">${esc(vBadge)}</span>
      ${p.min_payout ? `<span class="badge money">💵 min ${esc(p.min_payout)}</span>` : ""}
      ${p.ref_program ? `<span class="badge ref">🤝 ref: ${esc(p.ref_program)}</span>` : ""}
      ${isRef ? `<span class="badge alias">💸 your link is live</span>` : ""}
    </div>
    ${p.earn_model ? `<div class="earnline">💹 ${esc(p.earn_model)}</div>` : ""}
    ${(p.payout_methods || p.payout_via) ? `<div class="meta"><span>💳 ${esc(p.payout_methods || p.payout_via)}</span></div>` : ""}
    ${errNote}
    <div class="notes">${esc(p.notes)}</div>
    <div class="meta">
      <span>${esc(whenLabel(p.checked_at))}</span>
      ${p.nigeria_mentioned ? "<span>🇳🇬 mentioned on site today</span>" : ""}
    </div>
    <a class="visit ${p.status === "error" ? "dim" : ""}" href="${esc(link)}"
       target="_blank" rel="noopener">Open ${isRef ? "your link 💸" : "site"} ↗</a>
  </article>`;
}

function emptyHTML(tab) {
  const words = { nigeria_open: "open to Nigerians", restricted: "restricted", uncertain: "uncertain" };
  return `<div class="empty">No ${words[tab]} platforms match your search.</div>`;
}

function helpHTML() {
  return `
  <div class="help">
    <p><strong>No data found (data/surveys.json is missing or unreachable).</strong></p>
    <p>To generate it locally run:</p>
    <p><code>python main.py</code> — then open this page via a tiny server:
       <code>python -m http.server 8080</code></p>
    <p>On GitHub this file is refreshed automatically every day by
       <strong>Actions → “Daily survey refresh”</strong>. Enable GitHub Pages
       (Settings → Pages → main / root) and the site goes live for free.</p>
  </div>`;
}

function currentPlatformList() {
  if (!ALL) return [];
  return ALL[currentTab] || [];
}

function filtered() {
  const q = query.trim().toLowerCase();
  let list = currentPlatformList();
  if (verticalFilter !== "all") {
    list = list.filter((p) => (p.vertical || "survey") === verticalFilter);
  }
  if (!q) return list;
  return list.filter((p) => {
    const hay = FIELDS.map((f) => String(p[f] ?? "")).join(" ").toLowerCase();
    return hay.includes(q);
  });
}

function renderStats() {
  const s = (ALL && ALL.summary) || {};
  const chip = (num, lab, cls) =>
    `<div class="chip ${cls}"><div class="num">${num}</div><div class="lab">${lab}</div></div>`;
  $stats.innerHTML =
    chip(s.total ?? "—", "Tracked sites", "") +
    chip(s.nigeria_open ?? "—", "Open to NG", "open") +
    chip(s.restricted ?? "—", "Restricted", "restricted") +
    chip(s.uncertain ?? "—", "Uncertain", "uncertain");
}

function renderTabs() {
  const s = (ALL && ALL.summary) || {};
  $tabs.innerHTML = TABS.map((t) => {
    const count = s[t.id] ?? (ALL && ALL[t.id] ? ALL[t.id].length : 0);
    return `<button class="tab ${t.id === currentTab ? "active" : ""}"
              role="tab" data-tab="${t.id}">
              ${t.label}<span class="count">${count}</span></button>`;
  }).join("");
  $tabs.querySelectorAll(".tab:not(.secondary)").forEach((btn) => {
    btn.addEventListener("click", () => {
      currentTab = btn.dataset.tab;
      render();
    });
  });
}

function renderVchips() {
  if (!$vchips) return;
  const counts = {};
  for (const key of ["nigeria_open", "restricted", "uncertain"]) {
    (ALL[key] || []).forEach((p) => {
      const v = p.vertical || "survey";
      counts[v] = (counts[v] || 0) + 1;
    });
  }
  $vchips.innerHTML = VERTICALS.map((v) => {
    const count = v.id === "all" ? (ALL.summary?.total ?? "—") : (counts[v.id] ?? 0);
    return `<button class="tab secondary ${v.id === verticalFilter ? "active" : ""}"
              data-vertical="${v.id}">${v.label}<span class="count">${count}</span></button>`;
  }).join("");
  $vchips.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      verticalFilter = btn.dataset.vertical;
      render();
    });
  });
}

function renderCards() {
  const list = filtered();
  $cards.innerHTML = list.length
    ? list.map(cardHTML).join("")
    : currentPlatformList().length
      ? emptyHTML(currentTab)
      : (ALL ? emptyHTML(currentTab) : helpHTML());
}

function render() {
  if (!ALL) return;
  renderStats();
  renderTabs();
  renderVchips();
  renderCards();
  if (ALL.generated_at) {
    const t = new Date(ALL.generated_at);
    $updated.textContent = `updated ${t.toLocaleString()}`;
  }
}

async function load() {
  try {
    const res = await fetch("data/surveys.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    ALL = await res.json();
    if (!ALL || !Array.isArray(ALL.nigeria_open)) throw new Error("bad schema");
    render();
  } catch (err) {
    $updated.textContent = "no data yet";
    $cards.innerHTML = helpHTML();
  }
}

$search.addEventListener("input", (e) => {
  query = e.target.value;
  renderCards();
});

load();
