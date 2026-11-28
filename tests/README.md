# tests/ (Daniel lead, Carlos support)

## To build

- **Forecast backtest**: built into `data/forecast.py`, which writes `data/processed/backtest.csv`
  (average miss for our model and for "same as the last measured day", level accuracy, Serious days
  caught and false alarms) and `backtest_days.csv` (every day). Still to do: the CAMS comparison
  and the write-up in `docs/forecast_evaluation.md`.
- **Replay test days** with `python data/forecast.py --based-on <date>` (recorded weather, so
  the result is repeatable).
- `test_days.csv`: about 10 test cases (forecast Serious, forecast Normal after a Serious
  yesterday, missing data, forecast unavailable, weather-only question), each with the expected
  correct answer written down BEFORE running the agents. Until `forecast.py` exists, use
  `data/sample/sample_forecast.csv` (edit a copy for each case).
- A planted unsupported claim, and a planted "will be" forecast claim, to check the Reviewer
  catches both.
- `results.csv`: score per run (numbers correct, every claim backed by the tables, forecasts
  labelled with their error, action clear and sensible, alert only when expected).
- A comparison of runs with and without the Reviewer.
- `ethics_and_limitations.md`: correlation is not cause, forecasts are uncertain and labelled as
  such, modelled values are estimates, health advice stays general, a person approves every alert.

## Done when

Backtest results, results for all test cases and a one-page ethics and limitations summary are
ready for the slides.
