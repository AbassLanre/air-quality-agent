# Copilot Studio setup notes (owner: PercyAbs)

Environment: Northumbria University. Tabs on each agent: Overview, Knowledge, Tools, Agents,
Topics, Activity, Evaluation, Monitor, Channels, plus a "Test your agent" chat panel.

## What we found out

- [x] Can one agent hand work to another? Yes: Agents tab, "New child agent".
- [x] Can an agent call a custom tool? Yes: Tools, Add tool, REST API (upload `summary_api.yaml`).
- [x] Can Copilot Studio run our Python? No, not as an uploaded script. The Python runs in
      GitHub Actions and the agent reads its output through the REST API tool.
- [x] Can a run be scheduled daily? Yes, both sides: GitHub Actions runs the Python at 06:00 and
      12:00 UTC, and a Recurrence trigger in Copilot Studio runs the Coordinator at 07:30 UTC.
- [x] Which model is available (ChatGPT)?
- [ ] How does the result get out to the Streamlit page?
- [ ] Is code interpreter (Prompt tool setting) allowed on the school account? Optional, for charts.

## Configuration

| Item | Setting |
| --- | --- |
| Main agent | Coordinator, instructions from `coordinator.md` |
| Child agents | Analyst, Reviewer, Advisor |
| Tool 1 | REST API from `summary_api.yaml`, no authentication (GetDailySummary, GetSummaryReport) |
| Tool 2 | REST API from `airquality_forecast_api.yaml`, no authentication (GetAirQualityForecast) |
| Removed | "London Weather Forecast" (Open-Meteo) tool: no longer used, the forecast file carries the forecast weather |
| Data addresses | https://raw.githubusercontent.com/abasslanre/air-quality-agent/main/data/latest/summary.json and `forecast.json` in the same folder |

## First test (test_analyst, 18 Nov 2026)

Analyst instructions with the sample CSV attached: every figure quoted was in the table and it
said "linked to" throughout, but it wrote long numbered paragraphs instead of three short bullets.

## Daily check trigger (Recurrence)

| Item | Setting |
| --- | --- |
| Where | Coordinator > Overview > Triggers > Add trigger > Recurrence |
| Schedule | Every 1 day at 07:30, time zone (UTC) Coordinated Universal Time |
| Payload | `DAILY CHECK: Run the daily London air quality check now. Call GetDailySummary, GetSummaryReport and GetAirQualityForecast, follow every step in your instructions, and send an early warning for approval only if today or tomorrow is forecast Serious. Nobody is reading this conversation, so do not ask questions.` |
| Needs | Generative orchestration on; the agent published (the trigger does nothing until then) |
| Credentials | Triggers run with the maker's (PercyAbs's) connections, including Outlook in the alert flow |
| Cost | One run a day, billed like one user message in Copilot Credits |
| Where to see runs | Coordinator > Activity |

Source: Microsoft Learn, "Add an event trigger" and "Event triggers overview".
