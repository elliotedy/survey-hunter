# 🎯 Survey Hunter 🇳🇬

A daily survey-opportunity tracker built for Nigerians.

Every day it checks a curated list of paid survey platforms and sorts them
into **two clear buckets**:

- 🟢 **Open to Nigeria** — platform accepts Nigerian signups
- 🔴 **Restricted** — Nigeria is NOT accepted (skip, don't waste time)
- ❔ **Uncertain** — needs manual confirmation (listed too, with a link)

Results are published as:

1. a **free website** (GitHub Pages) with daily auto-updates, and
2. a **Telegram digest** sent to you every morning.

Everything also runs on your **phone in Termux** — no laptop needed.

---

## How it works

```
data/sources.json      ← your editable list of survey platforms
        │
        ▼
python main.py         ← checks each site live (geo-block phrases, HTTP,
        │                "nigeria" mentions), then classifies & writes
        ▼
data/surveys.json      ← the daily snapshot (site + Telegram read this)
        │
        ├──► GitHub Pages website (auto-deployed, free)
        └──► GitHub Actions → Telegram digest (6:30 AM WAT daily)
```

**Important honesty note:** the live check is a lightweight HTTP heuristic,
not a real signup test. It detects geo-block status codes (403/451),
"not available in your country/region" wording, and whether the page
mentions Nigeria. Survey companies also change rules frequently — so
always confirm at signup. If a site moves between buckets, keep or update
the `curated_open` flag in `data/sources.json`.

---

## 1) Push this project to your GitHub

```bash
cd "<this folder>"

# 1. create an EMPTY repository at https://github.com/new (name: survey-hunter)
# 2. then run:
git remote add origin https://github.com/<YOUR-USERNAME>/survey-hunter.git
git push -u origin main
```

(If you have the GitHub Desktop app, that's even easier: File → Add local
repository → Publish.)

## 2) Turn on the free website (GitHub Pages)

1. On your repo page: **Settings → Pages**
2. Under *Build and deployment*, set **Source = Deploy from a branch**
3. Choose **main / (root)** → Save
4. In 1–2 minutes your site is live at:
   `https://<YOUR-USERNAME>.github.io/survey-hunter/`

The daily workflow updates `data/surveys.json` automatically, so the site
stays fresh forever, for free.

## 3) Daily Telegram digest

**Create the bot (2 minutes):**

1. In Telegram, search **@BotFather** → send `/newbot` → follow the prompts
2. Copy the bot token it gives you (looks like `123456:ABC-DEF...`)
3. Search **@userinfobot** → send any message → it replies with your **chat ID**
   (or open `https://api.telegram.org/bot<TOKEN>/getUpdates` after messaging
   your new bot and read `"chat":{"id": … }`)

**Add the secrets to GitHub:**

`Settings → Secrets and variables → Actions → New repository secret`

- Name: `TELEGRAM_BOT_TOKEN` → value: the bot token
- Name: `TELEGRAM_CHAT_ID` → value: your chat ID

Done — every morning at **6:30 AM Nigeria time** you'll get the digest.
If the secrets are missing the workflow still updates the site silently.

## 4) Run it on your phone (Termux)

Install [Termux](https://f-droid.org/en/packages/com.termux/) (use the F-Droid
build), then:

```bash
pkg update && pkg install python git -y
git clone https://github.com/<YOUR-USERNAME>/survey-hunter.git
cd survey-hunter
pip install requests

python main.py                        # today's check + rebuild data
python main.py --skip-check           # offline mode (no internet / quick view)
python main.py --send-telegram        # push the digest to your Telegram
python -m http.server 8080            # view the website on your phone:
                                      # open http://localhost:8080 in the browser
```

**Daily auto-run on the phone:** install the app
[Termux:Job Scheduler](https://f-droid.org/en/packages/com.termux.jobcheduler/)
or use `termux-job-scheduler`/`cronie` from `pkg`, and schedule:

```bash
python ~/survey-hunter/main.py --send-telegram
```

## Run it on your Windows PC

Same commands as Termux — Python 3 is already installed on the PC:

```powershell
cd "C:\users\<you>\...\survey hunter"
python main.py                  # daily check + rebuild data
python main.py --send-telegram  # also push the Telegram digest
python -m http.server 8000      # then open http://localhost:8000
```

Or just double-click, no typing:

- **`run-today.bat`** → today's full check of all platforms
  (extra: right-drag a shortcut to your desktop)
- **`open-site.bat`** → opens the website locally in your browser

**Telegram on the PC** (one-time, then `python main.py --send-telegram` works everywhere):

```powershell
setx TELEGRAM_BOT_TOKEN "123456:ABC-DEF..."
setx TELEGRAM_CHAT_ID "0123456789"
```

**Daily automation on the PC:** Start menu → search **Task Scheduler**
→ *Create Basic Task* → name it → **Daily 06:30** → *Start a program* →
browse to `run-today.bat` → add the argument `--auto` → Finish.

## 5) Customising the platform list

Edit `data/sources.json`:

- `curated_open: true` → trusted as Nigeria-friendly (bucket 🟢)
- `curated_open: false` → known to restrict Nigeria (bucket 🔴)
- `curated_open: null` → unknown (bucket ❔) — the daily checker helps you verify

Add new platforms freely — the site and Telegram digest use whatever is
in the file. The daily check downgrade rule: a 🟢 platform whose page today
shows geo-block language is demoted to ❔ until someone confirms.

---

## Project layout

```
index.html            website (single page, mobile-first)
assets/               site styles + logic (vanilla, no build tools)
data/sources.json     editable platform registry  ← EDIT ME
data/surveys.json     daily generated snapshot
scraper/              python package (checker, classifier, telegram)
main.py               CLI entry point
.github/workflows/    daily GitHub Actions job (cron + commit + telegram)
```

## Roadmap ideas

- Scrape actual per-day survey inventory for platforms that expose it
- Push alerts when a new platform opens to Nigeria
- SQLite history to track which platforms trend up/down

## License

Use it, remix it, resell the insight — good luck with the new venture! 🚀
