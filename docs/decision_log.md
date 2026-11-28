# Decision log

| Date | Decision | Why | Decided by |
| --- | --- | --- | --- |
| 2026-11-17 | Project changed from EcoMind (annual emissions) to a city air quality agent | Team wanted agents that fetch live, regularly updated data | Whole team |
| 2026-11-17 | Agent platform is Copilot Studio | Provided by the school | Whole team |
| 2026-11-17 | Streamlit and Python allowed alongside Copilot Studio | Team confirmed it is allowed | Whole team |
| 2026-11-17 | London first; other cities only if their sources have a data feed | Under four weeks to 14 December | Whole team |
| 2026-11-18 | Roles and repository folders agreed | See README | Whole team |
| 2026-11-18 | One Coordinator agent with child agents (Analyst, Reviewer, Advisor) in Copilot Studio | Child agents share one conversation, so passing work between them is built in; separate agents need extra publishing and connecting | PercyAbs |
| 2026-11-18 | Python runs in GitHub Actions every morning (06:00 UTC), not in Copilot Studio | Copilot Studio cannot host our Python scripts; GitHub Actions is free and runs on a schedule | PercyAbs |
| 2026-11-18 | Agents read the data through a REST API tool pointing at `data/latest/` on GitHub; repo made public | Simplest bridge from GitHub to Copilot Studio; the repo holds no keys | PercyAbs |
| 2026-11-18 | Code interpreter not used for the core pipeline (optional for charts) | It cannot fetch live data or run on a schedule, and the model writes new code each time, so numbers could change between runs | PercyAbs |
| 2026-11-23 | Carlos's pipeline merged with his column changes: 365-day window, `typical_peak_hour` instead of `link_hour`, new columns (`mixing_height_m`, `link_mixing`, `weekday_vs_weekend_pct`, `today_percentile`, `daqi_max`), fixed panel of 8 sites | 30 days is too few for reliable links; a correlation with the hour number is misleading; a fixed panel is more reliable than whichever sites report | Carlos, approved by PercyAbs |
| 2026-11-23 | Workflow copies the summary and report into `data/latest/` and caches downloads | `data/processed/` is not tracked by git; the cache avoids re-downloading a year of data daily | PercyAbs |
| 2026-11-23 | Collector agent dropped | GitHub Actions plus the data tool already do its job | PercyAbs |
| 2026-11-23 | Coordinator made goal-driven: rates each day Serious, Elevated or Normal, and decides whether to fetch the forecast and whether to draft an alert | A fixed step-by-step run is a pipeline, not an agent; the brief rewards agents that decide and act | PercyAbs |
| 2026-11-23 | Weather forecast tool added (Open-Meteo, today and tomorrow) | Lets the agent judge whether bad air is likely to persist or clear | PercyAbs |
| 2026-11-23 | Alerts only on Serious days, only after a person approves them, via Teams or Outlook | Avoids alert fatigue; a person stays accountable for any health-related message (ethics, 10% of the mark) | PercyAbs |
| 2026-11-23 | Data tool renamed in Copilot Studio to "Daily Air Quality Summary" | Clearer name for the agent and the demo | PercyAbs |
| 2026-11-23 | Alerts on Serious days only, no routine daily report | A daily message would be ignored; alerts keep attention for days that matter | PercyAbs |
| 2026-11-23 | Streamlit shows the data, Copilot Studio shows the agents; both read `data/latest/` | Agent answers cannot reach Streamlit automatically; keeping them separate is simplest and honest | PercyAbs |
| 2026-11-23 | Data tool reads JSON files (`summary.json`, `summary_report.json`) instead of the raw CSV and text | Copilot Studio REST tools expect JSON and failed on plain text ("'S' is an invalid start of a value"); the workflow now wraps the CSV and report in JSON | PercyAbs |
| 2026-11-23 | Coordinator carries on if only the report fails; stops only if the summary fails | The summary already has sites_missing, so a missing report should not block the whole assessment | PercyAbs |
| 2026-11-23 | Coordinator must treat every question, including weather-only ones, as an air quality assessment; no unit conversions or own advice | In testing it answered "weather today" as a weather bot, skipped the data tool and agents, converted to °F and gave clothing advice | PercyAbs |
| 2026-11-23 | Alert built as an agent flow: draft sent to a person by Outlook (Request for information), emailed to the team only if approved | Copilot Studio human review sends through Outlook; flow replies to the agent first so the chat does not wait for approval | PercyAbs |
| 2026-11-24 | fetch_traffic.py merged into fetch.py; one script fetches air, weather, boundary layer and traffic | One command and one place to maintain; summarise.py --fetch needs no change | Daniel |
| 2026-11-24 | New hourly_merged.csv: one row per GMT hour with air quality, weather, boundary layer and traffic; gaps left blank | Lets the analysis compare the same hour across all sources; nothing is filled in | Daniel |
| 2026-11-24 | Run date taken from the GMT clock instead of the computer's local date | Local runs and GitHub (UTC) cut the data at the same hour | Daniel |
| 2026-11-24 | Traffic from TfL road status, saved by snapshots in data/traffic/traffic_status.csv | TfL's /Road gives only the current status; no hourly history exists to download | Daniel |
| 2026-11-24 | Traffic polled every 3 hours instead of every hour | Cuts commits to main from about 24 to 8 a day | Daniel |
| 2026-11-24 | Rush windows (06-09 and 15-18 UTC) polled every 30 min; 01, 04, 12, 22 UTC once each	| Rush hour matters most for pollution, and the windows cover both GMT and BST; 20 runs a day | Daniel |
| 2026-11-24 | Traffic day counts only with 9 of 12 polled hours; replaces the 18-of-24 rule | The old rule would have discarded every day under the new schedule | Daniel |
| 2026-11-24 | TfL past-date status query not used for now | One value per window, not hourly; looks like worst disruption status, so it is a different, weaker measure | Daniel |
| 2026-11-24 | Traffic described as "disruption status", not "congestion" | Evidence points to disruption records (roadworks, incidents), not measured flow | Daniel |
| 2026-11-27 | Traffic data dropped: traffic.yml, TfL polling, data/traffic/ and the traffic code in fetch.py removed. Supersedes the 24 Nov traffic rows above | TfL gives disruption status (roadworks, incidents), not traffic volume, and history would only start on 27 Nov: under 3 weeks by 14 Dec, too little for a reliable link | PercyAbs |
| 2026-11-27 | hourly_merged.csv kept, without traffic columns | One row per hour of air quality, weather and boundary layer is the input the forecast model needs | PercyAbs |
| 2026-11-27 | Project focus changed to forecasting: predict London air quality 1 and 2 days ahead from past air quality and the weather forecast | Warning people before a bad day is more useful than reporting it afterwards, and gives the agents a real decision to make | PercyAbs |
| 2026-11-27 | Forecast made by a Python script in GitHub Actions; agents read it, they do not predict | An LLM asked to forecast would invent numbers that change each time (same reason the code interpreter is not used) | PercyAbs |
| 2026-11-27 | Forecast horizon capped at 2 days | Weather forecasts, the main input, lose accuracy quickly after 2 days | PercyAbs |
| 2026-11-27 | Forecast judged against two benchmarks: "tomorrow = today" and the CAMS European forecast (Open-Meteo air quality API) | The model is only worth using if it beats the simple guess; CAMS shows how close we get to a professional forecast | PercyAbs |
| 2026-11-27 | Forecast handover shape fixed in data/sample/sample_forecast.csv (16 columns, 8 rows: 4 pollutants x today and tomorrow) | Agents, Streamlit and tests can be built now against invented numbers while forecast.py is written | PercyAbs |
| 2026-11-27 | likely_level set by code with the Coordinator's percentile thresholds (90+ Serious, 75-89 Elevated) | The agents must not calculate; the same rule is used for measured and forecast days | PercyAbs |
| 2026-11-27 | Early warnings only when today or tomorrow is forecast Serious; a Serious yesterday alone no longer triggers an alert | The point is to warn before the bad day; alerting about yesterday is too late to act on | PercyAbs |
| 2026-11-27 | Open-Meteo weather tool (GetWeatherForecast) removed from the Coordinator; replaced by GetAirQualityForecast | forecast.json already carries the forecast weather; one tool is simpler and keeps the numbers consistent | PercyAbs |
| 2026-11-27 | Daily workflow runs data/forecast.py only if the file exists | The workflow can be merged now without breaking the daily summary | PercyAbs |
| 2026-11-28 | GitHub Actions runs twice a day, 06:00 and 12:00 UTC | The midday run picks up a newer weather forecast and the official index, which is often not published by 06:00 | PercyAbs |
| 2026-11-28 | Copilot Studio Recurrence trigger runs the Coordinator by itself at 07:30 UTC ("DAILY CHECK") | Without it the agent only acts when someone asks, so a forecast Serious day could pass with no warning; 07:30 leaves a buffer for late GitHub runs | PercyAbs |
| 2026-11-28 | Early warnings only from the daily check, never from chat | Stops the approver getting a duplicate alert every time someone asks about a Serious day | PercyAbs |
