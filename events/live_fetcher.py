"""
live_fetcher.py
---------------
Fetches macroeconomic events from free public APIs and caches them
so the calendar stays up-to-date automatically.

Sources:
  FOMC  — FRED series DFEDTARU (upper target rate) via api.stlouisfed.org
  CPI   — FRED series CPIAUCSL (all-items CPI) via api.stlouisfed.org
  RBI   — FRED series INDIRLTLT01STM (India long rate) as proxy trigger;
           confirmed decisions kept in a lightweight supplement list.
  Geo   — Static baseline (no reliable free live feed); maintained manually.

FRED public API requires no key for < 120 req/day.
Cache TTL: 6 hours (written to events/_cache.json next to this file).
"""

import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)

CACHE_FILE = Path(__file__).parent / "_cache.json"
CACHE_TTL  = 6 * 3600  # seconds

FRED_BASE  = "https://api.stlouisfed.org/fred/series/observations"
FRED_PARAMS = {
    "file_type": "json",
    "observation_start": "2020-01-01",
}

# ── Geopolitical events (static — updated manually on major shocks) ──────────
GEO_EVENTS = [
    {"date": "2020-02-24", "name": "COVID-19 market panic begins",              "category": "Geopolitical"},
    {"date": "2020-03-11", "name": "WHO declares COVID-19 pandemic",             "category": "Geopolitical"},
    {"date": "2022-02-24", "name": "Russia invades Ukraine",                     "category": "Geopolitical"},
    {"date": "2023-03-10", "name": "Silicon Valley Bank collapse",               "category": "Geopolitical"},
    {"date": "2023-10-07", "name": "Hamas attack on Israel",                     "category": "Geopolitical"},
    {"date": "2024-08-05", "name": "Global market crash — Yen carry unwind",    "category": "Geopolitical"},
    {"date": "2025-01-20", "name": "Trump inauguration — tariff fears",          "category": "Geopolitical"},
    {"date": "2025-04-02", "name": "Trump Liberation Day — sweeping global tariffs", "category": "Geopolitical"},
    {"date": "2025-04-09", "name": "S&P 500 +9.5% — 90-day tariff pause",       "category": "Geopolitical"},
    {"date": "2025-05-12", "name": "US-China 90-day tariff truce",              "category": "Geopolitical"},
    {"date": "2025-06-13", "name": "Israel strikes Iran nuclear sites — oil surges 20%", "category": "Geopolitical"},
    {"date": "2025-06-22", "name": "US joins Israel strikes on Iran",            "category": "Geopolitical"},
]

# ── RBI supplement (FRED has no clean RBI decision series) ───────────────────
RBI_EVENTS = [
    {"date": "2020-03-27", "name": "RBI Emergency Cut -75bps",                  "category": "RBI"},
    {"date": "2022-05-04", "name": "RBI Off-cycle Hike +40bps",                 "category": "RBI"},
    {"date": "2022-06-08", "name": "RBI Hike +50bps",                           "category": "RBI"},
    {"date": "2023-04-06", "name": "RBI Hold at 6.50%",                         "category": "RBI"},
    {"date": "2024-04-05", "name": "RBI Hold — stance changed to neutral",      "category": "RBI"},
    {"date": "2024-10-09", "name": "RBI Hold at 6.50%",                         "category": "RBI"},
    {"date": "2025-02-07", "name": "RBI Cut -25bps to 6.25%",                   "category": "RBI"},
    {"date": "2025-04-09", "name": "RBI Cut -25bps to 6.00%",                   "category": "RBI"},
    {"date": "2025-06-06", "name": "RBI Cut -50bps to 5.50% — aggressive easing", "category": "RBI"},
    {"date": "2025-08-06", "name": "RBI Hold at 5.50% — assessing tariff impact", "category": "RBI"},
    {"date": "2025-10-08", "name": "RBI Hold at 5.50%",                         "category": "RBI"},
    {"date": "2025-12-05", "name": "RBI Cut -25bps to 5.25% — growth support", "category": "RBI"},
]


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text())
            if time.time() - data.get("ts", 0) < CACHE_TTL:
                return data
        except Exception:
            pass
    return {}


def _save_cache(data: dict):
    try:
        data["ts"] = time.time()
        CACHE_FILE.write_text(json.dumps(data, default=str))
    except Exception as e:
        logger.warning(f"Cache write failed: {e}")


def _fred_fetch(series_id: str) -> list[dict]:
    """Return list of {date, value} from FRED."""
    try:
        params = {**FRED_PARAMS, "series_id": series_id}
        r = httpx.get(FRED_BASE, params=params, timeout=10)
        r.raise_for_status()
        obs = r.json().get("observations", [])
        return [
            {"date": o["date"], "value": o["value"]}
            for o in obs
            if o["value"] not in (".", "")
        ]
    except Exception as e:
        logger.warning(f"FRED fetch failed for {series_id}: {e}")
        return []


def _build_fomc_events(obs: list[dict]) -> list[dict]:
    """
    DFEDTARU = upper bound of Fed funds target rate (daily).
    We detect days where the rate changes vs the previous observation.
    """
    events = []
    prev_val = None
    prev_date = None

    for o in obs:
        val = float(o["value"])
        date = o["date"]

        if prev_val is not None and val != prev_val:
            diff_bps = round((val - prev_val) * 100)
            sign = "+" if diff_bps > 0 else ""

            if diff_bps > 0:
                action = f"Fed Hike {sign}{diff_bps}bps → {val:.2f}%"
            elif diff_bps < 0:
                action = f"Fed Cut {diff_bps}bps → {val:.2f}%"
            else:
                action = f"Fed Hold at {val:.2f}%"

            # Only emit on the actual decision date (rate first changes)
            events.append({"date": date, "name": action, "category": "FOMC"})

        elif prev_val is not None and val == prev_val:
            # Detect holds: FOMC meets 8x/year. We flag months where rate
            # is unchanged but a meeting likely occurred (months with no change).
            # We skip this for brevity — holds appear from the static list.
            pass

        prev_val = val
        prev_date = date

    # Deduplicate same-date entries (FRED sometimes has duplicate obs)
    seen = set()
    deduped = []
    for e in events:
        if e["date"] not in seen:
            seen.add(e["date"])
            deduped.append(e)

    return deduped


def _build_cpi_events(obs: list[dict]) -> list[dict]:
    """
    CPIAUCSL is monthly index level. Compute YoY % change and flag
    significant releases (every month — that's what traders watch).
    """
    events = []
    # Build date → value lookup
    by_date = {o["date"]: float(o["value"]) for o in obs}
    dates = sorted(by_date.keys())

    for date in dates:
        dt = datetime.strptime(date, "%Y-%m-%d")
        # Find value ~12 months ago
        prev_dt = dt.replace(year=dt.year - 1)
        prev_str = prev_dt.strftime("%Y-%m-%d")

        # FRED uses first-of-month dates; allow ±5 day window
        prev_val = None
        for delta in range(-5, 6):
            candidate = (prev_dt + timedelta(days=delta)).strftime("%Y-%m-%d")
            if candidate in by_date:
                prev_val = by_date[candidate]
                break

        if prev_val and prev_val > 0:
            yoy = (by_date[date] / prev_val - 1) * 100
            label = f"CPI +{yoy:.1f}% YoY"

            # Add qualitative note for historically notable readings
            if yoy >= 8.0:
                label += " — multi-decade high"
            elif yoy >= 6.0:
                label += " — elevated"
            elif yoy <= 2.1:
                label += " — near Fed target"

            events.append({"date": date, "name": label, "category": "CPI"})

    return events


# ── Known FOMC hold dates to supplement FRED rate-change detection ───────────
# FRED only shows rate *changes*. Holds are invisible in DFEDTARU.
# We keep a rolling list of confirmed hold dates here.
FOMC_HOLDS = [
    {"date": "2023-09-20", "name": "Fed Hold at 5.25–5.50%",       "category": "FOMC"},
    {"date": "2023-11-01", "name": "Fed Hold at 5.25–5.50%",       "category": "FOMC"},
    {"date": "2023-12-13", "name": "Fed Hold at 5.25–5.50%",       "category": "FOMC"},
    {"date": "2024-01-31", "name": "Fed Hold at 5.25–5.50%",       "category": "FOMC"},
    {"date": "2024-03-20", "name": "Fed Hold at 5.25–5.50%",       "category": "FOMC"},
    {"date": "2024-05-01", "name": "Fed Hold at 5.25–5.50%",       "category": "FOMC"},
    {"date": "2024-06-12", "name": "Fed Hold at 5.25–5.50%",       "category": "FOMC"},
    {"date": "2024-07-31", "name": "Fed Hold at 5.25–5.50%",       "category": "FOMC"},
    {"date": "2025-01-29", "name": "Fed Hold — cautious on inflation", "category": "FOMC"},
    {"date": "2025-03-19", "name": "Fed Hold at 4.25–4.50% — tariff uncertainty", "category": "FOMC"},
    {"date": "2025-05-07", "name": "Fed Hold at 4.25–4.50% — stagflation fears", "category": "FOMC"},
    {"date": "2025-06-18", "name": "Fed Hold at 4.25–4.50% — data dependent",    "category": "FOMC"},
    {"date": "2025-07-30", "name": "Fed Hold at 4.25–4.50%",       "category": "FOMC"},
    {"date": "2025-10-29", "name": "Fed Hold at 4.00–4.25%",       "category": "FOMC"},
    {"date": "2026-01-28", "name": "Fed Hold at 3.50–3.75%",       "category": "FOMC"},
    {"date": "2026-03-18", "name": "Fed Hold at 3.50–3.75%",       "category": "FOMC"},
]


def fetch_live_events() -> list[dict]:
    """
    Returns merged, date-sorted list of all macro events.
    Uses cache; refreshes from FRED if stale.
    """
    cache = _load_cache()
    if cache.get("events"):
        logger.info("Returning cached macro events")
        return cache["events"]

    logger.info("Cache miss — fetching live macro events from FRED")

    # ── FOMC: rate changes from FRED ─────────────────────────────────────────
    fomc_obs = _fred_fetch("DFEDTARU")
    fomc_changes = _build_fomc_events(fomc_obs)

    # Merge changes + holds, deduplicate by date (changes win over holds)
    fomc_dates = {e["date"] for e in fomc_changes}
    fomc_holds_filtered = [e for e in FOMC_HOLDS if e["date"] not in fomc_dates]
    fomc_all = fomc_changes + fomc_holds_filtered

    # ── CPI: monthly YoY from FRED ───────────────────────────────────────────
    cpi_obs = _fred_fetch("CPIAUCSL")
    cpi_events = _build_cpi_events(cpi_obs)

    # Only keep CPI events that are notably above or below 2.5% or historically high
    # (keeps chart uncluttered — show every reading since 2021 inflation started)
    cpi_filtered = [
        e for e in cpi_events
        if datetime.strptime(e["date"], "%Y-%m-%d") >= datetime(2021, 1, 1)
    ]

    # ── Merge all sources ────────────────────────────────────────────────────
    all_events = fomc_all + cpi_filtered + RBI_EVENTS + GEO_EVENTS

    # Sort by date, remove exact duplicates
    seen = set()
    deduped = []
    for e in sorted(all_events, key=lambda x: x["date"]):
        key = (e["date"], e["category"])
        if key not in seen:
            seen.add(key)
            deduped.append(e)

    _save_cache({"events": deduped})
    logger.info(f"Fetched {len(deduped)} live macro events")
    return deduped


def get_events(category: str = None) -> list[dict]:
    """Drop-in replacement for calendar.get_events()."""
    events = fetch_live_events()
    if category:
        return [e for e in events if e["category"] == category]
    return events


def invalidate_cache():
    """Force a refresh on next call."""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
