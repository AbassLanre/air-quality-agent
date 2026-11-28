# Handover formats

| From | To | What | Format |
| --- | --- | --- | --- |
| Carlos and Daniel | PercyAbs | Fetch, clean and summarise | `data/fetch.py`, `data/summarise.py`, run daily by `.github/workflows/daily.yml` |
| Carlos and Daniel | Everyone | Daily summary table | CSV shaped like `data/sample/sample_summary.csv`, published as `data/latest/summary.csv` and `summary.json` |
| Carlos and Daniel | Everyone | Forecast for today and tomorrow | `data/forecast.py` writing `data/processed/forecast.csv`, shaped exactly like `data/sample/sample_forecast.csv`. The workflow publishes it as `data/latest/forecast.csv` and `forecast.json` |
| Daniel and Carlos | PercyAbs and Precious | How good the forecast is | `docs/forecast_evaluation.md` (backtest table + plain-English summary); its errors feed `typical_error_ugm3` |
| Precious | PercyAbs | Analyst, Reviewer and Advisor instructions | Markdown files in `agents/` |
| PercyAbs | Ade | The day's result plus each agent's step | JSON shaped like `data/sample/sample_result.json` |
| Daniel | Precious | Test results, ethics and limitations | `tests/results.csv` and `tests/ethics_and_limitations.md` |

The column names in the two sample files are a contract. Changing one means telling PercyAbs
first, because the agents and the Streamlit page read them by name.

## Decisions (were open, now settled)

- [x] Due on 14 December: live presentation.
- [ ] Does the 21 January 2027 Turnitin submission still stand? (to confirm)
- [x] Copilot Studio allows several agents working together (child agents) and custom REST tools.
- [x] The agents reach the Python output through REST tools reading `data/latest/` on GitHub.
- [ ] Project name.
