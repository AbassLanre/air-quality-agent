"""
forecast.py  -  forecast London air quality for today and tomorrow, and test how good it is.

Run from the project folder, after summarise.py (it reads summarise.py's daily.csv):
    python data/forecast.py                         forecast from the latest measured day  <- daily run
    python data/forecast.py --based-on 2026-11-20   replay: forecast as if 2026-11-20 were the latest
                                                    measured day (uses the weather that actually
                                                    happened instead of a forecast; for tests and demos)

HOW IT WORKS (plain English)
  For each pollutant (NO2, PM2.5, PM10, O3) and each lead (1 = today, 2 = tomorrow) there is one
  small model: 4 x 2 = 8 models. Each model learns, from the past year, how a day's average
  pollution follows these clues:
      last_day_ugm3      the pollutant on the last measured day (pollution is "sticky")
      last_3_days_ugm3   its average over the last 3 measured days
      wind_avg_kmh       wind on the day being forecast
      rain_total_mm      rain on that day
      temp_avg_c         temperature on that day
      mixing_height_m    how deep the air layer is that pollution can spread into
      is_weekend         1 on Saturday and Sunday
  The model is ridge regression: a straight-line fit with a small penalty that stops any one
  clue getting an extreme weight. It is solved exactly with numpy, so the same input always
  gives the same output (no randomness, no extra library).

  Live, the weather clues come from the Open-Meteo forecast for today and tomorrow.

HOW WE KNOW HOW GOOD IT IS (the backtest, run every time)
  For each of the last 90 days that have a measurement, the model is trained only on what was
  known at the time and then predicts that day. Its average miss (mean absolute error) becomes
  typical_error_ugm3. The same is done for the simple guess "same as the last measured day"
  (persistence_error_ugm3). If the model does not beat the simple guess, the note column says so.
  Known weakness: the backtest uses the weather that actually happened, but live forecasts use
  forecast weather, which can be wrong. So live errors will usually be a bit larger.

RULES
  Numbers come from code; the agents never calculate or predict.
  Nothing is filled in: if a clue is missing, no forecast is made for that row and the note says why.

Reads:   data/processed/daily.csv            (made by summarise.py)
Writes:  data/processed/forecast.csv          8 rows, columns as data/sample/sample_forecast.csv
         data/processed/backtest.csv          one row per pollutant and lead: errors and level hits
         data/processed/backtest_days.csv     every backtest day: actual, model, simple guess (charts)
         data/processed/forecast_report.txt   short text version
"""
import argparse
import datetime as dt
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# ------------------------------------------------------------------ settings
ROOT = Path(__file__).parent
PROCESSED = ROOT / "processed"

OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"   # <- UPDATE HERE if it moves
LAT, LON = 51.5074, -0.1278                                     # central London, as fetch.py

POLLUTANTS = ["NO2", "PM2.5", "PM10", "O3"]
LEADS = [1, 2]                         # 1 = day after the last measured day (today), 2 = tomorrow
WEATHER = ["wind_avg_kmh", "rain_total_mm", "temp_avg_c", "mixing_height_m"]
FEATURES = ["last_day_ugm3", "last_3_days_ugm3"] + WEATHER + ["is_weekend"]

RIDGE_ALPHA = 1.0         # size of the penalty; 1.0 is a mild, standard choice
WINDOW_DAYS = 365         # history used for percentiles, same as summarise.py
BACKTEST_DAYS = 90        # days replayed to measure the error
MIN_TRAIN_ROWS = 60       # fewer complete training days than this -> no model
MIN_HOURS = 18            # a forecast day needs 18 of 24 hourly weather values, as summarise.py
SERIOUS, ELEVATED = 90, 75   # percentile thresholds, the same ones the Coordinator uses

COLUMNS = ["city", "made_on", "based_on_date", "target_date", "lead_days", "pollutant",
           "predicted_ugm3", "typical_error_ugm3", "persistence_error_ugm3",
           "predicted_percentile", "likely_level", "forecast_wind_kmh", "forecast_rain_mm",
           "forecast_temp_c", "forecast_mixing_height_m", "note"]


# ------------------------------------------------------------------ data
def load():
    """Daily pollution (one column per pollutant) and daily weather, one row per date."""
    try:
        d = pd.read_csv(PROCESSED / "daily.csv", parse_dates=["date"])
    except FileNotFoundError:
        raise SystemExit("data/processed/daily.csv not found. Run  python data/summarise.py --fetch  first.")
    days = pd.date_range(d.date.min(), d.date.max(), freq="D", name="date")
    pollution = d.pivot_table(index="date", columns="pollutant", values="avg_ugm3").reindex(days)
    weather = d.drop_duplicates("date").set_index("date")[WEATHER].reindex(days)
    return pollution, weather


def build_table(series, weather, lead):
    """One row per target day: the clues known `lead` days earlier, that day's weather, the answer."""
    t = pd.DataFrame(index=series.index)
    t["last_day_ugm3"] = series.shift(lead)
    t["last_3_days_ugm3"] = series.rolling(3, min_periods=2).mean().shift(lead)
    t[WEATHER] = weather
    t["is_weekend"] = (t.index.dayofweek >= 5).astype(float)
    t["actual"] = series
    return t


def clues_for(series, weather_row, base, target):
    """The clue row for a day after the data ends (live forecast or replay)."""
    last3 = series.loc[base - pd.Timedelta(days=2):base]
    return pd.Series({
        "last_day_ugm3": series.get(base, np.nan),
        "last_3_days_ugm3": last3.mean() if last3.notna().sum() >= 2 else np.nan,
        **{w: weather_row.get(w, np.nan) for w in WEATHER},
        "is_weekend": float(target.dayofweek >= 5),
    })


# ------------------------------------------------------------------ the model
def fit(X, y):
    """Ridge regression on standardised clues, solved exactly."""
    X, y = np.asarray(X, float), np.asarray(y, float)
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    w = np.linalg.solve(Z.T @ Z + RIDGE_ALPHA * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return {"mu": mu, "sd": sd, "w": w, "b": y.mean()}


def predict(model, x):
    z = (np.asarray(x, float) - model["mu"]) / model["sd"]
    return max(0.0, float(model["b"] + z @ model["w"]))      # a concentration cannot be negative


def train(table, last_known):
    """Fit on complete rows whose answer was known by `last_known`. None if too few rows."""
    rows = table.loc[:last_known].dropna(subset=FEATURES + ["actual"])
    if len(rows) < MIN_TRAIN_ROWS:
        return None
    return fit(rows[FEATURES], rows.actual)


# ------------------------------------------------------------------ helpers
def percentile(value, series, base):
    """% of the WINDOW_DAYS up to `base` with an average at or below `value` (as today_percentile)."""
    hist = series.loc[base - pd.Timedelta(days=WINDOW_DAYS - 1):base].dropna()
    return int(round(100 * (hist <= value).mean())) if len(hist) else None


def level(p):
    if p is None:
        return None
    return "Serious" if p >= SERIOUS else "Elevated" if p >= ELEVATED else "Normal"


def get_weather_forecast(dates):
    """Daily weather for the given dates from the Open-Meteo forecast, rolled up like summarise.py."""
    params = {"latitude": LAT, "longitude": LON, "timezone": "GMT",
              "hourly": "wind_speed_10m,precipitation,temperature_2m,boundary_layer_height",
              "start_date": str(min(dates).date()), "end_date": str(max(dates).date())}
    for attempt in range(1, 4):
        try:
            r = requests.get(OPEN_METEO_FORECAST, params=params, timeout=60)
            r.raise_for_status()
            h = pd.DataFrame(r.json()["hourly"])
            break
        except Exception as e:
            print(f"   weather forecast attempt {attempt} failed: {e}")
            time.sleep(3 * attempt)
    else:
        return pd.DataFrame(columns=WEATHER), "weather forecast unavailable, so no forecast was made"
    h["date"] = pd.to_datetime(h.time).dt.normalize()
    g = h.groupby("date")
    w = pd.DataFrame({"wind_avg_kmh": g.wind_speed_10m.mean(),          # km/h, Open-Meteo default
                      "rain_total_mm": g.precipitation.sum(),
                      "temp_avg_c": g.temperature_2m.mean(),
                      "mixing_height_m": g.boundary_layer_height.mean(),
                      "hours": g.temperature_2m.count()})
    w = w[w.hours >= MIN_HOURS].drop(columns="hours")
    return w, ""


# ------------------------------------------------------------------ backtest
def backtest(table, series, lead, end, days):
    """Replay the last `days` measured target days up to `end`, training only on what was known."""
    targets = table.loc[:end].dropna(subset=["actual"]).index[-days:]
    out = []
    for t in targets:
        base = t - pd.Timedelta(days=lead)
        row = table.loc[t]
        if row[FEATURES].isna().any():
            continue
        model = train(table, base)
        if model is None:
            continue
        pred = predict(model, row[FEATURES])
        out.append({"date": t.date(), "lead_days": lead, "actual_ugm3": row.actual,
                    "model_ugm3": round(pred, 1), "persistence_ugm3": row.last_day_ugm3,
                    "actual_level": level(percentile(row.actual, series, base)),
                    "model_level": level(percentile(pred, series, base))})
    return pd.DataFrame(out)


def score(days):
    """Average misses and level hits for one pollutant and lead."""
    if days.empty:
        return {"days_tested": 0}
    serious = days.actual_level == "Serious"
    return {"days_tested": len(days),
            "model_error_ugm3": round((days.model_ugm3 - days.actual_ugm3).abs().mean(), 1),
            "persistence_error_ugm3": round((days.persistence_ugm3 - days.actual_ugm3).abs().mean(), 1),
            "level_correct_pct": int(round(100 * (days.model_level == days.actual_level).mean())),
            "serious_days": int(serious.sum()),
            "serious_caught": int((serious & (days.model_level == "Serious")).sum()),
            "false_serious": int((~serious & (days.model_level == "Serious")).sum())}


# ------------------------------------------------------------------ main
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--based-on", help="replay: treat this date (YYYY-MM-DD) as the last measured "
                                           "day and use recorded weather instead of a forecast")
    parser.add_argument("--backtest-days", type=int, default=BACKTEST_DAYS)
    args = parser.parse_args()

    pollution, weather = load()
    latest = pollution.dropna(how="all").index.max()
    replay = args.based_on is not None
    base = pd.Timestamp(args.based_on) if replay else latest
    if replay and not (pollution.index.min() <= base <= latest):
        raise SystemExit(f"--based-on must be between {pollution.index.min().date()} and {latest.date()}.")
    made_on = (base + pd.Timedelta(days=1)).date() if replay else dt.datetime.now(dt.timezone.utc).date()
    targets = [base + pd.Timedelta(days=lead) for lead in LEADS]

    # weather for the forecast days
    if replay:
        fw, weather_note = weather.reindex(targets), "replay: recorded weather used, not a forecast"
    else:
        print("Getting the weather forecast for", ", ".join(str(t.date()) for t in targets), "...")
        fw, problem = get_weather_forecast(targets)
        weather_note = problem
    stale_note = ""
    if not replay and base.date() + dt.timedelta(days=1) != made_on:
        stale_note = f"latest measured day is {base.date()}, not yesterday"

    print(f"Forecasting from {base.date()} (backtest over the last {args.backtest_days} days) ...")
    rows, scores, bt_days = [], [], []
    for p in POLLUTANTS:
        series = pollution[p] if p in pollution else pd.Series(np.nan, index=pollution.index)
        for lead, target in zip(LEADS, targets):
            table = build_table(series, weather, lead)

            days = backtest(table, series, lead, base, args.backtest_days)
            s = score(days)
            scores.append({"pollutant": p, "lead_days": lead, **s})
            if not days.empty:
                bt_days.append(days.assign(pollutant=p))

            w = fw.loc[target] if target in fw.index else pd.Series(dtype=float)
            x = clues_for(series, w, base, target)
            model = train(table, base)
            notes = [n for n in (weather_note, stale_note) if n]

            pred = pct = None
            if model is None:
                notes.append("not enough history to train a model")
            elif pd.isna(x["last_day_ugm3"]) or pd.isna(x["last_3_days_ugm3"]):
                notes.append(f"no measured {p} for {base.date()}, so no forecast was made")
            elif x[WEATHER].isna().any():
                if not weather_note:
                    notes.append(f"no weather for {target.date()}, so no forecast was made")
            else:
                pred = round(predict(model, x[FEATURES]), 1)
                pct = percentile(pred, series, base)
                if s.get("days_tested") and s["model_error_ugm3"] >= s["persistence_error_ugm3"]:
                    notes.append("in the backtest this model did not beat the simple guess")

            rows.append({
                "city": "London", "made_on": made_on, "based_on_date": base.date(),
                "target_date": target.date(), "lead_days": lead, "pollutant": p,
                "predicted_ugm3": pred,
                "typical_error_ugm3": s.get("model_error_ugm3"),
                "persistence_error_ugm3": s.get("persistence_error_ugm3"),
                "predicted_percentile": pct, "likely_level": level(pct),
                "forecast_wind_kmh": round(x.wind_avg_kmh, 1) if pd.notna(x.wind_avg_kmh) else None,
                "forecast_rain_mm": round(x.rain_total_mm, 1) if pd.notna(x.rain_total_mm) else None,
                "forecast_temp_c": round(x.temp_avg_c, 1) if pd.notna(x.temp_avg_c) else None,
                "forecast_mixing_height_m": int(round(x.mixing_height_m)) if pd.notna(x.mixing_height_m) else None,
                "note": "; ".join(notes)})

    # today's 4 rows first, then tomorrow's; a stable sort keeps the pollutant order
    forecast = pd.DataFrame(rows, columns=COLUMNS).sort_values("lead_days", kind="stable")
    for col in ["predicted_percentile", "forecast_mixing_height_m"]:
        forecast[col] = forecast[col].astype("Int64")       # whole numbers, blank if missing
    scores = pd.DataFrame(scores)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    forecast.to_csv(PROCESSED / "forecast.csv", index=False)
    scores.to_csv(PROCESSED / "backtest.csv", index=False)
    (pd.concat(bt_days) if bt_days else pd.DataFrame()).to_csv(PROCESSED / "backtest_days.csv", index=False)

    lines = [f"Forecast for London from {base.date()} (made {made_on}{', REPLAY' if replay else ''})", ""]
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        lines.append(forecast[["target_date", "pollutant", "predicted_ugm3", "typical_error_ugm3",
                               "predicted_percentile", "likely_level", "note"]].to_string(index=False))
        lines += ["", f"Backtest, last {args.backtest_days} days (errors are average misses in ug/m3):",
                  scores.to_string(index=False)]
    report = "\n".join(lines)
    (PROCESSED / "forecast_report.txt").write_text(report, encoding="utf-8")
    print("\n" + report)
    print("\nSaved: data/processed/forecast.csv, backtest.csv, backtest_days.csv, forecast_report.txt")


if __name__ == "__main__":
    main()
