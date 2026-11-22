# data/ (Carlos, Daniel)

Python that fetches, cleans and summarises London air quality and weather data.
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
| `fetch.py` | Downloads hourly readings for a fixed panel of 8 London Air sites and hourly central-London weather from Open-Meteo, for the last 365 days. Keeps every raw download as a cache and tidies them into two hourly tables (all times GMT). | `data/raw/`, `data/processed/air_hourly.csv`, `weather_hourly.csv`, `fetch_report.txt` |
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

## For the agents (Lanre)

- The tool to press: `python data/summarise.py --fetch`, then read `data/processed/summary.csv`
  and `summary_report.txt` (missing sites, for the Collector).
- Copilot Studio cannot run Python on a laptop unless the code is put online (out of scope).
  Simplest bridge: save `summary.csv` where the agents can read it (for example a shared OneDrive
  folder), or upload it to the agents.

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

## Changes from the original plan (to confirm with PercyAbs / Lanre)

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
- Data limitations: see `limitations.md`.

## Done when

- [x] One command fetches today's data and writes the summary
- [ ] Three figures checked by hand against the source websites
