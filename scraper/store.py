"""Classify platforms into Nigeria buckets and write data/surveys.json."""
import json
from datetime import datetime, timezone

from .registry import OUTPUT_FILE

BUCKETS = ("nigeria_open", "restricted", "uncertain")


def categorize(platform):
    """Two-plus-one classification for a single platform dict.

    Rules (deliberately simple and explainable):
    - curated flag true  -> nigeria_open (downgraded to uncertain if the
                            live check found geo-block language)
    - curated flag false -> restricted (page problems do not flip this)
    - curated flag null  -> uncertain
    """
    curated = platform.get("curated_open")
    if curated is True:
        if platform.get("block_signal"):
            return "uncertain"
        return "nigeria_open"
    if curated is False:
        return "restricted"
    return "uncertain"


def build_snapshot(platforms):
    """Return the full daily snapshot dict for the website + Telegram."""
    groups = {name: [] for name in BUCKETS}
    for p in platforms:
        merged = dict(p)
        merged["category"] = categorize(p)
        groups[merged["category"]].append(merged)

    # Reachable + freshly checked platforms float to the top of each list.
    for name in BUCKETS:
        groups[name].sort(
            key=lambda p: (p.get("status") != "ok", p.get("name", "").lower())
        )

    summary = {
        "total": len(platforms),
        "nigeria_open": len(groups["nigeria_open"]),
        "restricted": len(groups["restricted"]),
        "uncertain": len(groups["uncertain"]),
        "checked": sum(1 for p in platforms if p.get("status") in ("ok", "error")),
        "errors": sum(1 for p in platforms if p.get("status") == "error"),
    }

    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "summary": summary,
    }
    for name in BUCKETS:
        clean = []
        for p in groups[name]:
            entry = {
                "id": p["id"],
                "name": p["name"],
                "url": p["url"],
                "type": p.get("type", ""),
                "min_payout": p.get("min_payout", ""),
                "payout_methods": p.get("payout_methods", ""),
                "notes": p.get("notes", ""),
                "curated_open": p.get("curated_open"),
                "status": p.get("status", "unchecked"),
                "checked_at": p.get("checked_at"),
                "block_signal": bool(p.get("block_signal")),
                "nigeria_mentioned": bool(p.get("nigeria_mentioned")),
                "check_detail": p.get("check_detail", ""),
            }
            clean.append(entry)
        snapshot[name] = clean
    return snapshot


def write_snapshot(snapshot, path=OUTPUT_FILE):
    import os

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return path
