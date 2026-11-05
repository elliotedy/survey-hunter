"""Daily live check of every survey platform page.

The checks are lightweight HTTP heuristics, not a full browser test:
they look for geo-block status codes and for "not available in your
country/region" style sentences. Results feed the classifier in store.py.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9,en-GB;q=0.8",
}

# Phrases that mean the site is telling visitors "you cannot join here".
NEGATIVE_PATTERNS = [
    "not available in your country",
    "not available in your region",
    "not supported in your country",
    "not supported in your region",
    "unavailable in your country",
    "unavailable in your region",
    "country is not supported",
    "not accepting members from",
    "service is not available in your",
]

# HTTP status codes commonly returned for geo/legally blocked pages.
GEO_BLOCK_STATUS = {403, 410, 451}


def check_url(url, timeout=25):
    """Fetch a platform URL.

    Returns: (status, block_signal, nigeria_mentioned, detail)
        status            - "ok" | "error"
        block_signal      - True if the page suggests the visitor is blocked
        nigeria_mentioned - True if the page body mentions "nigeria"
        detail            - short human readable note
    """
    try:
        resp = requests.get(
            url, headers=HEADERS, timeout=timeout, allow_redirects=True
        )
    except requests.RequestException as exc:
        return "error", False, False, f"{type(exc).__name__}"

    if resp.status_code >= 400:
        if resp.status_code in GEO_BLOCK_STATUS:
            return "error", True, False, f"HTTP {resp.status_code} (possible geo-block)"
        return "error", False, False, f"HTTP {resp.status_code}"

    body = resp.text.lower()
    block_signal = any(pattern in body for pattern in NEGATIVE_PATTERNS)
    nigeria_mentioned = "nigeria" in body
    return "ok", block_signal, nigeria_mentioned, f"HTTP {resp.status_code}"


def run_checks(platforms, workers=8, timeout=25):
    """Check every platform concurrently; return updated dicts (same order)."""
    results = [None] * len(platforms)

    def apply(index, platform, outcome):
        status, block_signal, nigeria_mentioned, detail = outcome
        from datetime import datetime, timezone

        merged = dict(platform)
        merged.update(
            {
                "status": status,
                "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "block_signal": block_signal,
                "nigeria_mentioned": nigeria_mentioned,
                "check_detail": detail,
            }
        )
        results[index] = merged

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        future_map = {
            pool.submit(check_url, p["url"], timeout): i for i, p in enumerate(platforms)
        }
        for future in as_completed(future_map):
            index = future_map[future]
            try:
                outcome = future.result()
            except Exception as exc:  # defensive: never kill the whole run
                outcome = ("error", False, False, f"Unhandled: {type(exc).__name__}")
            apply(index, platforms[index], outcome)

    return results
