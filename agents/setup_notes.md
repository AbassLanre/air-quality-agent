# Copilot Studio setup notes (owner: PercyAbs)

Environment: Northumbria University. Tabs on each agent: Overview, Knowledge, Tools, Agents,
Topics, Activity, Evaluation, Monitor, Channels, plus a "Test your agent" chat panel.

## What we found out

- [x] Can one agent hand work to another? Yes: Agents tab, "New child agent".
- [x] Can an agent call a custom tool? Yes: Tools, Add tool, REST API (upload `summary_api.yaml`).
- [x] Can Copilot Studio run our Python? No, not as an uploaded script. The Python runs in
      GitHub Actions and the agent reads its output through the REST API tool.
- [x] Can a run be scheduled daily? The data side is scheduled by GitHub Actions (06:00 UTC).
- [x] Which model is available (ChatGPT)?
- [ ] How does the result get out to the Streamlit page?
- [ ] Is code interpreter (Prompt tool setting) allowed on the school account? Optional, for charts.

## Configuration

| Item | Setting |
| --- | --- |
| Main agent | Coordinator, instructions from `coordinator.md` |
| Child agents | Analyst, Reviewer, Advisor |
| Tool | REST API from `summary_api.yaml`, no authentication |
| Data address | https://raw.githubusercontent.com/abasslanre/air-quality-agent/main/data/latest/summary.csv |

## First test (test_analyst, 18 Nov 2026)

Analyst instructions with the sample CSV attached: every figure quoted was in the table and it
said "linked to" throughout, but it wrote long numbered paragraphs instead of three short bullets.
