#!/usr/bin/env python3
"""Telegram bot listener — makes the bot ANSWER you (not just broadcast).

Commands it answers (only from YOUR chat id):
  /start  /hi          -> online confirmation
  /today               -> live mini list from data/surveys.json
  /links               -> your link hub + radar URLs
  /help                -> command menu

Modes:
  python bot_listener.py --once      # drain pending messages and exit
                                     # (used by the GitHub Action daily)
  python bot_listener.py             # long-poll forever (PC logon / Termux)

NOTE: run the listener in ONE place at a time (PC *or* Termux) — two
listeners polling the same bot cause harmless but noisy 409 conflicts.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

from scraper.promo import SITE_URL
from scraper.registry import OUTPUT_FILE

API = "https://api.telegram.org"
ROOT = Path(__file__).resolve().parent  # script sits at the repo root
# Offset state lives in the REPO so GitHub Actions runs never re-answer
# old messages; locally it updates too - commit it now and then.
STATE_FILE = ROOT / "data" / "listener_offset.txt"
LOCK_FILE = ROOT / "config" / ".listener.lock"
MAX_LEN = 3800

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _pid_alive(pid):
    if not pid or pid <= 1:
        return False
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True  # exists but owned by someone else
    except OSError:
        return False


def acquire_lock():
    """Single-instance guard: only one listener may poll the bot."""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    old = 0
    if LOCK_FILE.exists():
        try:
            old = int(LOCK_FILE.read_text().strip())
        except Exception:
            old = 0
    if old and old != os.getpid() and _pid_alive(old):
        return False
    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    return True


def api(token, method, params=None, payload=None):
    url = f"{API}/bot{token}/{method}"
    if payload is None:
        resp = requests.get(url, params=params or {}, timeout=70)
    else:
        resp = requests.post(url, json=payload, timeout=70)
    data = resp.json()
    if not data.get("ok"):
        desc = data.get("description", str(data))
        raise RuntimeError(f"{method}: {desc}")
    return data["result"]


def load_snapshot():
    if not OUTPUT_FILE.exists():
        return None
    with OUTPUT_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def chunk(text):
    parts, cur = [], ""
    for line in text.splitlines():
        if cur and len(cur) + len(line) + 1 > MAX_LEN:
            parts.append(cur)
            cur = ""
        cur += line + "\n"
    if cur.strip():
        parts.append(cur)
    return parts


def reply(token, chat_id, text):
    for part in chunk(text):
        api(token, "sendMessage",
            payload={"chat_id": chat_id, "text": part[:MAX_LEN]})


def mini_digest(snapshot):
    if not snapshot:
        return ("No snapshot found on this device yet.\n"
                "Run `python main.py` first, then /today works.")
    s = snapshot.get("summary", {})
    date = str(snapshot.get("generated_at", ""))[:10]
    lines = [
        "🎯 Survey Hunter — live radar",
        f"{s.get('nigeria_open', 0)} open · {s.get('restricted', 0)} restricted · "
        f"{s.get('uncertain', 0)} uncertain · updated {date}",
        "",
        "⭐ picks (open to Nigeria today):",
    ]
    seen = {"survey": 0, "affiliate": 0, "freelance": 0}
    for p in snapshot.get("nigeria_open", []):
        v = p.get("vertical", "survey")
        if seen.get(v, 0) < 2:
            hook = (p.get("earn_model") or p.get("ref_program")
                    or p.get("min_payout", ""))
            lines.append(f"• {p['name']} — {str(hook)[:60]}")
            seen[v] += 1
    lines += ["", f"🔗 link-hub: {SITE_URL}", "Commands: /today · /links · /help"]
    return "\n".join(lines)


def respond(text, snapshot):
    t = text.strip().lower()
    if t.startswith(("/start", "/hi", "/hello", "hi", "hello")):
        return ("🎯 Survey Hunter is online!\n"
                "I re-check all platforms every morning.\n"
                "Try: /today or /links or /help.")
    if t.startswith("/today"):
        return mini_digest(snapshot)
    if t.startswith("/links"):
        return (f"🔗 Link hub (for your socials): {SITE_URL}\n"
                "🏠 Full radar: same site, index.html")
    if t.startswith("/help"):
        return ("Commands:\n"
                "/today — today's mini radar\n"
                "/links — your shareable URLs\n"
                "/help — this menu")
    return None  # ignore everything else quietly


def load_offset():
    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            return int(f.read().strip())
    except Exception:
        return None


def save_offset(value):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(str(value), encoding="utf-8")
    except Exception:
        pass


def handle_updates(token, allowed_chat, updates, snapshot):
    handled = 0
    for upd in updates:
        offset_now = upd["update_id"] + 1
        save_offset(offset_now)
        msg = upd.get("message") or upd.get("edited_message")
        if not msg:
            continue
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "")
        if chat_id != allowed_chat:
            continue  # only the owner's chat is ever answered
        answer = respond(text, snapshot)
        if answer:
            reply(token, chat_id, answer)
            print(f"   ↩ replied to {msg.get('text', '')[:30]!r}")
        handled += 1
    return handled


def _credentials():
    """Env vars first (PC/Termux), falling back to git-ignored local file."""
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if token and chat:
        return token, int(chat)
    cfg = ROOT / "config" / "telegram.json"
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            token = str(data.get("token", "")).strip()
            chat = str(data.get("chat_id", "")).strip()
            if token and chat:
                return token, int(chat)
        except Exception:
            pass
    return "", ""


def main():
    parser = argparse.ArgumentParser(description="Survey Hunter bot listener")
    parser.add_argument("--once", action="store_true",
                        help="drain pending messages then exit")
    args = parser.parse_args()

    token, chat_raw = _credentials()
    if not token or not chat_raw:
        print("!! No credentials: set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID "
              "or create config/telegram.json = {\"token\":..., \"chat_id\":...}")
        return

    if not acquire_lock():
        print("Another listener is already running - exiting quietly.")
        return

    allowed_chat = int(chat_raw)
    snapshot = load_snapshot()
    offset = load_offset()
    print(f"Listener ready (chat {allowed_chat}). Ctrl+C to stop.")

    if args.once:
        try:
            updates = api(token, "getUpdates",
                          params={"timeout": 1,
                                  **({"offset": offset} if offset else {})})
        except Exception as exc:
            print(f"getUpdates failed: {exc}")
            return
        if updates:
            n = handle_updates(token, allowed_chat, updates, snapshot)
            print(f"Processed {n} message group(s); exiting (--once).")
        else:
            print("No pending messages.")
        return

    backoff = 5
    while True:
        try:
            params = {"timeout": 50, "allowed_updates": ["message"]}
            if offset:
                params["offset"] = offset
            updates = api(token, "getUpdates", params=params)
            backoff = 5
            if updates:
                handle_updates(token, allowed_chat, updates, snapshot)
                offset = load_offset()
        except KeyboardInterrupt:
            print("Listener stopped.")
            return
        except Exception as exc:
            print(f"Listener retry in {backoff}s — {type(exc).__name__}: {exc}")
            time.sleep(backoff)
            backoff = min(backoff * 2, 120)


if __name__ == "__main__":
    main()
