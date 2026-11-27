# Next steps: from "what happened yesterday" to "what is coming"

Written 27 Nov 2026. Presentation: Monday 14 Dec. That leaves about 2.5 weeks.

## The new plan in one paragraph

Every morning a Python script in GitHub Actions learns from the past year of London air
quality and weather, takes the weather forecast for today and tomorrow, and predicts how
polluted each day will be. It writes the prediction to `data/latest/forecast.json`. The
agents in Copilot Studio do not predict anything. They read that file, decide whether today
and tomorrow look Normal, Elevated or Serious, explain why, and draft an early warning on
Serious days. A person approves the warning before anyone receives it. Traffic data is
dropped (see the decision log, 27 Nov).

Pitch: **"Our agents warn London about bad air days before they happen, and explain why."**

## Already done (27 Nov, branch `drop-traffic`)

- Removed `.github/workflows/traffic.yml` (the TfL polling job) and `data/traffic/`.
- Removed all traffic code from `data/fetch.py`. It still writes `hourly_merged.csv`
  (air quality, weather, boundary layer, ventilation index), now without traffic columns.
- Removed `TFL_APP_KEY` from `.env.example` and the traffic lines from `data/limitations.md`.
- Added 6 rows to `docs/decision_log.md`.

## Important detail about dates

The data always runs to the end of **yesterday** (London Air publishes with a delay). So
when the script runs on the morning of day D, the last full day it knows is D-1, and it
predicts:

- **lead 1 = today (D)**
- **lead 2 = tomorrow (D+1)**

No further than that. Weather forecasts, our main input, get much worse after 2 days.

---

## Phase 0: housekeeping (Sat 28 to Sun 29 Nov). Owner: PercyAbs

1. Push `drop-traffic`, open a PR, merge it into `main`.
   - Verify: on GitHub, the Actions tab no longer lists "Traffic snapshot". Prediction: only
     the daily workflow is left.
2. If anyone added a `TFL_APP_KEY` secret: Settings > Secrets and variables > Actions > delete it.
3. Check the next 06:00 UTC daily run, the first one using the new `fetch.py`.
   - Verify: green tick, and a new "Daily summary" commit. Prediction: `data/latest/summary.csv`
     has the same columns as before. Nothing the agents read has changed.
4. Send the team this file and get a yes or no on the plan by Sunday evening.

## Phase 1: the forecast script (Mon 30 Nov to Wed 2 Dec). Owners: Carlos and Daniel (Data)

Create `data/forecast.py`. In plain English it should:

1. **Read the history.** Use `data/processed/daily.csv` (one row per day and pollutant, made
   by `summarise.py`) or `hourly_merged.csv` rolled up to days. One row per day with:
   - the pollutant's daily average (London panel)
   - the same day's weather: mean wind, total rain, mean temperature, mean boundary layer
     height, ventilation index
   - weekday or weekend
2. **Build the "clues" for each prediction.** For a target day:
   - pollution the day before the forecast was made (lead 1: yesterday; lead 2: also yesterday)
   - the average over the last 3 days
   - the target day's weather (from the archive when training, from the forecast when live)
   - weekday or weekend, and month (winter is dirtier)
3. **Train one simple model per pollutant and per lead.** Start with linear regression
   (scikit-learn `Ridge`). 4 pollutants x 2 leads = 8 small models. Add `scikit-learn` to
   `requirements.txt`.
4. **Get the live weather forecast** for today and tomorrow from Open-Meteo
   (`api.open-meteo.com/v1/forecast`, hourly, including `boundary_layer_height`), and roll it
   up to days the same way as the history.
5. **Predict and translate.** For each pollutant and day, write:
   - `predicted_ugm3`
   - `predicted_percentile`: where that sits against the past 365 days (same idea as
     `today_percentile`)
   - `likely_level`: Serious (90+), Elevated (75 to 89), Normal (below 75), using the same
     thresholds the Coordinator already uses
   - `typical_error_ugm3`: the model's average miss from the backtest (Phase 2), so the agents
     can say how sure we are
   - the weather values used (forecast wind, rain, boundary layer), so the Analyst can explain
6. **Write** `data/processed/forecast.csv`. The workflow (Phase 3) copies it to
   `data/latest/forecast.json`.

Rules (same as the rest of the project): the numbers come from code, never from the agents.
Same input gives the same output. Never fill in missing values: if yesterday has no data,
say so in a `note` column.

- Verify: run `python data/forecast.py` twice. Prediction: 8 rows (4 pollutants x 2 days),
  identical numbers both times, every `predicted_ugm3` between 0 and the highest value seen
  in the past year.

**Known weakness to state in the report:** in training we use the weather that actually
happened. Live, we only have a forecast of it, which can be wrong. So live accuracy will be
a bit worse than the backtest. This is normal practice, but we must say it.

## Phase 2: prove it works (Wed 2 to Fri 4 Dec). Owners: Daniel and Carlos (Testing)

Create `data/backtest.py` and `docs/forecast_evaluation.md`.

1. **Backtest.** For each of the last 90 days: train only on days before it, predict it,
   compare with what actually happened. (Pretend it is that morning; no peeking at the future.)
2. **Compare against benchmark 1, "tomorrow = today"** (persistence). For each pollutant and
   lead, report the mean absolute error (MAE, the average miss in ug/m3) for:
   - our model
   - persistence
   - Verify: prediction: our model beats persistence for at least NO2 and PM2.5 at lead 2.
     If it does not, we say so honestly and simplify the claim.
3. **Benchmark 2, CAMS (the European forecast).** Open-Meteo's air quality API
   (`air-quality-api.open-meteo.com`) serves the CAMS forecast. We cannot get its *old
   forecasts* reliably, so start a small daily job **now** that saves CAMS's forecast for
   today and tomorrow. By 14 Dec we will have about 10 days to compare. Present it as
   "early comparison", not a final verdict.
4. **Level accuracy.** How often did we get the level (Normal/Elevated/Serious) right? Did we
   miss any Serious days? Missing a Serious day matters more than a false alarm, so report it
   separately.
5. Write the results table and 3 to 5 plain sentences into `docs/forecast_evaluation.md`.
   The `typical_error_ugm3` used in Phase 1 comes from here.

## Phase 3: put it in the daily run (Thu 3 to Fri 4 Dec). Owner: PercyAbs

1. In `.github/workflows/daily.yml`, after `summarise.py`, run `python data/forecast.py`, copy
   `forecast.csv` into `data/latest/`, and wrap it as `forecast.json` the same way
   `summary.json` is made (Copilot Studio REST tools need JSON).
2. Add `agents/forecast_data_api.yaml`, a copy of `summary_api.yaml` pointing at
   `/data/latest/forecast.json`, operationId `GetAirQualityForecast`.
   - Verify: open the raw GitHub URL in a browser. Prediction: JSON with a `forecast_csv`
     field holding 8 rows and a `made_for` date of today.
3. Decide on the old weather tool (`GetWeatherForecast`): **keep it** only if the agents need
   weather beyond what is in `forecast.json`. Otherwise remove it to keep the demo simple.

## Phase 4: update the agents (Fri 4 to Sun 6 Dec). Owners: PercyAbs and Precious

In Copilot Studio, add the `GetAirQualityForecast` tool to the Coordinator, then update the
instructions in `agents/` (and record each change in `agents/changes_log.md`):

- **Coordinator**
  - Always call GetDailySummary **and** GetAirQualityForecast.
  - Rate three things: yesterday (measured), today (forecast), tomorrow (forecast).
  - Alert rule: draft an alert if **today or tomorrow is forecast Serious**, through the same
    approval flow. Title starts "Forecast:" so nobody confuses it with a measurement.
  - Questions like "Will tomorrow be bad?" go straight to the forecast.
- **Analyst**: explains *why* the forecast says what it says, only from columns in the file
  (for example "forecast wind is low and the boundary layer is shallow, and both are linked to
  higher NO2 in summary.csv").
- **Reviewer**: new rules. A forecast must be labelled as a forecast. It must quote the
  `typical_error_ugm3`. It must never be stated as certain.
- **Advisor**: one action for the forecast day (for example "plan outdoor school activities
  for the morning"), never medical advice.

- Verify with 3 test questions. Predictions:
  1. "What's tomorrow looking like?" calls both tools and answers with level + figure + error.
  2. On a day forecast Serious, it drafts an alert that goes to the approver.
  3. On a Normal forecast, no alert, and it says why.

## Phase 5: Streamlit (Sat 5 to Tue 8 Dec). Owner: Ade

Add a forecast section that reads `data/latest/forecast.json` and `daily.csv`:

1. A line chart: the last 14 days measured, then today and tomorrow predicted (dashed), with
   the typical error shown as a shaded band.
2. Coloured cards for today and tomorrow: Normal / Elevated / Serious.
3. A small "How good is the forecast?" chart from the backtest: model vs "tomorrow = today".

- Verify: the page loads from the live GitHub files. Prediction: today's cards match what
  the Coordinator says for the same day.

## Phase 6: end-to-end testing (Mon 7 to Wed 9 Dec). Owners: Daniel and Carlos

1. Extend `tests/test_days.csv` with forecast cases: a past Serious day, a past Normal day, a
   day with missing data, and a weather-only question.
2. Run each case through the Coordinator and record pass or fail with a screenshot.
3. Re-run the backtest with the latest data so the numbers on the slides are current.

## Phase 7: presentation (Wed 9 to Sun 13 Dec). Owners: PercyAbs (integration), Precious (presentation)

1. **Feature freeze on Wed 9 Dec.** After that, fixes only.
2. Slides: problem, data, how the forecast works (one simple diagram), agents and who decides
   what, results vs benchmarks, ethics (a person approves every alert, honest uncertainty),
   limitations, what we would do next.
3. Demo script plus a **recorded backup video** in case the live APIs or Copilot Studio fail
   on the day.
4. Full rehearsal on Sat 12 or Sun 13 Dec.

---

## Who does what (summary)

| Who | Main job | Due |
| --- | --- | --- |
| PercyAbs | Merge cleanup, daily workflow + forecast tool, Coordinator, integration | 29 Nov, 4 Dec, 6 Dec |
| Carlos + Daniel | `forecast.py`, backtest, CAMS saving, evaluation write-up, test runs | 2 Dec, 4 Dec, 9 Dec |
| Precious | Analyst/Reviewer/Advisor updates, slides lead | 6 Dec, 11 Dec |
| Ade | Streamlit forecast page | 8 Dec |
| Everyone | Rehearsal | 12 or 13 Dec |

## Open questions for the team

1. Train on 1 year or 2? Two years gives the model more winters to learn from but doubles the
   download (the cache in `data/raw/` makes repeat runs cheap).
2. Should the CAMS comparison job be a separate small workflow or part of the daily one?
3. Do we keep the old weather tool in Copilot Studio or rely only on `forecast.json`?
