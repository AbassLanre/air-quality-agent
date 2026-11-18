# agents/ (PercyAbs builds, Precious writes the instructions)

The four agents are built in Copilot Studio. This folder keeps their instructions and setup notes
under version control, so changes are tracked.

## Files

- `collector.md`, `analyst.md`, `reviewer.md`, `advisor.md`: the instructions pasted into each agent.
- `setup_notes.md`: how each agent is configured in Copilot Studio (tools, order, schedule).
- `changes_log.md`: what was changed in an instruction, why, and which test showed the problem.

## Every instruction file has five parts

1. Who you are: one line naming the role.
2. What you receive: the exact input.
3. Tools you may use: the buttons this agent may press.
4. Rules: what it must and must not do.
5. Answer format: the exact shape of the reply, so the next agent can read it.

## Build order (PercyAbs)

1. Analyst, on `data/sample/sample_summary.csv`.
2. Reviewer, checking the Analyst against the same file.
3. Advisor, producing the final action.
4. Collector last, once Carlos's real code exists.

## Done when

One run produces a daily action, every figure in it matches the summary table, and a planted
unsupported claim is sent back by the Reviewer.
