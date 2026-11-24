"""
fetch_traffic.py  -  London road traffic (congestion) from Transport for London (TfL).

Run from the project folder (the one that contains data/ and agents/):
    python data/fetch_traffic.py --poll      save TfL's road status for right now
    python data/fetch_traffic.py --daily     turn the saved history into one row per day

Why there are two steps:
  TfL only publishes the CURRENT status of each major road. There is no history to
  download (unlike London Air and Open-Meteo). So the history has to be built up by
  saving a snapshot every hour. The GitHub workflow .github/workflows/traffic.yml
  does this automatically. Traffic links can only be worked out once enough days
  have been saved (summarise.py needs 30 days before it reports any link).

What --poll does:
  1. Asks TfL for the status of its 24 main London road corridors (A406, A4, ...).
  2. Turns each status into a number (see SEVERITY below).
  3. Adds one row per corridor to data/traffic/traffic_status.csv
        polled_gmt, road_id, severity
     This file IS committed to git (data/processed/ is not), because it is the only
     copy of the history.

What --daily does:
  Writes data/processed/traffic_daily.csv, one row per day (GMT, like the other tables):
     date                     the day
     hours_covered            hours of that day with at least one snapshot
     traffic_mean_severity    average severity over all roads and snapshots (0 = no delays)
     traffic_delay_pct        % of road readings with any delay (severity 1 or more)
     traffic_rush_severity    same average, but only 07:00-10:00 and 16:00-19:00 London time
     traffic_peak_roads       most roads with a delay in any single snapshot
  A day only counts if it has at least MIN_HOURS hours covered (same 75% rule as
  summarise.py), so a day when the workflow failed is left out, not half-counted.

Important limits (also add these to data/limitations.md):
  - TfL gives a congestion STATUS per road, not a vehicle count. It is a rough
    measure: most hours are 0, so the signal sits in the bad hours.
  - It covers London's main TfL roads, not every street near a monitoring site.
  - The history starts on the day polling started.

Optional key: TfL works without a key for light use. If you get rate-limit errors,
register free at https://api-portal.tfl.gov.uk/ and put TFL_APP_KEY=... in your .env
file (and as a GitHub secret named TFL_APP_KEY for the workflow). Never commit it.
"""
import argparse
import datetime as dt
import os
from pathlib import Path

import pandas as pd
import requests

try:                                  # .env is optional; the workflow uses GitHub secrets
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ------------------------------------------------------------------ settings
TFL_ROADS_URL = "https://api.tfl.gov.uk/Road"       # <- UPDATE HERE if TfL moves the API
TFL_APP_KEY = os.environ.get("TFL_APP_KEY")         # <- OPTIONAL key, from .env

# TfL's statusSeverity text -> a number we can average. 0 = no delays, higher = worse.
SEVERITY = {"Good": 0, "Minor": 1, "Moderate": 2, "Serious": 3, "Severe": 4, "Closure": 5}

MIN_HOURS = 18                       # a day counts only with 18 of 24 hours covered
RUSH_HOURS = [7, 8, 9, 16, 17, 18]   # London local time (07:00-10:00 and 16:00-19:00)

ROOT = Path(__file__).parent
HISTORY = ROOT / "traffic" / "traffic_status.csv"   # committed to git
PROCESSED = ROOT / "processed"


# ------------------------------------------------------------------ poll
def poll():
    """Save one snapshot of every TfL road corridor's status."""
    params = {"app_key": TFL_APP_KEY} if TFL_APP_KEY else None
    try:
        r = requests.get(TFL_ROADS_URL, params=params, timeout=60)
        r.raise_for_status()
        roads = r.json()
    except Exception as e:
        raise SystemExit(f"TfL download failed: {e}")   # non-zero exit -> workflow shows red

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")   # GMT
    rows, unknown = [], set()
    for road in roads:
        sev = SEVERITY.get(road.get("statusSeverity"))
        if sev is None:
            unknown.add(str(road.get("statusSeverity")))
            continue
        rows.append((now, road["id"], sev))
    if unknown:
        print(f"Warning: unknown TfL status {sorted(unknown)}. Add it to SEVERITY in this file.")
    if not rows:
        raise SystemExit("TfL returned no usable roads. Nothing saved.")

    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    new = pd.DataFrame(rows, columns=["polled_gmt", "road_id", "severity"])
    new.to_csv(HISTORY, mode="a", header=not HISTORY.exists(), index=False)
    delayed = int((new.severity > 0).sum())
    print(f"{now} GMT: saved {len(new)} roads, {delayed} with delays "
          f"(mean severity {new.severity.mean():.2f})")


# ------------------------------------------------------------------ daily
def daily():
    """Turn the saved snapshots into one row per day."""
    if not HISTORY.exists():
        raise SystemExit("No traffic history yet. Run  python data/fetch_traffic.py --poll  first.")
    t = pd.read_csv(HISTORY, parse_dates=["polled_gmt"])
    t = t.drop_duplicates(["polled_gmt", "road_id"])
    t["date"] = t.polled_gmt.dt.date
    t["hour_gmt"] = t.polled_gmt.dt.floor("h")
    london_hour = (t.polled_gmt.dt.tz_localize("UTC").dt.tz_convert("Europe/London").dt.hour)
    t["is_rush"] = london_hour.isin(RUSH_HOURS)

    out = []
    for date, g in t.groupby("date"):
        hours = g.hour_gmt.nunique()
        if hours < MIN_HOURS:
            continue
        per_snapshot = g.groupby("polled_gmt").severity.apply(lambda s: int((s > 0).sum()))
        rush = g[g.is_rush]
        out.append({
            "date": date,
            "hours_covered": hours,
            "traffic_mean_severity": round(g.severity.mean(), 3),
            "traffic_delay_pct": round(100 * (g.severity > 0).mean(), 1),
            "traffic_rush_severity": round(rush.severity.mean(), 3) if len(rush) else None,
            "traffic_peak_roads": int(per_snapshot.max()),
        })

    PROCESSED.mkdir(parents=True, exist_ok=True)
    cols = ["date", "hours_covered", "traffic_mean_severity", "traffic_delay_pct",
            "traffic_rush_severity", "traffic_peak_roads"]
    daily_df = pd.DataFrame(out, columns=cols)
    daily_df.to_csv(PROCESSED / "traffic_daily.csv", index=False)

    first = t.date.min()
    print(f"History starts {first}; {t.date.nunique()} days saved, "
          f"{len(daily_df)} days complete enough to use (need {MIN_HOURS}+ hours).")
    print("Saved: data/processed/traffic_daily.csv")


# ------------------------------------------------------------------ main
def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--poll", action="store_true", help="save TfL's road status for right now")
    mode.add_argument("--daily", action="store_true", help="build data/processed/traffic_daily.csv")
    args = parser.parse_args()
    poll() if args.poll else daily()


if __name__ == "__main__":
    main()
