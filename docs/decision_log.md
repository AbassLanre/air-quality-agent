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
