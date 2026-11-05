"""Send the daily digest to a Telegram chat via the Bot API."""
import html
import requests

API_BASE = "https://api.telegram.org"
MAX_LEN = 3900  # Telegram hard limit is 4096; keep headroom.


def send_text(token, chat_id, text):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    resp = requests.post(f"{API_BASE}/bot{token}/sendMessage", json=payload, timeout=30)
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data.get('description', data)}")
    return data


def _link(name, url):
    return f'<a href="{html.escape(url, quote=True)}">{html.escape(name)}</a>'


VERTICAL_EMOJI = {"survey": "💰", "affiliate": "🤝", "freelance": "💼"}


def _entry_line(entry):
    # If the owner configured their own referral link, use it for clicks.
    link = entry.get("your_ref_url") or entry.get("url", "")
    emoji = VERTICAL_EMOJI.get(entry.get("vertical", "survey"), "▪")
    parts = [f"▪ {emoji} {_link(entry['name'], link)}"]
    if entry.get("earn_model"):
        parts.append(html.escape(str(entry["earn_model"])[:150]))
    elif entry.get("min_payout"):
        parts.append(f"min {entry['min_payout']}")
    if entry.get("status") == "error":
        parts.append(f"⚠ check failed ({entry.get('check_detail', '')})")
    line = " — ".join(parts)
    note = entry.get("notes", "")
    if note:
        line += f"\n<i>{html.escape(note[:180])}</i>"
    if entry.get("ref_program"):
        line += f"\n<b>ref:</b> {html.escape(str(entry['ref_program'])[:120])}"
    return line


def digest_lines(snapshot):
    s = snapshot.get("summary", {})
    site = snapshot["generated_at"][:10]
    lines = [
        "🎯 <b>Survey Hunter — daily digest</b> 🇳🇬",
        f"<i>{site} · {s.get('nigeria_open', 0)} open · "
        f"{s.get('restricted', 0)} restricted · {s.get('uncertain', 0)} uncertain</i>",
        "",
        "🟢 <b>OPEN TO NIGERIANS</b>",
    ]
    for e in snapshot.get("nigeria_open", []):
        lines.append(_entry_line(e))

    lines += ["", "🔴 <b>RESTRICTED (skip these)</b>"]
    for e in snapshot.get("restricted", []):
        lines.append(_entry_line(e))

    uncertain = snapshot.get("uncertain", [])
    if uncertain:
        lines += ["", "❔ <b>UNCERTAIN (verify at signup)</b>"]
        for e in uncertain:
            lines.append(_entry_line(e))

    lines += [
        "",
        "⚡ Full list + live updates: <i>your GitHub Pages site</i>",
        "<i>Payout limits change often - always confirm at signup.</i>",
    ]
    return lines


def _chunks(lines):
    chunks, current = [], ""
    for line in lines:
        if current and len(current) + len(line) + 1 > MAX_LEN:
            chunks.append(current.rstrip())
            current = ""
        current += line + "\n"
    if current.strip():
        chunks.append(current.rstrip())
    return chunks


def send_digest(token, chat_id, snapshot):
    """Send the digest, splitting across messages if needed. Returns count."""
    sent = 0
    for chunk in _chunks(digest_lines(snapshot)):
        send_text(token, chat_id, chunk)
        sent += 1
    return sent
