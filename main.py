#!/usr/bin/env python3
"""Survey Hunter CLI.

Daily survey availability tracker for Nigeria.

Examples:
    python main.py                     # full check + build data/surveys.json
    python main.py --skip-check        # offline: rebuild snapshot from sources only
    python main.py --send-telegram     # send today's digest to Telegram
    python main.py --skip-check --send-telegram   # reuse snapshot, send digest

Environment (needed only for --send-telegram):
    TELEGRAM_BOT_TOKEN   from @BotFather
    TELEGRAM_CHAT_ID     your chat id (see README)
"""
import argparse
import os
import sys
from datetime import datetime, timezone

from scraper import telegram
from scraper.checker import run_checks
from scraper.registry import OUTPUT_FILE, load_sources
from scraper.store import build_snapshot, write_snapshot

# Windows/Termux consoles can be picky about emoji; normalise stdout.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def now_utc():
    return datetime.now(timezone.utc)


def finalize(platforms, skip_check, workers):
    """Optionally live-check, then categorise and write the snapshot."""
    if skip_check:
        stamp = now_utc().isoformat(timespec="seconds")
        for p in platforms:
            p.setdefault("status", "unchecked")
            p.setdefault("checked_at", None)
            p.setdefault("block_signal", False)
            p.setdefault("nigeria_mentioned", False)
            p.setdefault("check_detail", "skipped (offline run)")
            _ = stamp  # keep timestamps absent; the site shows "not checked yet"
    else:
        print(f"[{now_utc():%H:%M:%S}] Checking {len(platforms)} platforms "
              f"with {workers} workers ...")
        platforms = run_checks(platforms, workers=workers)

    snapshot = build_snapshot(platforms)
    out = write_snapshot(snapshot, OUTPUT_FILE)
    s = snapshot["summary"]
    print(f"[{now_utc():%H:%M:%S}] Snapshot written -> {out}")
    print(f"    total={s['total']}  open_to_NG={s['nigeria_open']}  "
          f"restricted={s['restricted']}  uncertain={s['uncertain']}  "
          f"check_errors={s['errors']}")
    return snapshot


def send(snapshot):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("!! Telegram not configured - set TELEGRAM_BOT_TOKEN and "
              "TELEGRAM_CHAT_ID environment variables (see README).")
        return False
    messages = telegram.send_digest(token, chat_id, snapshot)
    print(f"[{now_utc():%H:%M:%S}] Telegram digest sent ({messages} message[s]).")
    return True


def main():
    parser = argparse.ArgumentParser(description="Survey Hunter daily tracker")
    parser.add_argument("--skip-check", action="store_true",
                        help="skip network live checks (offline mode)")
    parser.add_argument("--send-telegram", action="store_true",
                        help="send the Telegram digest after building the snapshot")
    parser.add_argument("--auto", action="store_true",
                        help="headless marker used by run-today.bat / Task Scheduler (no-op)")
    parser.add_argument("--workers", type=int, default=8,
                        help="parallel HTTP workers (default 8)")
    args = parser.parse_args()

    platforms = load_sources()
    print(f"[{now_utc():%H:%M:%S}] Loaded {len(platforms)} platforms "
          f"from data/sources.json")

    if args.skip_check and OUTPUT_FILE.exists():
        # Digest-only run: keep today's real check results as they are.
        import json
        with OUTPUT_FILE.open("r", encoding="utf-8") as f:
            snapshot = json.load(f)
        print(f"[{now_utc():%H:%M:%S}] Reusing existing snapshot "
              f"({OUTPUT_FILE.name}) - no checks performed")
    else:
        snapshot = finalize(platforms, args.skip_check, args.workers)

    # Keep the shareable link-in-bio page in sync with the snapshot.
    # (Do this every run so manual edits/keyword changes propagate.)
    from scraper.links import generate_links
    links_path = generate_links(snapshot)
    print(f"[{now_utc():%H:%M:%S}] Link hub written -> {links_path}")

    # Daily social share assets (caption + card images).
    from scraper.promo import generate_promo
    promo_paths = generate_promo(snapshot)
    print(f"[{now_utc():%H:%M:%S}] Promo assets -> "
          f"{', '.join(p.name for p in promo_paths)}")

    if args.send_telegram:
        send(snapshot)


if __name__ == "__main__":
    main()
