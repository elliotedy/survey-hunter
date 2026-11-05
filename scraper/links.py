"""Generate links.html - a link-in-bio page fed by the daily snapshot.

Rebuilt automatically on every run (CLI, Termux, GitHub Actions), so the
page you drop in your social bios is always consistent with today's data.
"""
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "links.html"

# EDIT ME - how your page presents YOU on socials
PROFILE = {
    "name": "Elli 🇳🇬",
    "handle": "@Elliotedy",
    "tagline": "Daily side-hustle radar: surveys, affiliate deals & freelance gigs - vetted for Nigeria.",
    "cta_note": "Come back daily - the list refreshes itself. Links marked 💸 support this page.",
}

SECTIONS = [
    ("affiliate", "🤝 Partner programs (earns you money)", "Affiliate & referral programs that accept Nigerian signups. Using these links supports the page 💸."),
    ("survey", "💰 Surveys open to Nigeria", "Real survey platforms where Nigerian accounts actually get invites."),
    ("freelance", "💼 Freelance & remote work", "Sell your skills in USD - the bigger long-term money."),
]

PAGE_CSS = """
* { box-sizing: border-box; }
a { color: inherit; text-decoration: none; }
body {
  margin: 0;
  background: #0b0f10;
  color: #e8f0ef;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
  padding-bottom: 40px;
}
.wrap { max-width: 560px; margin: 0 auto; padding: 26px 16px; }
header { text-align: center; margin-bottom: 22px; }
.avatar {
  width: 84px; height: 84px; border-radius: 50%;
  background: linear-gradient(135deg, #008751, #2bd576);
  display: flex; align-items: center; justify-content: center;
  font-size: 40px; margin: 0 auto 12px;
  box-shadow: 0 0 24px rgba(43, 213, 118, .35);
}
h1 { font-size: 22px; margin: 0 0 4px; }
.handle { color: #93a8a4; font-size: 13px; }
.tagline { color: #a9c0bb; font-size: 14px; line-height: 1.5; margin-top: 10px; }
.sechead {
  font-size: 14px; font-weight: 800; letter-spacing: .2px;
  margin: 26px 2px 10px; color: #dff0ea;
}
.secsub { color: #7d948f; font-size: 12px; margin: -6px 2px 10px; line-height: 1.45; }
.row {
  display: flex; align-items: center; gap: 10px;
  background: #131a1c; border: 1px solid #233236;
  border-radius: 14px; padding: 12px 14px; margin-bottom: 8px;
  text-decoration: none; transition: transform .08s ease, border-color .15s ease;
}
.row:hover { transform: translateY(-1px); border-color: #2e464b; }
.row .arrow { color: #2bd576; font-weight: 800; margin-left: auto; }
.rowname { font-weight: 800; font-size: 14.5px; }
.rowhint { display: block; color: #93a8a4; font-size: 11.5px; margin-top: 3px; line-height: 1.4; }
.pill {
  display: inline-block; font-size: 10.5px; font-weight: 800;
  border-radius: 999px; padding: 2px 8px; margin-left: 6px; vertical-align: 2px;
}
.pill.ref { background: rgba(255, 209, 102, .15); color: #ffd166; }
footer { text-align: center; color: #5f7370; font-size: 11px; margin-top: 30px; line-height: 1.6; }
footer a { color: #2bd576; text-decoration: none; }
"""


def _esc(s):
    return html.escape(str(s or ""))


def _row(p):
    link = p.get("your_ref_url") or p.get("url", "")
    hint = p.get("earn_model") or (f"min {p['min_payout']}" if p.get("min_payout") else "")
    ref = '<span class="pill ref">💸</span>' if p.get("your_ref_url") else ""
    hint_html = f'<span class="rowhint">{_esc(hint)}</span>' if hint else ""
    return (
        f'<a class="row" href="{_esc(link)}" target="_blank" rel="noopener">'
        f'<span><span class="rowname">{_esc(p.get("name"))}{ref}</span>{hint_html}</span>'
        f'<span class="arrow">↗</span></a>'
    )


def generate_links(snapshot, out=OUT):
    """Write links.html from the snapshot's nigeria_open list. Returns path."""
    body_parts = []
    for vertical, heading, sub in SECTIONS:
        items = [
            p for p in snapshot.get("nigeria_open", [])
            if p.get("vertical", "survey") == vertical
        ]
        if not items:
            continue
        body_parts.append(f'<div class="sechead">{html.escape(heading)}</div>')
        body_parts.append(f'<div class="secsub">{html.escape(sub)}</div>')
        body_parts.append("".join(_row(p) for p in items))

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(PROFILE['name'])} - side-hustle radar</title>
<meta name="description" content="Daily-updated survey, affiliate & freelance links for Nigerians.">
<meta property="og:title" content="{_esc(PROFILE['name'])} - daily side-hustle radar">
<meta property="og:description" content="{_esc(PROFILE['tagline'])}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎯</text></svg>">
<style>{PAGE_CSS}</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="avatar">🎯</div>
    <h1>{_esc(PROFILE['name'])}</h1>
    <div class="handle">{_esc(PROFILE['handle'])}</div>
    <div class="tagline">{_esc(PROFILE['tagline'])}</div>
  </header>
  {"".join(body_parts)}
  <footer>
    {_esc(PROFILE['cta_note'])}<br>
    Refreshed {html.escape(str(snapshot.get('generated_at', ''))[:10])} ·
    <a href="index.html">full radar ↗</a>
  </footer>
</div>
</body>
</html>
"""
    out = Path(out)
    out.write_text(page, encoding="utf-8")
    return out
