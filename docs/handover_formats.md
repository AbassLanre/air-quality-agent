# Handover formats

| From | To | What | Format |
| --- | --- | --- | --- |
| Carlos and Daniel | PercyAbs | Fetch, clean and summarise, ready to connect as tools | Python functions with a short note on how to run each |
| Carlos and Daniel | Precious and Ade | Daily summary table | CSV shaped like `data/sample/sample_summary.csv` |
| Precious | PercyAbs | The four instruction files | Markdown files in `agents/` |
| PercyAbs | Ade | The day's result plus each agent's step | JSON shaped like `data/sample/sample_result.json` |
| Daniel | Precious | Test results, ethics and limitations | `tests/results.csv` and `tests/ethics_and_limitations.md` |

## Open decisions

- [ ] What exactly is due on 14 December, and does the 21 January 2027 Turnitin submission still stand?
- [ ] Does the school's Copilot Studio allow several agents working together and custom tools?
- [ ] How do the agents reach the Python? Simplest: the script runs daily and saves the summary where agents read it.
- [ ] Is Claude available as the model in Copilot Studio?
- [ ] Project name.
