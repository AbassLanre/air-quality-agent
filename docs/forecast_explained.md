# The forecast script, explained (for Carlos and Daniel)

File: `data/forecast.py`. First version written 28 Nov 2026. You two own it from here: review it,
run it, improve it, and write up the results in `docs/forecast_evaluation.md`.

## 1. What it does, in one paragraph

Every morning, after `summarise.py`, it predicts the daily average of NO2, PM2.5, PM10 and O3 for
**today** and **tomorrow**. It learns from the past year how pollution follows the previous days
and the weather, then plugs in the latest measurements and the Open-Meteo weather forecast. For each
prediction it also says how it ranks against the past year, whether that is Normal, Elevated or
Serious, and how far off the model usually is. The agents read this; they never predict anything
themselves.

## 2. How to run it

From the project folder, after `python data/summarise.py --fetch` (it needs `data/processed/daily.csv`):

| Command | What it does |
| --- | --- |
| `python data/forecast.py` | Live forecast for today and tomorrow (this is what GitHub Actions runs) |
| `python data/forecast.py --based-on 2026-11-20` | **Replay**: pretend 20 Nov was the latest measured day and forecast 21 and 22 Nov, using the weather that actually happened. Repeatable, so use it for test days and as a demo backup |
| `python data/forecast.py --backtest-days 60` | Change how many past days the backtest replays (default 90) |

It takes about 2 seconds. No new libraries: only pandas, numpy and requests, which we already use.

## 3. Dates: what "today" and "tomorrow" mean

London Air data always runs to the end of **yesterday**. So when the script runs on the morning of
day D:

- `based_on_date` = D-1, the last day with measurements
- `lead_days` 1 = D (today)
- `lead_days` 2 = D+1 (tomorrow)

We never forecast further than 2 days ahead, because weather forecasts get much less reliable
after that.

## 4. The model

### The clues (inputs)

For each day being forecast, the model looks at:

| Clue | Meaning | Why it helps |
| --- | --- | --- |
| `last_day_ugm3` | The pollutant on the last measured day | Pollution is "sticky": a bad day is often followed by another |
| `last_3_days_ugm3` | Its average over the last 3 measured days | Smooths out one odd day |
| `wind_avg_kmh` | Wind on the day being forecast | Wind blows pollution away |
| `rain_total_mm` | Rain that day | Rain washes particles out |
| `temp_avg_c` | Temperature that day | Cold, still days trap pollution; it also tracks the seasons |
| `mixing_height_m` | How deep the air layer is that pollution can spread into | A low "ceiling" traps pollution near the ground |
| `is_weekend` | 1 on Saturday and Sunday | Weekdays are usually dirtier |

### The method: ridge regression

There are **8 small models**: 4 pollutants x 2 leads (today, tomorrow).

Each one is **ridge regression**, which is linear regression (a "line of best fit" with several
inputs) plus a small penalty that stops any one clue getting an extreme weight. The penalty
matters because some clues move together (temperature and mixing height, yesterday and the 3-day
average); without it, plain regression can give silly weights.

It is solved exactly with numpy (the `fit` function, about 8 lines), so the same data always gives
the same forecast. No randomness, no extra library.

### Why not random forest or XGBoost?

You will probably be asked this in the presentation.

- **Small data.** About 365 days per pollutant. Tree models need more and overfit easily.
- **Explainable.** Each clue has a weight you can read ("lower mixing height goes with higher
  NO2"), which the agents and the slides need.
- **Repeatable.** No randomness, the same principle as keeping calculations out of the LLM.
- **Proportionate.** The test that matters is whether it beats "same as yesterday" (section 5).
  Ridge already does for most pollutants, so a complex model has to justify itself first.

A good addition if you have time: run a random forest or gradient boosting through the **same
backtest** and compare. If it does not clearly beat ridge, we keep ridge and say why. That
comparison is worth more marks than just picking XGBoost.

## 5. The backtest: how we know how good it is

### What a backtest is

A way to test a forecast on the past by pretending you are back on those days.

Analogy: to test a friend who says they can predict football scores, you cover up last season's
results, show them only what was known before each match, let them predict, then uncover the real
score. Repeat for every match and count how often they were close.

### What ours does

1. Take a past day, say 1 September.
2. Hide everything from 1 September on. The model only sees data up to 31 August.
3. Train on that, predict 1 September.
4. Uncover the real value and record the miss.
5. Move to 2 September (now allowed to see up to 1 September). Repeat.
6. Do this for the last 90 days, then average the misses.

The golden rule is **no peeking**: on each replayed day the model may only use what was known that
morning. If it saw the answer during training it would look brilliant in testing and fail live.
(In the code this is `train(table, base)`: it only uses rows up to the `base` date.)

### The two numbers it produces

- `typical_error_ugm3`: our model's average miss (mean absolute error). The agents quote it:
  "NO2 is forecast at 36 µg/m³, typically within 4".
- `persistence_error_ugm3`: the average miss of the lazy guess "same as the last measured day".
  If ours is not smaller, the model is not worth using, and the `note` column says so.

It also counts how often the level (Normal / Elevated / Serious) was right, how many real Serious
days it caught, and how many false Serious alarms it raised.

The backtest runs **every time** the script runs, so the errors stay up to date.

### First results (replay from 20 Nov 2026, real data, last 90 days)

Errors in µg/m³ (lower is better).

| Pollutant | Lead | Model miss | "Same as yesterday" miss | Level right | Serious days caught |
| --- | --- | --- | --- | --- | --- |
| NO2 | today | 3.7 | 5.7 | 83% | 15 of 19 |
| NO2 | tomorrow | 4.0 | 8.1 | 76% | 9 of 19 |
| PM2.5 | today | 4.1 | **3.8** | 72% | 8 of 14 |
| PM2.5 | tomorrow | 5.2 | 5.6 | 67% | 6 of 14 |
| PM10 | today | 5.2 | 5.7 | 72% | 8 of 11 |
| PM10 | tomorrow | 6.7 | 7.7 | 59% | 3 of 11 |
| O3 | today | 7.6 | 8.7 | 97% | none occurred |
| O3 | tomorrow | 10.1 | 13.0 | 93% | none occurred |

How to read it:

- **NO2 is strong**: tomorrow's error is half the lazy guess's.
- **PM2.5 today does not beat the lazy guess.** We say so honestly; the note column flags it.
- **It misses many Serious days a day ahead**, especially for particles (PM10: 3 of 11). This is
  the main weakness to report and the best thing to try to improve.

### The one big caveat

In the backtest the model uses the weather that **actually happened**. Live, it only has a weather
**forecast**, which can be wrong. So live accuracy will be somewhat worse than these numbers. This
is a standard approach, but it must be stated in the report and on the slides.

## 6. What it writes

All in `data/processed/` (not committed). The daily workflow copies the first three to
`data/latest/`.

| File | Contents |
| --- | --- |
| `forecast.csv` | 8 rows: 4 pollutants x today and tomorrow. Columns exactly as `data/sample/sample_forecast.csv` (meanings in `data/sample/README.md`). **Do not rename columns**; the agents read them by name |
| `backtest.csv` | One row per pollutant and lead: errors, level accuracy, Serious days caught, false alarms |
| `backtest_days.csv` | Every replayed day: actual, model, lazy guess, levels. For charts (Ade) and your write-up |
| `forecast_report.txt` | The same as text, handy to paste into chat |

## 7. Rules it follows (keep these if you change it)

- Code calculates; agents never predict.
- Same input, same output.
- Nothing is filled in. If a clue is missing (no measurement yesterday, no weather forecast), that
  row gets no prediction and the `note` says why.
- If the weather forecast cannot be downloaded, it still writes the file (blank predictions plus a
  note) instead of crashing, so the daily summary still gets published.
- `likely_level` uses the same percentile thresholds as the Coordinator: 90+ Serious, 75 to 89
  Elevated, below 75 Normal.

## 8. Where to change things

All settings are at the top of the file:

| Setting | Default | Meaning |
| --- | --- | --- |
| `RIDGE_ALPHA` | 1.0 | Size of the penalty. Bigger = weights pulled closer to zero |
| `BACKTEST_DAYS` | 90 | Days replayed |
| `MIN_TRAIN_ROWS` | 60 | Fewer complete training days than this = no model |
| `FEATURES` | 7 clues | Add or remove clues here (and in `build_table` / `clues_for`) |
| `SERIOUS`, `ELEVATED` | 90, 75 | Level thresholds; keep in step with `agents/coordinator.md` |

## 9. What is left for you two

1. **Review the code** and run both commands in section 2. Before you run the replay, write down
   what you expect (8 rows, NO2 on 21 Nov around 33 to 34 µg/m³, Elevated), then check.
2. **CAMS comparison.** Start saving the CAMS forecast daily from Open-Meteo's air quality API
   (`air-quality-api.open-meteo.com`) for today and tomorrow, then compare its misses with ours
   over the days collected before 14 Dec.
3. **Write `docs/forecast_evaluation.md`**: the backtest table, the CAMS comparison, and 3 to 5
   plain sentences on what it means, including the weather caveat.
4. **Optional: try a better model** (more training history, extra clues such as the previous
   day's wind, or a random forest) through the same backtest. Only keep a change if it beats the
   current numbers.
5. Tell Lanre before changing any output column.
