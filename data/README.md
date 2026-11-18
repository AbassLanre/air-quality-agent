# data/ (Carlos, Daniel)

Python that fetches, cleans and summarises the data each day. The agents call these as tools.

## To build

- `fetch.py`: download today's London Air readings and Open-Meteo weather, save raw files to `data/raw/`.
- `clean.py`: drop sites with no data, line up timestamps, one tidy hourly table in `data/processed/`.
- `summarise.py`: produce the daily summary in exactly the shape of `sample/sample_summary.csv`.
- Link strengths (correlations) between each pollutant and wind, rain, temperature and hour of day,
  calculated over the last 30 days of saved data.

## Rules

- Output columns must match `sample/sample_summary.csv`. Tell PercyAbs before changing any.
- Raw and processed data are not committed (see `.gitignore`); only `sample/` is.

## Done when

One command fetches today's data and writes the summary, and three figures checked by hand match the source websites.
