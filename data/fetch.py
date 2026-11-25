"""
fetch.py  -  London air quality, weather, boundary layer height and road traffic,
             matched hour by hour.

Run from the project folder (the one that contains data/ and agents/):
    python data/fetch.py              download last 365 days, write all tables   <- daily run
    python data/fetch.py --days 30    a shorter test
    python data/fetch.py --poll       save ONE traffic snapshot now (run by traffic.yml: every 30 min in rush hours)

summarise.py runs the first form by itself (python data/summarise.py --fetch).
.github/workflows/traffic.yml runs the --poll form every 30 minutes in the morning and evening
rush hours and about every 3 hours the rest of the day.

DATA SOURCES (nothing needs a key unless you hit TfL rate limits)
  1. London Air (LAQN), King's College London / Imperial ERG   - MEASURED, hourly
       https://api.erg.ic.ac.uk/AirQuality/Data/SiteSpecies/...
       NO2, PM2.5, PM10, O3 at a fixed panel of 8 sites (see PANEL). Recent values are provisional.
  2. Open-Meteo Historical Weather API (ERA5 based)            - MODELLED, hourly
       https://archive-api.open-meteo.com/v1/archive
       wind speed and direction, rain, temperature, humidity, pressure, cloud cover and
       boundary layer height for central London. Runs a few days behind real time.
  3. Open-Meteo Forecast API (last 14 days)                    - MODELLED, hourly
       https://api.open-meteo.com/v1/forecast
       Fills the most recent days when the archive has not caught up.
  4. TfL Unified API, road corridor status                     - REPORTED, snapshot per hour
       https://api.tfl.gov.uk/Road
       Delay status of 24 main London roads. TfL keeps NO history, so we save a snapshot
       on a schedule ourselves (data/traffic/traffic_status.csv): every 30 min in rush
       hours, about every 3 hours otherwise. History starts on the day polling started,
       and only the polled hours have a traffic value.
  (The official daily air quality index, DAQI, is fetched by summarise.py, not here.)

TIME: every table is on one clock, GMT, one row per hour, so "Tuesday 08:00" in air quality,
weather, boundary layer and traffic is the same row. Traffic snapshots are placed in the hour
they were taken (a 07:10 and a 07:40 snapshot both go in the 07:00 row and are averaged). Only
the 12 polled hours a day have a traffic value; the other hours stay blank, never filled in
or guessed.

WRITES (data/processed/, not committed)
    air_hourly.csv       site_code, site_type, pollutant, time_gmt, value_ugm3   (as before)
    weather_hourly.csv   time_gmt + one column per weather variable            (as before)
    traffic_daily.csv    one row per day with enough snapshots
    hourly_merged.csv    ONE ROW PER HOUR with everything side by side          <- new
    fetch_report.txt     coverage and sources  <- paste this into the chat
Writes data/traffic/traffic_status.csv (committed) when run with --poll.
"""
import argparse
import datetime as dt
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

try:                                  # .env is optional; GitHub uses secrets instead
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ------------------------------------------------------------------ settings
# Site panel chosen from a 365-day coverage check (20 Nov 2026):
# every pair below had a value in at least 80% of hours.
PANEL = {
    # site: (type, pollutants)
    "HP1": ("background", ["NO2", "PM25", "PM10", "O3"]),  # Lewisham - Honor Oak Park
    "KC1": ("background", ["NO2", "O3"]),                  # Kensington and Chelsea - North Ken
    "TH6": ("background", ["NO2", "O3"]),                  # Tower Hamlets - Millwall Park
    "CW3": ("background", ["PM25", "PM10"]),               # Tower Hamlets - Jubilee Park
    "MY1": ("roadside", ["NO2"]),                          # Westminster - Marylebone Road
    "BT4": ("roadside", ["NO2", "PM25", "PM10"]),          # Brent - Ikea
    "CE2": ("roadside", ["NO2", "PM25", "PM10"]),          # Waterloo Place
    "TH4": ("roadside", ["NO2"]),                          # Tower Hamlets - Blackwall
}
POLLUTANT_NAMES = {"NO2": "NO2", "PM25": "PM2.5", "PM10": "PM10", "O3": "O3"}

LAT, LON = 51.5074, -0.1278          # central London
# boundary_layer_height = how deep the layer of air is that pollution mixes into (metres)
WEATHER_VARS = [
    "temperature_2m", "relative_humidity_2m", "precipitation",
    "wind_speed_10m", "wind_direction_10m", "surface_pressure",
    "boundary_layer_height", "cloud_cover",
]

LAQN = "https://api.erg.ic.ac.uk/AirQuality"                  # <- UPDATE HERE if the source moves
OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_RECENT = "https://api.open-meteo.com/v1/forecast"
TFL_ROADS_URL = "https://api.tfl.gov.uk/Road"
TFL_APP_KEY = os.environ.get("TFL_APP_KEY")                   # OPTIONAL, from .env / GitHub secret

# TfL's statusSeverity text -> a number we can average. 0 = no delays, higher = worse.
SEVERITY = {"Good": 0, "Minor": 1, "Moderate": 2, "Serious": 3, "Severe": 4, "Closure": 5}
# GMT hours in which traffic.yml takes snapshots. KEEP IN STEP with the cron lines there.
#   rush windows 06-09 and 15-18 GMT: every 30 min (covers London rush hour in winter AND summer)
#   all other times: 01, 04, 12, 22 GMT (every ~3 hours)
POLL_HOURS_UTC = [1, 4, 6, 7, 8, 9, 12, 15, 16, 17, 18, 22]
EXPECTED_SNAPSHOT_HOURS = len(POLL_HOURS_UTC)                         # 12 polled hours a day
MIN_SNAPSHOT_HOURS = max(1, round(0.75 * EXPECTED_SNAPSHOT_HOURS))   # 75% rule: 9 of 12
RUSH_HOURS = [7, 8, 9, 16, 17, 18]   # London local time (07:00-10:00 and 16:00-19:00)

ROOT = Path(__file__).parent
RAW = ROOT / "raw"
PROCESSED = ROOT / "processed"
HISTORY = ROOT / "traffic" / "traffic_status.csv"             # committed to git


# ------------------------------------------------------------------ helpers
def as_list(x):
    """London Air returns a dict instead of a list when there is only one item."""
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def get_json(url, params=None, tries=3):
    for attempt in range(1, tries + 1):
        try:
            r = requests.get(url, params=params, timeout=120)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"   attempt {attempt} failed: {e}")
            time.sleep(3 * attempt)
    return None


def month_starts(start, end):
    """First day of every month that overlaps [start, end)."""
    m = start.replace(day=1)
    while m < end:
        yield m
        m = (m.replace(day=28) + dt.timedelta(days=4)).replace(day=1)


def utc_today():
    """Today's date on the GMT clock (so the cut-off is the same on any computer)."""
    return dt.datetime.now(dt.timezone.utc).date()


# ------------------------------------------------------------------ air
def fetch_month(site, species, month, today):
    """Download one site-pollutant-month, using the cache when possible."""
    next_month = (month.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    path = RAW / "laqn" / f"{site}_{species}_{month:%Y-%m}.json"
    finished = next_month <= today - dt.timedelta(days=3)  # old enough to be final
    if path.exists() and finished:
        return json.loads(path.read_text(encoding="utf-8"))
    url = (f"{LAQN}/Data/SiteSpecies/SiteCode={site}/SpeciesCode={species}"
           f"/StartDate={month}/EndDate={min(next_month, today)}/Json")  # EndDate is exclusive
    data = get_json(url)
    if data is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
    return data


def fetch_air(start, today):
    jobs = [(site, sp, m) for site, (_, sps) in PANEL.items()
            for sp in sps for m in month_starts(start, today)]
    print(f"1/3  London Air: {len(jobs)} site-pollutant-months to check ...")

    def run(job):
        site, sp, m = job
        return job, fetch_month(site, sp, m, today)

    rows, failed = [], []
    with ThreadPoolExecutor(max_workers=3) as pool:   # 3 at a time: polite to the free API
        for n, ((site, sp, m), data) in enumerate(pool.map(run, jobs), 1):
            if data is None:
                failed.append(f"{site} {sp} {m:%Y-%m}")
                continue
            for rec in as_list(data.get("RawAQData", {}).get("Data")):
                rows.append((site, PANEL[site][0], POLLUTANT_NAMES[sp],
                             rec["@MeasurementDateGMT"], rec.get("@Value")))
            if n % 25 == 0:
                print(f"     {n}/{len(jobs)} done")

    air = pd.DataFrame(rows, columns=["site_code", "site_type", "pollutant", "time_gmt", "value_ugm3"])
    air["time_gmt"] = pd.to_datetime(air["time_gmt"])
    air["value_ugm3"] = pd.to_numeric(air["value_ugm3"], errors="coerce")  # "" -> missing
    air = air[(air.time_gmt >= pd.Timestamp(start)) & (air.time_gmt < pd.Timestamp(today))]
    air = air.drop_duplicates(["site_code", "pollutant", "time_gmt"]).sort_values(
        ["pollutant", "site_code", "time_gmt"])
    return air, failed


# ------------------------------------------------------------------ weather + boundary layer
def fetch_weather(start, today):
    """Hourly wind, rain, temperature, pressure ... AND boundary layer height, one request each.

    Two extra columns say where each hour came from:
      weather_source  "archive" (ERA5 history) or "forecast-model" (recent days the archive lacks)
      blh_source      the same, for boundary layer height specifically
    """
    print("2/3  Open-Meteo weather and boundary layer height ...")
    params = {"latitude": LAT, "longitude": LON, "timezone": "GMT",
              "hourly": ",".join(WEATHER_VARS)}
    archive = get_json(OPEN_METEO_ARCHIVE, {
        **params, "start_date": str(start), "end_date": str(today - dt.timedelta(days=1))})
    recent = get_json(OPEN_METEO_RECENT, {**params, "past_days": 14, "forecast_days": 1})
    for name, data in [("archive", archive), ("recent", recent)]:
        if data is not None:
            (RAW / "weather").mkdir(parents=True, exist_ok=True)
            (RAW / "weather" / f"openmeteo_{name}_{today}.json").write_text(
                json.dumps(data), encoding="utf-8")
    if archive is None:
        raise SystemExit("Open-Meteo archive download failed. Check your internet and run again.")

    a = pd.DataFrame(archive["hourly"]).set_index("time")
    w = a
    if recent is not None:  # the archive can lag a few days; fill the gap from the recent feed
        w = a.combine_first(pd.DataFrame(recent["hourly"]).set_index("time"))
    w["weather_source"] = np.where(a["temperature_2m"].reindex(w.index).notna(),
                                   "archive", "forecast-model")
    w["blh_source"] = np.where(a["boundary_layer_height"].reindex(w.index).notna(), "archive",
                               np.where(w["boundary_layer_height"].notna(), "forecast-model", ""))
    w = w.reset_index().rename(columns={"time": "time_gmt"})
    w["time_gmt"] = pd.to_datetime(w["time_gmt"])
    w = w[(w.time_gmt >= pd.Timestamp(start)) & (w.time_gmt < pd.Timestamp(today))]
    return w.sort_values("time_gmt")


# ------------------------------------------------------------------ traffic
def poll():
    """Save one snapshot of every TfL road corridor's status (run every hour)."""
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
    print(f"{now} GMT: saved {len(new)} roads, {int((new.severity > 0).sum())} with delays "
          f"(mean severity {new.severity.mean():.2f})")


def load_traffic():
    """Read the saved snapshots (or None if polling has not started)."""
    if not HISTORY.exists():
        return None
    t = pd.read_csv(HISTORY, parse_dates=["polled_gmt"])
    return t.drop_duplicates(["polled_gmt", "road_id"])


def traffic_hourly(t):
    """One row per hour that has at least one snapshot."""
    cols = ["traffic_mean_severity", "traffic_roads_delayed", "traffic_snapshots"]
    if t is None or t.empty:
        return pd.DataFrame(columns=cols, index=pd.DatetimeIndex([], name="time_gmt"))
    snap = (t.groupby("polled_gmt").severity
            .agg(sev="mean", delayed=lambda s: int((s > 0).sum())).reset_index())
    snap["time_gmt"] = snap.polled_gmt.dt.floor("h")
    h = snap.groupby("time_gmt").agg(traffic_mean_severity=("sev", "mean"),
                                     traffic_roads_delayed=("delayed", "max"),
                                     traffic_snapshots=("polled_gmt", "count"))
    h["traffic_mean_severity"] = h.traffic_mean_severity.round(3)
    return h


def traffic_daily(t):
    """One row per day with at least MIN_SNAPSHOT_HOURS polled hours (9 of 12)."""
    cols = ["date", "hours_covered", "traffic_mean_severity", "traffic_delay_pct",
            "traffic_rush_severity", "traffic_rush_snapshots", "traffic_peak_roads"]
    if t is None or t.empty:
        return pd.DataFrame(columns=cols)
    t = t.copy()
    t["date"] = t.polled_gmt.dt.date
    t["hour_gmt"] = t.polled_gmt.dt.floor("h")
    london_hour = t.polled_gmt.dt.tz_localize("UTC").dt.tz_convert("Europe/London").dt.hour
    t["is_rush"] = london_hour.isin(RUSH_HOURS)
    out = []
    for date, g in t.groupby("date"):
        hours = g.hour_gmt.nunique()          # distinct hours that have a snapshot
        if hours < MIN_SNAPSHOT_HOURS:
            continue
        per_snapshot = g.groupby("polled_gmt").severity.apply(lambda s: int((s > 0).sum()))
        rush = g[g.is_rush]
        out.append({"date": date, "hours_covered": hours,
                    "traffic_mean_severity": round(g.severity.mean(), 3),
                    "traffic_delay_pct": round(100 * (g.severity > 0).mean(), 1),
                    "traffic_rush_severity": round(rush.severity.mean(), 3) if len(rush) else None,
                    "traffic_rush_snapshots": int(rush.polled_gmt.nunique()),
                    "traffic_peak_roads": int(per_snapshot.max())})
    return pd.DataFrame(out, columns=cols)


# ------------------------------------------------------------------ one row per hour
def build_hourly(air, weather, traffic_h, start, today):
    """Put air quality, weather, boundary layer and traffic side by side, one row per GMT hour.

    Every hour from start to the end of yesterday gets a row, even if some sources have nothing
    for it. Each source is lined up on the same hour; nothing is filled in.
    """
    grid = pd.date_range(pd.Timestamp(start), pd.Timestamp(today) - pd.Timedelta(hours=1),
                         freq="h", name="time_gmt")
    out = pd.DataFrame(index=grid)

    # air quality: average of the panel sites reporting that hour (all, roadside, background)
    a = air.dropna(subset=["value_ugm3"])
    for code, name in POLLUTANT_NAMES.items():
        base = name.lower().replace(".", "")                 # NO2 -> no2, PM2.5 -> pm25
        p = a[a.pollutant == name]
        out[f"{base}_ugm3"] = p.groupby("time_gmt").value_ugm3.mean().round(1)
        types = {t for t, sps in PANEL.values() if code in sps}
        for site_type in ("roadside", "background"):
            if site_type in types:
                out[f"{base}_{site_type}_ugm3"] = (p[p.site_type == site_type]
                                                   .groupby("time_gmt").value_ugm3.mean().round(1))
        if {"roadside", "background"} <= types:              # local traffic signal
            out[f"{base}_road_minus_bg_ugm3"] = (out[f"{base}_roadside_ugm3"]
                                                 - out[f"{base}_background_ugm3"]).round(1)

    # weather + boundary layer
    w = weather.set_index("time_gmt")
    for c in WEATHER_VARS + ["weather_source", "blh_source"]:
        out[c] = w[c]
    # ventilation index = boundary layer height x wind speed (m/s). Low = pollution is trapped.
    out["ventilation_index_m2s"] = ((out.wind_speed_10m / 3.6) * out.boundary_layer_height).round(0)

    # traffic
    out = out.join(traffic_h)

    # time columns (traffic follows London local time, so keep both clocks)
    london = out.index.tz_localize("UTC").tz_convert("Europe/London")
    out.insert(0, "is_weekend", (out.index.dayofweek >= 5))
    out.insert(0, "weekday", out.index.day_name())
    out.insert(0, "hour_london", london.hour)
    out.insert(0, "hour_gmt", out.index.hour)
    out.insert(0, "date", out.index.date)
    return out.reset_index()


# ------------------------------------------------------------------ main
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--poll", action="store_true",
                        help="save one TfL traffic snapshot and stop (used by the scheduled workflow)")
    args = parser.parse_args()
    if args.poll:
        return poll()

    days = args.days
    today = utc_today()                     # data runs up to the end of yesterday (GMT)
    start = today - dt.timedelta(days=days)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {start} to {today - dt.timedelta(days=1)} ({days} days)\n")

    air, failed = fetch_air(start, today)
    weather = fetch_weather(start, today)
    print("3/3  Traffic: reading saved TfL snapshots ...")
    t = load_traffic()
    th = traffic_hourly(t)
    tdaily = traffic_daily(t)
    merged = build_hourly(air, weather, th, start, today)

    air.to_csv(PROCESSED / "air_hourly.csv", index=False)
    weather.drop(columns=["weather_source", "blh_source"]).to_csv(
        PROCESSED / "weather_hourly.csv", index=False)       # same columns as before
    tdaily.to_csv(PROCESSED / "traffic_daily.csv", index=False)
    merged.to_csv(PROCESSED / "hourly_merged.csv", index=False)

    # ---- report
    hours = days * 24
    pct = lambda s: round(100 * s.notna().sum() / hours, 1)
    lines = [f"Fetch run {dt.datetime.now():%Y-%m-%d %H:%M}",
             f"Period: {start} to {today - dt.timedelta(days=1)} ({days} days, {hours} hours)", "",
             "Sources: London Air (LAQN) | Open-Meteo archive (ERA5) | Open-Meteo forecast "
             "(last 14 days) | TfL road status", "",
             "Air quality: % of hours with a value (site, type, pollutant)"]
    cov = (air.groupby(["pollutant", "site_code", "site_type"]).value_ugm3
           .agg(lambda v: round(100 * v.notna().sum() / hours, 1)).reset_index())
    for _, r in cov.iterrows():
        lines.append(f"   {r.pollutant:6} {r.site_code:4} {r.site_type:10} {r.value_ugm3:5.1f}%")
    lines += ["", "Weather and boundary layer: % of hours with a value"]
    for v in WEATHER_VARS:
        lines.append(f"   {v:24} {round(100 * weather[v].notna().sum() / hours, 1):5.1f}%")
    blh = weather.blh_source.value_counts()
    lines.append("   boundary layer source:   " + ", ".join(f"{k or 'missing'} {v}h" for k, v in blh.items()))
    lines += ["", "Traffic: hours with a TfL snapshot "
              + (f"(history starts {t.polled_gmt.min():%Y-%m-%d %H:%M})" if t is not None
                 else "(no history yet: run the hourly workflow)"),
              f"   {pct(merged.traffic_mean_severity):5.1f}% of hours (about "
              f"{100 * EXPECTED_SNAPSHOT_HOURS / 24:.0f}% expected on the current schedule), "
              f"{len(tdaily)} complete days (need {MIN_SNAPSHOT_HOURS}+ of {EXPECTED_SNAPSHOT_HOURS} polled hours)"]
    ok = pd.DataFrame({"air": merged.no2_ugm3.notna(),
                       "weather": merged[["wind_speed_10m", "precipitation"]].notna().all(axis=1),
                       "boundary layer": merged.boundary_layer_height.notna(),
                       "traffic": merged.traffic_mean_severity.notna()})
    lines += ["", "Hourly merged table: hours where each source has a value"]
    share = lambda s: round(100 * s.sum() / hours, 1)        # ok columns are True/False
    lines += [f"   {c:15} {share(ok[c]):5.1f}%" for c in ok]
    lines.append(f"   {'ALL FOUR':15} {share(ok.all(axis=1)):5.1f}%   <- hours usable for the full comparison")
    lines += ["", f"Rows saved: air {len(air):,}, weather {len(weather):,}, merged {len(merged):,}",
              f"Failed downloads: {', '.join(failed) if failed else 'none'}"]
    report = "\n".join(lines)
    (PROCESSED / "fetch_report.txt").write_text(report, encoding="utf-8")
    print("\n" + report)
    print("\nSaved: data/processed/air_hourly.csv, weather_hourly.csv, traffic_daily.csv, "
          "hourly_merged.csv, fetch_report.txt")


if __name__ == "__main__":
    main()
