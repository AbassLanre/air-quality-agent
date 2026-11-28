# data/ (Carlos, Daniel)

Python that fetches, cleans, summarises and forecasts London air quality from weather data.
Status: working and tested on 21 Nov 2026 (Windows, Python 3.15).

## The one daily command

Run from the project folder:

```
python data/summarise.py --fetch
```

First run about 1-5 minutes (downloads 365 days); after that about 10 seconds, because finished
months are cached in `data/raw/`. No API keys are needed for the data.

## Scripts

| Script | What it does | Writes |
| --- | --- | --- |
| `fetch.py` | Downloads hourly readings for a fixed panel of 8 London Air sites and hourly central-London weather from Open-Meteo, for the last 365 days. Keeps every raw download as a cache and tidies them into hourly tables (all times GMT), including one merged row per hour with air quality, weather, boundary layer and ventilation index. | `data/raw/`, `data/processed/air_hourly.csv`, `weather_hourly.csv`, `hourly_merged.csv`, `fetch_report.txt` |
| `forecast.py` | Learns from the past year how each pollutant follows the previous days and the weather (ridge regression, 8 small models), takes the Open-Meteo forecast for today and tomorrow, and predicts each pollutant's daily average, its percentile against the past year, the likely level and the model's typical error. Replays the last 90 days every run to measure that error. `--based-on 2026-11-20` replays any past day with recorded weather (tests, demo backup) | `data/processed/forecast.csv` (shaped like `data/sample/sample_forecast.csv`), `backtest.csv`, `backtest_days.csv`, `forecast_report.txt` |
| `summarise.py` | Cleans to daily values (a site's day counts only with 18 of 24 hours), averages the panel sites, adds the day's weather, calculates the links over the last 365 days, and adds the official daily index. | `data/processed/summary.csv`, `daily.csv`, `summary_report.txt` |

Other options:
- `python data/summarise.py --date 2026-11-05` gives the summary for any past day (test days).
- `python data/fetch.py --days 30` downloads a shorter period.

## Outputs

- `summary.csv`: one day, one row per pollutant (NO2, PM2.5, PM10, O3). This is what the agents read.
  Some columns are that day's values; the link columns, `typical_peak_hour`,
  `weekday_vs_weekend_pct` and `today_percentile` are calculated over the 365 days up to that day.
  Every column is explained at the top of `summarise.py`.
- `daily.csv`: every day of the last 365 days (for charts and choosing test days).
- `summary_report.txt`: the same summary as text, plus which sites had no full day of data.
- `hourly_merged.csv`: every hour of the past year, all sources side by side (input for the forecast).
- `forecast.csv` (once `forecast.py` exists): 8 rows, 4 pollutants x today and tomorrow. Column
  meanings: `data/sample/README.md`.

## For the agents (Lanre)

- Daily run: a GitHub Actions workflow runs `python data/summarise.py --fetch` once a day and
  publishes `data/latest/summary.csv` (and `.json`). It then runs `python data/forecast.py` if the
  file exists and publishes `data/latest/forecast.csv` (and `.json`). Lanre owns the workflow.
- The agents read the JSON versions. Column meanings: `data/sample/README.md`.
- `forecast.py` must: read only `data/processed/` (no new downloads except the weather forecast),
  give the same output for the same input, never fill in missing values (write a `note`
  instead), and keep the column names of `sample_forecast.csv` exactly.
- Notes for the workflow:
  - `data/raw/` is not committed, so each run downloads the full 365 days (about 1-5 minutes).
    Caching `data/raw/` between runs (for example with GitHub's cache action) cuts this to seconds.
  - Install with `pip install -r requirements.txt`. No keys are needed for the data.
    Tested on Python 3.12 and 3.15.
  - If the run happens before London Air publishes the official daily index, `daqi_max` is blank.
    Running later in the day makes it more likely to be filled.
  - `data/processed/summary_report.txt` lists the sites without a full day of data; the workflow
    copies it to `data/latest/` for the Coordinator.
  - `fetch.py` retries each download three times and lists any failed months in `fetch_report.txt`.
    `summarise.py` stops with an error if there is no data to summarise.

## Site panel

Chosen because each pollutant at each site had a value in at least 80% of hours over the past year.

| Site | Name | Type | Pollutants |
| --- | --- | --- | --- |
| HP1 | Lewisham - Honor Oak Park | background | NO2, PM2.5, PM10, O3 |
| KC1 | Kensington and Chelsea - North Kensington | background | NO2, O3 |
| TH6 | Tower Hamlets - Millwall Park | background | NO2, O3 |
| CW3 | Jubilee Park | background | PM2.5, PM10 |
| MY1 | Westminster - Marylebone Road | roadside | NO2 |
| BT4 | Brent - Ikea | roadside | NO2, PM2.5, PM10 |
| CE2 | Waterloo Place | roadside | NO2, PM2.5, PM10 |
| TH4 | Tower Hamlets - Blackwall | roadside | NO2 |

## Changes from the original plan (approved by Lanre, 23 Nov 2026)

- Links over 365 days instead of 30: 30 days is too few for reliable links. The history comes from
  the same two sources, so no new data source was added.
- Hour of day: `typical_peak_hour` instead of `link_hour`, because hour of day is a clock (0-23)
  and a correlation with it is misleading (NO2 peaks twice a day).
- Weekday: `weekday_vs_weekend_pct`.
- Added `mixing_height_m`, `link_mixing`, `today_percentile` and `daqi_max`.
- A fixed panel of 8 reliable sites instead of whichever sites report each day.
- There is no separate `clean.py`: cleaning happens inside `fetch.py` and `summarise.py`.

## Rules

- Raw and processed data are not committed (see `.gitignore`); only the scripts and notes are.
  The exception is `data/latest/`, which the daily workflow publishes.
- Data limitations: see `limitations.md`.

## Done when

- [x] One command fetches today's data and writes the summary
- [x] Three figures checked by hand against the source websites (see below)

## Hand checks (22 Nov 2026)

| Figure | Source value | Our value | Match |
| --- | --- | --- | --- |
| HP1 NO2, 15 Nov 00:00-02:00 (London Air) | 41.2, 47.0, 45.1 | 41.2, 47.0, 45.1 | Yes |
| Temperature, 15 Nov 00:00-02:00 (Open-Meteo) | 2.9, 2.8, 2.8 °C | 2.9, 2.8, 2.8 °C | Yes |
| Rain total and mean temperature, 20 Nov (calculated) | 0.5 mm, 6.6 °C | 0.5 mm, 6.6 °C | Yes |
