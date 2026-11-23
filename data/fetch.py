"""
fetch.py  -  download London air quality and weather history (default: last 365 days).

Run from the project folder (the one that contains data/ and agents/):
    python data/fetch.py              last 365 days (first run about 3-6 minutes)
    python data/fetch.py --days 30    a shorter test

What it does:
  1. Downloads hourly readings for a fixed panel of reliable London sites
     from London Air (LAQN), one month at a time.
  2. Downloads hourly weather for central London from Open-Meteo.
  3. Saves every raw download in data/raw/ (a cache: finished months are
     never downloaded twice, so running it again each day is fast).
  4. Writes two tidy tables in data/processed/:
        air_hourly.csv      site_code, site_type, pollutant, time_gmt, value_ugm3
        weather_hourly.csv  time_gmt + one column per weather variable
  5. Writes data/processed/fetch_report.txt  <- paste this into the chat

All times are GMT (London Air's own clock).
"""
import argparse
import datetime as dt
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

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
WEATHER_VARS = [
    "temperature_2m", "relative_humidity_2m", "precipitation",
    "wind_speed_10m", "wind_direction_10m", "surface_pressure",
    "boundary_layer_height", "cloud_cover",
]

LAQN = "https://api.erg.ic.ac.uk/AirQuality"
ROOT = Path(__file__).parent
RAW = ROOT / "raw"
PROCESSED = ROOT / "processed"


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
    print(f"1/2  London Air: {len(jobs)} site-pollutant-months to check ...")

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


# ------------------------------------------------------------------ weather
def fetch_weather(start, today):
    print("2/2  Open-Meteo weather ...")
    params = {"latitude": LAT, "longitude": LON, "timezone": "GMT",
              "hourly": ",".join(WEATHER_VARS)}
    archive = get_json("https://archive-api.open-meteo.com/v1/archive", {
        **params, "start_date": str(start), "end_date": str(today - dt.timedelta(days=1))})
    recent = get_json("https://api.open-meteo.com/v1/forecast", {
        **params, "past_days": 14, "forecast_days": 1})
    for name, data in [("archive", archive), ("recent", recent)]:
        if data is not None:
            (RAW / "weather").mkdir(parents=True, exist_ok=True)
            (RAW / "weather" / f"openmeteo_{name}_{today}.json").write_text(
                json.dumps(data), encoding="utf-8")
    if archive is None:
        raise SystemExit("Open-Meteo archive download failed. Check your internet and run again.")

    w = pd.DataFrame(archive["hourly"])
    if recent is not None:  # the archive can lag a few days; fill the gap from the recent feed
        r = pd.DataFrame(recent["hourly"])
        w = w.set_index("time").combine_first(r.set_index("time")).reset_index()
    w = w.rename(columns={"time": "time_gmt"})
    w["time_gmt"] = pd.to_datetime(w["time_gmt"])
    w = w[(w.time_gmt >= pd.Timestamp(start)) & (w.time_gmt < pd.Timestamp(today))]
    return w.sort_values("time_gmt")


# ------------------------------------------------------------------ main
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=365)
    days = parser.parse_args().days

    today = dt.date.today()                 # data runs up to the end of yesterday
    start = today - dt.timedelta(days=days)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {start} to {today - dt.timedelta(days=1)} ({days} days)\n")

    air, failed = fetch_air(start, today)
    weather = fetch_weather(start, today)

    air.to_csv(PROCESSED / "air_hourly.csv", index=False)
    weather.to_csv(PROCESSED / "weather_hourly.csv", index=False)

    # ---- report
    hours = days * 24
    lines = [f"Fetch run {dt.datetime.now():%Y-%m-%d %H:%M}",
             f"Period: {start} to {today - dt.timedelta(days=1)} ({days} days, {hours} hours)", "",
             "Air quality: % of hours with a value (site, type, pollutant)"]
    cov = (air.groupby(["pollutant", "site_code", "site_type"]).value_ugm3
           .agg(lambda v: round(100 * v.notna().sum() / hours, 1)).reset_index())
    for _, r in cov.iterrows():
        lines.append(f"   {r.pollutant:6} {r.site_code:4} {r.site_type:10} {r.value_ugm3:5.1f}%")
    lines += ["", "Weather: % of hours with a value"]
    for v in WEATHER_VARS:
        lines.append(f"   {v:24} {round(100 * weather[v].notna().sum() / hours, 1):5.1f}%")
    lines += ["", f"Rows saved: air {len(air):,}, weather {len(weather):,}",
              f"Failed downloads: {', '.join(failed) if failed else 'none'}"]
    report = "\n".join(lines)
    (PROCESSED / "fetch_report.txt").write_text(report, encoding="utf-8")
    print("\n" + report)
    print("\nSaved: data/processed/air_hourly.csv, weather_hourly.csv, fetch_report.txt")


if __name__ == "__main__":
    main()
