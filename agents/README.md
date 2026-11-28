# agents/ (PercyAbs builds, Precious writes the instructions)

The agents are built in Copilot Studio. This folder keeps their instructions and setup notes
under version control, so changes are tracked.

## How it fits together

One main agent with three child agents inside it:

| Agent | File | Job |
| --- | --- | --- |
| Coordinator (main) | `coordinator.md` | Rates yesterday (measured), today and tomorrow (forecast) as Serious, Elevated or Normal; runs the child agents; drafts an early warning when today or tomorrow is forecast Serious |
| Analyst (child) | `analyst.md` | Explains what yesterday's pollution is linked to and what the forecast shows |
| Reviewer (child) | `reviewer.md` | Checks each claim against the numbers (including that forecasts are labelled as forecasts with their error), sends unsupported claims back (max twice) |
| Advisor (child) | `advisor.md` | Turns the reviewed findings into one action for the worst forecast day |

The agents never calculate or predict. Python in GitHub Actions does that every morning
(`.github/workflows/daily.yml`) and publishes to `data/latest/`:

- `summary.json` / `summary_report.json`: yesterday's measured summary (`data/summarise.py`)
- `forecast.json`: today's and tomorrow's forecast (`data/forecast.py`, once it is written)

The coordinator reads them through two REST API tools.

## Files

- `coordinator.md`, `analyst.md`, `reviewer.md`, `advisor.md`: the instructions pasted into each agent.
- `summary_api.yaml`: REST API tool for the daily summary and report (GetDailySummary, GetSummaryReport).
- `airquality_forecast_api.yaml`: REST API tool for our forecast (GetAirQualityForecast).
  It replaces the old Open-Meteo weather tool, because the forecast file already carries the
  forecast weather.
- `alert_flow.md`: the early-warning flow with human approval.
- `setup_notes.md`: how the agents are configured in Copilot Studio, and what we found out.
- `changes_log.md`: what was changed in an instruction, why, and which test showed the problem.

## Every instruction file has five parts

1. Who you are: one line naming the role.
2. What you receive: the exact input.
3. Tools you may use: the tools this agent may call (only the coordinator has any).
4. Rules: what it must and must not do.
5. Answer format: the exact shape of the reply, so the next agent can read it.

## Build order (PercyAbs)

1. REST API tool from `summary_api.yaml` (done).
2. REST API tool from `airquality_forecast_api.yaml`. Until `forecast.py` exists, test the
   agents by attaching `data/sample/sample_forecast.csv` in the test chat.
3. Remove the old "London Weather Forecast" tool from the Coordinator in Copilot Studio.
4. Paste the updated Coordinator, Analyst and Reviewer instructions; Advisor when Precious
   has written it.
5. Test with the cases in `alert_flow.md` and `tests/`.

## Done when

One run rates yesterday, today and tomorrow; every figure matches `data/latest/summary.csv` and
`data/latest/forecast.csv`; forecasts are labelled with their typical error; a planted
unsupported claim is sent back by the Reviewer; and a forecast Serious day produces an early
warning that waits for approval.
