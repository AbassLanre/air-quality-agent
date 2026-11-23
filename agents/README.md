# agents/ (PercyAbs builds, Precious writes the instructions)

The agents are built in Copilot Studio. This folder keeps their instructions and setup notes
under version control, so changes are tracked.

## How it fits together

One main agent with three child agents inside it:

| Agent | File | Job |
| --- | --- | --- |
| Coordinator (main) | `coordinator.md` | Judges how serious the day is, decides whether to fetch the forecast and draft an alert, runs the child agents |
| Analyst (child) | `analyst.md` | Explains which factors are linked to the day's pollution |
| Reviewer (child) | `reviewer.md` | Checks each claim against the numbers, sends unsupported claims back (max twice) |
| Advisor (child) | `advisor.md` | Turns the reviewed findings into one clear action |

There is no Collector agent. Fetching and cleaning run as Python in GitHub Actions every morning
(`.github/workflows/daily.yml`), which publishes `data/latest/summary.csv` and
`data/latest/summary_report.txt`. The coordinator reads them through the REST API tool
described in `summary_api.yaml`.

## Files

- `coordinator.md`, `analyst.md`, `reviewer.md`, `advisor.md`: the instructions pasted into each agent.
- `summary_api.yaml`: REST API tool for the daily summary and report (our data, via GitHub).
- `forecast_api.yaml`: REST API tool for the Open-Meteo weather forecast. The coordinator only
  calls it on Elevated or Serious days, or when asked about tomorrow.
- `setup_notes.md`: how the agents are configured in Copilot Studio, and what we found out.
- `changes_log.md`: what was changed in an instruction, why, and which test showed the problem.

## Every instruction file has five parts

1. Who you are: one line naming the role.
2. What you receive: the exact input.
3. Tools you may use: the tools this agent may call (only the coordinator has one).
4. Rules: what it must and must not do.
5. Answer format: the exact shape of the reply, so the next agent can read it.

## Build order (PercyAbs)

1. REST API tool from `summary_api.yaml`; test that it returns the CSV.
2. Coordinator, then the Analyst as a child agent.
3. Reviewer, tested with a planted unsupported claim.
4. Advisor, producing the final action.

## Done when

One run produces a daily action, every figure in it matches `data/latest/summary.csv`, and a
planted unsupported claim is sent back by the Reviewer.
