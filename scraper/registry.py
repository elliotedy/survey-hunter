"""Load and validate the survey platform registry (data/sources.json)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SOURCES_FILE = DATA_DIR / "sources.json"
OUTPUT_FILE = DATA_DIR / "surveys.json"


def load_sources(path=SOURCES_FILE):
    """Return a list of validated platform dicts."""
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)

    platforms = data.get("platforms", [])
    if not isinstance(platforms, list):
        raise ValueError("sources.json must contain a 'platforms' list")

    cleaned = []
    for p in platforms:
        for key in ("id", "name", "url"):
            if not p.get(key):
                raise ValueError(f"Platform entry missing '{key}': {p}")
        if p.get("curated_open") not in (True, False, None):
            raise ValueError(
                f"{p['id']}: curated_open must be true, false or null"
            )
        p.setdefault("type", "Survey site")
        p.setdefault("min_payout", "?")
        p.setdefault("payout_methods", "?")
        p.setdefault("notes", "")
        cleaned.append(p)
    return cleaned


def save_sources(platforms, path=SOURCES_FILE):
    """Rewrite sources.json (used to normalise the file after edits)."""
    with Path(path).open("w", encoding="utf-8") as f:
        json.dump({"platforms": platforms}, f, indent=2, ensure_ascii=False)
