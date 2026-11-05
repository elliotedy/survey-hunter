#!/usr/bin/env python3
"""Signup fast-fill assistant — LEGIT single-account signups only.

What it does:
  * loads YOUR real identity ONCE from config/profile.json (never synced)
  * opens the platform's signup page in your browser (your ref link if set)
  * copies your details to the clipboard field-by-field so each signup
    takes seconds instead of minutes

What it will NOT do:
  * create accounts automatically, or manage accounts that are not yours.
    Platforms allow ONE account per person; automation there gets
    people banned and payouts forfeited. Fill things yourself, honestly.
"""
import argparse
import getpass
import json
import sys
import webbrowser
from pathlib import Path

from scraper.clipboard import backend_name, copy_text
from scraper.registry import ROOT, load_sources

PROFILE_FILE = ROOT / "config" / "profile.json"

FIELDS = [
    ("full_name", "Full name"),
    ("email", "Email address"),
    ("phone", "Phone (+234...)"),
    ("username", "Username (optional)"),
    ("city", "City (optional)"),
    ("dob", "Date of birth (optional)"),
    ("password", "Password"),
]

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def load_profile():
    if not PROFILE_FILE.exists():
        print("No profile yet. Run:  python signup-helper.py --setup")
        return None
    with PROFILE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def cmd_setup():
    if PROFILE_FILE.exists():
        print(f"Profile already exists at {PROFILE_FILE}")
        if input("Overwrite and re-enter details? [y/N] ").strip().lower() != "y":
            return
    data = {"_note": "PERSONAL - gitignored. One honest account per human."}
    print(f"\n== Your real details (stored only on this device) ==")
    for key, label in FIELDS:
        if key == "password":
            value = getpass.getpass(f"  {label}: ")
        else:
            value = input(f"  {label}: ").strip()
        if value:
            data[key] = value
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with PROFILE_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"\nSaved -> {PROFILE_FILE}")
    print("Keep it safe: this folder is 'config/' and already git-ignored.")


def cmd_list(*_, **__):
    from scraper.store import categorize

    platforms = [p for p in load_sources() if categorize(p) != "restricted"]
    print(f"\nViable signup targets ({len(platforms)} tracked "
          f"— restricted sites excluded):\n")
    for p in sorted(platforms,
                    key=lambda x: (x.get("curated_open") is not True,
                                   x.get("name", "").lower())):
        flag = "💸ref" if p.get("your_ref_url") else "    "
        tag = "🟢" if p.get("curated_open") is True else "❔"
        print(f"  {tag} {flag}  {p['name'][:26]:26s} {p['url']}")


def _pick(platforms, needle):
    n = needle.lower() if needle else ""
    for p in platforms:
        if n in (p.get("id", ""), p.get("name", "").lower()):
            return p
    if needle:
        matches = [p for p in platforms if n in p.get("name", "").lower()]
        if len(matches) == 1:
            return matches[0]
    return None


def cmd_fill(profile, name=None):
    from scraper.store import categorize

    platforms = [p for p in load_sources() if categorize(p) != "restricted"]
    p = _pick(platforms, name)
    if p is None:
        print("Not found. Try:  python signup-helper.py --list")
        return 1

    target = p.get("your_ref_url") or p["url"]
    print(f"\nOpening: {p.get('name')} — {target}")
    webbrowser.open(target)

    print(f"Clipboard backend: {backend_name()}\n")
    for key, label in FIELDS:
        value = (profile or {}).get(key)
        if not value:
            continue
        backend = copy_text(value)
        shown = "•" * len(value) if key == "password" else value
        if backend is None:
            print(f"  {label}: could not access clipboard — copy manually: {shown}")
        else:
            print(f"  {label} COPIED: {shown}  (paste with Ctrl+V / long-press)")
        nxt = input("      [Enter] next field / s=skip rest / q=quit ... ").strip().lower()
        if nxt == "s":
            break
        if nxt == "q":
            return 0
    print("\nFinish the form yourself — CAPTCHA + email verification keep the"
          " account safe and payout-eligible. One honest account per human.")
    return 0


def cmd_copy(profile, key):
    if key not in dict(FIELDS):
        print(f"Unknown field '{key}'. Options: {[k for k, _ in FIELDS]}")
        return 1
    value = (profile or {}).get(key)
    if not value:
        print(f"No '{key}' in {PROFILE_FILE.name} — run --setup")
        return 1
    shown = "•" * len(value) if key == "password" else value
    backend = copy_text(value)
    if backend:
        print(f"{key} COPIED ({backend}): {shown}")
    else:
        print(f"No clipboard found — copy manually: {shown}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Survey Hunter signup helper")
    parser.add_argument("--setup", action="store_true",
                        help="create/replace your personal profile.json")
    parser.add_argument("--list", action="store_true",
                        help="list viable signup targets")
    parser.add_argument("--fill", nargs="?", const="", metavar="NAME",
                        help="open a site's signup + walk your fields through the clipboard")
    parser.add_argument("--copy", metavar="FIELD",
                        help="copy one profile field (e.g. email)")
    args = parser.parse_args()

    if args.setup:
        cmd_setup()
        return
    if args.list:
        cmd_list()
        return

    profile = load_profile()
    if profile is None:
        return

    if args.copy:
        sys.exit(cmd_copy(profile, args.copy.strip().lower()))

    if args.fill is not None:
        sys.exit(cmd_fill(profile, args.fill))

    parser.print_help()


if __name__ == "__main__":
    main()
