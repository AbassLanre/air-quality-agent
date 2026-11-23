"""
summarise.py  -  turn the hourly data into the daily summary table the agents read.

Run from the project folder, after fetch.py:
    python data/summarise.py --fetch             download the latest data first, then summarise
                                                 (the one daily command)
    python data/summarise.py                     summarise the data already saved (latest full day)
    python data/summarise.py --date 2026-11-12   summary for any earlier day (used for test days)

Reads:   data/processed/air_hourly.csv and weather_hourly.csv   (made by fetch.py)
Writes:  data/processed/summary.csv         the day's summary, one row per pollutant  <- agents read this
         data/processed/daily.csv           one row per day and pollutant (history for the charts)
         data/processed/summary_report.txt  short text version  <- paste this into the chat

How each number is made (so anyone can check it):
  - A site's day counts only if it has at least 18 of 24 hourly values (75%).
  - avg_ugm3        average of the panel sites that counted that day.
  - peak_ugm3/hour  highest single hourly value at any panel site that day, and its hour.
  - weather         central London from Open-Meteo: mean wind, total rain, mean temperature,
                    mean mixing height (how deep the air layer is that pollution can spread into).
  - link_*          Spearman correlation between the daily pollutant average and the daily
                    weather value over the last 365 days up to and including the date.
                    It runs from -1 to +1. Negative = when the weather value goes up,
                    pollution tends to go down.
  - typical_peak_hour  hour of day with the highest average over the same 365 days.
  - weekday_vs_weekend_pct  how much higher (+) or lower (-) the average is on weekdays
                    (Mon-Fri) than at weekends, over the same 365 days, in %.
  - today_percentile   % of those days with an average at or below this day's average.
  - daqi_max        highest official Daily Air Quality Index (1-10) for that pollutant across
                    all London Air sites that day (blank if not published yet).
  - All times are GMT. All numbers come from code; the agents never calculate.
"""
import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).parent
PROCESSED = ROOT / "processed"
RAW = ROOT / "raw"

WINDOW_DAYS = 365
MIN_HOURS = 18            # 75% of a day
MIN_DAYS_FOR_LINK = 30    # fewer days than this -> no link reported
POLLUTANTS = ["NO2", "PM2.5", "PM10", "O3"]
DAQI_CODES = {"NO2": "NO2", "PM2.5": "PM25", "PM10": "PM10", "O3": "O3"}
WEATHER_LINKS = {"link_wind": "wind_avg_kmh", "link_rain": "rain_total_mm",
                 "link_temp": "temp_avg_c", "link_mixing": "mixing_height_m"}
COLUMNS = ["city", "date", "pollutant", "avg_ugm3", "peak_ugm3", "peak_hour",
           "sites_reporting", "sites_missing", "wind_avg_kmh", "rain_total_mm",
           "temp_avg_c", "mixing_height_m", "link_wind", "link_rain", "link_temp",
           "link_mixing", "typical_peak_hour", "weekday_vs_weekend_pct", "today_percentile",
           "daqi_max", "window_days"]


def as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


# ------------------------------------------------------------------ load
def load():
    try:
        air = pd.read_csv(PROCESSED / "air_hourly.csv", parse_dates=["time_gmt"])
        weather = pd.read_csv(PROCESSED / "weather_hourly.csv", parse_dates=["time_gmt"])
    except FileNotFoundError:
        raise SystemExit("Data not found. Run  python data/fetch.py  first.")
    air["date"] = air.time_gmt.dt.date
    air["hour"] = air.time_gmt.dt.hour
    weather["date"] = weather.time_gmt.dt.date
    return air, weather


# ------------------------------------------------------------------ daily tables
def build_daily(air, weather):
    site_day = (air.groupby(["pollutant", "site_code", "date"]).value_ugm3
                .agg(site_mean="mean", hours="count").reset_index())
    valid = site_day[site_day.hours >= MIN_HOURS]
    panel_size = air.groupby("pollutant").site_code.nunique()

    daily = (valid.groupby(["pollutant", "date"])
             .agg(avg_ugm3=("site_mean", "mean"), sites_reporting=("site_code", "nunique"))
             .reset_index())

    wday = (weather.groupby("date")
            .agg(wind_avg_kmh=("wind_speed_10m", "mean"),
                 rain_total_mm=("precipitation", "sum"),
                 temp_avg_c=("temperature_2m", "mean"),
                 mixing_height_m=("boundary_layer_height", "mean"),
                 weather_hours=("temperature_2m", "count"))
            .reset_index())
    wday = wday[wday.weather_hours >= MIN_HOURS].drop(columns="weather_hours")

    daily = daily.merge(wday, on="date", how="left")
    return daily, valid, panel_size, wday


# ------------------------------------------------------------------ official index
def fetch_daqi(date):
    """Highest official DAQI per pollutant across London on the date (or {} if unavailable)."""
    url = (f"https://api.erg.ic.ac.uk/AirQuality/Daily/MonitoringIndex/"
           f"GroupName=London/Date={date}/Json")
    try:
        data = requests.get(url, timeout=60).json()
    except Exception as e:
        print(f"   (official index not available: {e})")
        return {}
    (RAW / "daqi").mkdir(parents=True, exist_ok=True)
    (RAW / "daqi" / f"daqi_{date}.json").write_text(json.dumps(data), encoding="utf-8")
    best = {}
    for la in as_list(data.get("DailyAirQualityIndex", {}).get("LocalAuthority")):
        for site in as_list(la.get("Site")):
            for sp in as_list(site.get("Species")):
                code, idx = sp.get("@SpeciesCode"), sp.get("@AirQualityIndex")
                if idx and str(idx).isdigit():
                    best[code] = max(best.get(code, 0), int(idx))
    return best


# ------------------------------------------------------------------ summary
def summarise(target, air, daily, valid, panel_size, wday):
    start = target - dt.timedelta(days=WINDOW_DAYS - 1)
    daqi = fetch_daqi(target)
    weather_today = wday[wday.date == target]
    rows, missing_names = [], {}

    for p in POLLUTANTS:
        hist = daily[(daily.pollutant == p) & (daily.date >= start) & (daily.date <= target)]
        today = hist[hist.date == target]
        hours_today = air[(air.pollutant == p) & (air.date == target)].dropna(subset=["value_ugm3"])
        hours_window = air[(air.pollutant == p) & (air.date >= start) & (air.date <= target)]

        all_sites = set(air.loc[air.pollutant == p, "site_code"])
        ok_sites = set(valid.loc[(valid.pollutant == p) & (valid.date == target), "site_code"])
        missing_names[p] = sorted(all_sites - ok_sites)

        row = {"city": "London", "date": str(target), "pollutant": p}
        if not today.empty:
            row["avg_ugm3"] = round(today.avg_ugm3.iloc[0], 1)
            avg_today = today.avg_ugm3.iloc[0]
            row["today_percentile"] = int(round(100 * (hist.avg_ugm3 <= avg_today).mean()))
        if not hours_today.empty:
            peak = hours_today.loc[hours_today.value_ugm3.idxmax()]
            row["peak_ugm3"] = round(peak.value_ugm3, 1)
            row["peak_hour"] = int(peak.hour)
        row["sites_reporting"] = len(ok_sites)
        row["sites_missing"] = int(panel_size.get(p, 0)) - len(ok_sites)

        if not weather_today.empty:
            w = weather_today.iloc[0]
            row["wind_avg_kmh"] = round(w.wind_avg_kmh, 1)
            row["rain_total_mm"] = round(w.rain_total_mm, 1)
            row["temp_avg_c"] = round(w.temp_avg_c, 1)
            row["mixing_height_m"] = int(round(w.mixing_height_m))

        both = hist.dropna(subset=["avg_ugm3", "wind_avg_kmh"])
        row["window_days"] = len(both)
        if len(both) >= MIN_DAYS_FOR_LINK:
            for col, wcol in WEATHER_LINKS.items():
                # Spearman = ordinary correlation of the ranks (no extra library needed)
                row[col] = round(both.avg_ugm3.rank().corr(both[wcol].rank()), 2)
        if not hours_window.empty:
            row["typical_peak_hour"] = int(hours_window.groupby("hour").value_ugm3.mean().idxmax())
        is_weekday = pd.to_datetime(hist.date).dt.day_of_week < 5
        wk, we = hist.avg_ugm3[is_weekday.values].mean(), hist.avg_ugm3[~is_weekday.values].mean()
        if len(hist) >= MIN_DAYS_FOR_LINK and pd.notna(wk) and pd.notna(we) and we > 0:
            row["weekday_vs_weekend_pct"] = int(round(100 * (wk - we) / we))
        if DAQI_CODES[p] in daqi:
            row["daqi_max"] = daqi[DAQI_CODES[p]]
        rows.append(row)

    summary = pd.DataFrame(rows).reindex(columns=COLUMNS)
    for col in ["peak_hour", "sites_reporting", "sites_missing", "mixing_height_m",
                "typical_peak_hour", "weekday_vs_weekend_pct", "today_percentile",
                "daqi_max", "window_days"]:
        summary[col] = summary[col].astype("Int64")   # whole numbers, blank if missing
    return summary, missing_names


# ------------------------------------------------------------------ main
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="day to summarise, YYYY-MM-DD (default: latest full day)")
    parser.add_argument("--fetch", action="store_true", help="run fetch.py first to get the latest data")
    args = parser.parse_args()

    if args.fetch:
        if subprocess.run([sys.executable, str(ROOT / "fetch.py")]).returncode != 0:
            raise SystemExit("fetch.py failed; see the message above.")
        print()

    print("Reading data/processed/ ...")
    air, weather = load()
    daily, valid, panel_size, wday = build_daily(air, weather)

    latest = daily.dropna(subset=["avg_ugm3"]).date.max()
    target = dt.date.fromisoformat(args.date) if args.date else latest
    if target < daily.date.min() or target > latest:
        raise SystemExit(f"No data for {target}. Choose a date between {daily.date.min()} and {latest}.")

    print(f"Summarising {target} (links over the {WINDOW_DAYS} days up to that date) ...")
    summary, missing = summarise(target, air, daily, valid, panel_size, wday)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    summary.to_csv(PROCESSED / "summary.csv", index=False)
    daily.round(2).to_csv(PROCESSED / "daily.csv", index=False)

    lines = [f"Summary for London, {target}  (made {dt.datetime.now():%Y-%m-%d %H:%M})", ""]
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        lines.append(summary.drop(columns=["city", "date"]).to_string(index=False))
    lines += ["", "Panel sites without a full day of data:"]
    lines += [f"   {p:6} {', '.join(missing[p]) if missing[p] else 'none'}" for p in POLLUTANTS]
    if summary.daqi_max.isna().all():
        lines.append("\nNote: the official daily index for this date is not published yet.")
    report = "\n".join(lines)
    (PROCESSED / "summary_report.txt").write_text(report, encoding="utf-8")
    print("\n" + report)
    print("\nSaved: data/processed/summary.csv, daily.csv, summary_report.txt")


if __name__ == "__main__":
    main()
