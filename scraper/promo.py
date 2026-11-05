"""Daily share assets for socials — zero required dependencies.

Generates from the latest data/surveys.json snapshot:
  * promo.txt  — ready-to-paste caption for WhatsApp status / X / TikTok bio
  * promo.svg  — 800x800 share card image (pure vector, works everywhere)
  * promo.html — pretty preview page (also fine to screenshot by hand)
  * promo.png  — 1080x1080 only when Pillow is installed (optional)

Everything is derived from real numbers of the day - never promises.
"""
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# EDIT ME - where your link hub lives (goes into captions/cards)
SITE_URL = "https://elliotedy.github.io/survey-hunter/links.html"
BRAND = "Survey Hunter"
HANDLE = "@Elliotedy"

VERT_LABEL = {"survey": "💰 surveys", "affiliate": "🤝 affiliate", "freelance": "💼 freelance"}


def _top_picks(snapshot):
    """Two surveys + two affiliate + one freelance, reachable-first."""
    out = []
    for want, n in (("survey", 2), ("affiliate", 2), ("freelance", 1)):
        picked = 0
        for p in snapshot.get("nigeria_open", []):
            if p.get("vertical", "survey") == want and picked < n:
                out.append(p)
                picked += 1
    return out


def caption(snapshot):
    s = snapshot.get("summary", {})
    date = str(snapshot.get("generated_at", ""))[:10]
    lines = [
        f"🎯 {BRAND} - {date}",
        f"{s.get('nigeria_open', 0)} platforms OPEN to Nigeria today"
        f" (of {s.get('total', 0)} tracked)",
    ]
    for v, label in VERT_LABEL.items():
        n = s.get("by_vertical", {}).get(v, 0)
        if n:
            lines.append(f"   {label}: {n}")
    lines.append("")
    lines.append("⭐ TODAY'S PICKS")
    for p in _top_picks(snapshot):
        hook = p.get("earn_model") or p.get("ref_program") or p.get("min_payout") or ""
        lines.append(f"• {p['name']} - {hook[:70]}")
    lines.append("")
    lines.append(f"🔗 full daily list: {SITE_URL}")
    lines.append("payout rules change - always verify at signup")
    return "\n".join(lines)


def svg(snapshot):
    s = snapshot.get("summary", {})
    date = str(snapshot.get("generated_at", ""))[:10]
    picks = _top_picks(snapshot)
    pick_rows = []
    y = 560
    row_ys = []
    for p in picks:
        row_ys.append(y)
        y += 44
    pick_rows = [
        f'<text x="60" y="{ry + 22}" font-family="Segoe UI, Roboto, Arial" '
        f'font-size="21" fill="#cfe8dd">• {html.escape(p["name"][:30])} '
        f'<tspan fill="#93a8a4" font-size="16">- {html.escape((p.get("earn_model") or p.get("ref_program") or p.get("min_payout", ""))[:34])}</tspan></text>'
        for p, ry in zip(picks, row_ys)
    ]
    card = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0d1415"/>
      <stop offset="1" stop-color="#0b0f10"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.34" r="0.4">
      <stop offset="0" stop-color="#008751" stop-opacity="0.55"/>
      <stop offset="1" stop-color="#008751" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="800" height="800" fill="url(#bg)"/>
  <rect x="1.5" y="1.5" width="797" height="797" fill="none" stroke="#233236" stroke-width="3"/>
  <circle cx="400" cy="272" r="215" fill="url(#glow)"/>
  <circle cx="400" cy="272" r="150" fill="none" stroke="#2bd576" stroke-width="3" opacity="0.75"/>
  <circle cx="400" cy="272" r="112" fill="none" stroke="#008751" stroke-width="3" opacity="0.9"/>
  <circle cx="400" cy="272" r="12" fill="#2bd576"/>
  <text x="400" y="252" text-anchor="middle" font-family="Segoe UI, Roboto, Arial" font-size="84" font-weight="bold" fill="#2bd576">{s.get('nigeria_open', 0)}</text>
  <text x="400" y="292" text-anchor="middle" font-family="Segoe UI, Roboto, Arial" font-size="20" fill="#e8f0ef"> Survey platforms OPEN to Nigeria</text>
  <text x="400" y="318" text-anchor="middle" font-family="Segoe UI, Roboto, Arial" font-size="16" fill="#7d948f">{s.get('total', 0)} tracked · re-checked today ({html.escape(date)})</text>
  <text x="400" y="396" text-anchor="middle" font-family="Segoe UI, Roboto, Arial" font-size="20" fill="#dbe9e5">of which 💰 {s.get('by_vertical', {}).get('survey', 0)} · 🤝 {s.get('by_vertical', {}).get('affiliate', 0)} · 💼 {s.get('by_vertical', {}).get('freelance', 0)}</text>
  <text x="60" y="500" font-family="Segoe UI, Roboto, Arial" font-size="24" font-weight="bold" fill="#2bd576">⭐ TODAY'S PICKS</text>
  {"".join(pick_rows)}
  <text x="60" y="708" font-family="Segoe UI, Roboto, Arial" font-size="19" font-weight="bold" fill="#ffd166">🔗 link in bio {html.escape(HANDLE)} → {html.escape(SITE_URL.replace('https://', ''))}</text>
  <text x="60" y="742" font-family="Segoe UI, Roboto, Arial" font-size="13" fill="#5f7370">{html.escape(BRAND)} · daily notice - verify at signup before work.</text>
</svg>"""
    return card


def html_page(snapshot):
    s = snapshot.get("summary", {})
    date = str(snapshot.get("generated_at", ""))[:10]
    picks = _top_picks(snapshot)
    chips = (
        f'<span class="chip">💰 {s.get("by_vertical", {}).get("survey", 0)} surveys</span>'
        f'<span class="chip">🤝 {s.get("by_vertical", {}).get("affiliate", 0)} affiliate</span>'
        f'<span class="chip">💼 {s.get("by_vertical", {}).get("freelance", 0)} freelance</span>'
    )
    rows = "".join(
        f'<div class="pick"><div class="pickname">{html.escape(p["name"])}'
        f'<span class="pill">{"💸 ref" if p.get("your_ref_url") else html.escape(p.get("type", "")[:40])}</span></div>'
        f'<div class="pickhint">{html.escape(p.get("earn_model") or p.get("ref_program") or "")}</div>'
        f'<a class="cta" href="{html.escape(p.get("your_ref_url") or p["url"])}" target="_blank" rel="noopener">open ↗</a></div>'
        for p in picks
    )
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(BRAND)} - daily share page</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎯</text></svg>">
<style>
*{{box-sizing:border-box}}
a{{color:inherit;text-decoration:none}}
body{{margin:0;background:#0b0f10;color:#e8f0ef;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}}
.wrap{{max-width:640px;margin:0 auto;padding:30px 18px 44px}}
.hdr{{text-align:center}}
.num{{font-size:64px;font-weight:800;color:#2bd576;line-height:1}}
.sub{{color:#93a8a4;margin-top:6px;font-size:15px}}
.chips{{text-align:center;margin:14px 0}}
.chip{{display:inline-block;background:#131a1c;border:1px solid #233236;color:#a9c0bb;border-radius:999px;padding:6px 12px;font-size:12.5px;margin:0 4px 6px}}
.h{{color:#2bd576;font-weight:800;margin:26px 0 8px;font-size:15px;letter-spacing:.3px}}
.pick{{background:linear-gradient(180deg,#182125,#131a1c);border:1px solid #233236;border-radius:14px;padding:13px 15px;margin-bottom:9px;position:relative}}
.pickname{{font-weight:800;font-size:15px}}
.pill{{color:#ffd166;font-size:11px;font-weight:800;margin-left:6px}}
.pickhint{{color:#93a8a4;font-size:12px;line-height:1.45;margin-top:4px;max-width:82%}}
.cta{{position:absolute;top:12px;right:12px;color:#06130c;background:linear-gradient(135deg,#2bd576,#008751);border-radius:9px;padding:6px 10px;font-weight:800;font-size:12px}}
.foot{{margin-top:26px;text-align:center;color:#5f7370;font-size:11.5px;line-height:1.6}}
.biglink{{display:block;text-align:center;margin-top:20px;padding:13px;border-radius:12px;background:linear-gradient(135deg,#ffd166,#ff9f43);color:#06130c;font-weight:800;text-decoration:none}}
</style></head><body>
<div class="wrap">
  <div class="hdr">
    <div class="num">{s.get('nigeria_open', 0)}</div>
    <div class="sub">platforms open to Nigeria<br>{s.get('total', 0)} tracked · updated {html.escape(date)}</div>
    <div class="chips">{chips}</div>
  </div>
  <div class="h">⭐ TODAY'S PICKS</div>
  {rows}
  <a class="biglink" href="{html.escape(SITE_URL)}">See all {s.get('total', 0)} platforms ↗ {html.escape(HANDLE)}</a>
  <div class="foot">{html.escape(BRAND)} · refreshed daily · payout rules change - verify at signup<br><a style="color:#2bd576" href="index.html">full radar</a> · <a style="color:#2bd576" href="links.html">link hub</a></div>
</div>
</body></html>"""


def png(snapshot, out):
    """Optional 1080x1080 PNG — silently skipped when Pillow/fonts missing."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None
    s = snapshot.get("summary", {})
    date = str(snapshot.get("generated_at", ""))[:10]

    font_candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf",
        "/system/fonts/Roboto-Bold.ttf", "/system/fonts/Roboto-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    font_path = next((f for f in font_candidates if Path(f).exists()), None)
    if not font_path:
        return None
    emoji_ok = any(Path(p).exists() for p in
                   [r"C:\Windows\Fonts\seguiemj.ttf"])  # best effort

    img = Image.new("RGB", (1080, 1080), (11, 15, 16))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 1076, 1076], outline=(35, 50, 54), width=4)

    f_num = ImageFont.truetype(font_path, 210)
    f_head = ImageFont.truetype(font_path, 44)
    f_mid = ImageFont.truetype(font_path, 30)
    f_small = ImageFont.truetype(font_path, 22)
    f_tiny = ImageFont.truetype(font_path, 18)

    cx, cy = 540, 330
    for r, color, wdt in ((330, (43, 213, 118, 60), 6),
                          (260, (0, 135, 81, 160), 6),
                          (20, (43, 213, 118, 255), 12)):
        try:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=wdt)
        except Exception:
            pass

    num = str(s.get("nigeria_open", 0))
    d.text((cx, cy - 40), num, font=f_num, fill=(43, 213, 118), anchor="mm")
    d.text((cx, cy + 95), "survey platforms OPEN to Nigeria", font=f_mid,
           fill=(232, 240, 239), anchor="mm")
    d.text((cx, cy + 140), f"{s.get('total', 0)} tracked · re-checked today ({date})",
           font=f_tiny, fill=(125, 148, 143), anchor="mm")

    d.text((100, 560), "TODAY'S PICKS", font=f_head, fill=(245, 209, 97))
    y = 640
    for p in _top_picks(snapshot):
        hook = p.get("earn_model") or p.get("ref_program") or p.get("min_payout", "")
        d.text((100, y), f"• {p['name']}  -  {hook[:38]}", font=f_mid, fill=(207, 232, 221))
        y += 56

    d.text((100, 950), f"LINK IN BIO {HANDLE}", font=f_mid, fill=(255, 209, 102))
    d.text((100, 1000), f"{BRAND} - daily notice, payout rules change - verify at signup",
           font=f_tiny, fill=(95, 115, 112))
    img.save(out, "PNG")
    return out


def generate_promo(snapshot, out_dir=ROOT):
    out_dir = Path(out_dir)
    wrote = []
    files = {
        out_dir / "promo.txt": caption(snapshot),
        out_dir / "promo.svg": svg(snapshot),
        out_dir / "promo.html": html_page(snapshot),
    }
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
        wrote.append(path)
    try:
        png_path = png(snapshot, out_dir / "promo.png")
    except Exception:
        png_path = None  # any Pillow-related issue must never break the run
    if png_path:
        wrote.append(png_path)
    return wrote
