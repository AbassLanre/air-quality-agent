# City Air Quality Agent

LD7237 Hackathon group project, Northumbria University London (AI Agents Unleashed).

A set of AI agents that collect city air quality and weather data once a day, work out which
factors are most strongly linked to pollution, check their own claims, and give one clear action.
London first; other cities only if their sources have a usable data feed.

## How it works

There are two kinds of workers:

- **Code** (Python) fetches, cleans and calculates. Same job every time, no AI involved.
- **Agents** (Copilot Studio) read what the code produced, explain it, check it and advise.
  Agents never do the arithmetic; they press a "button" (a tool) that runs the Python.

Daily run:

1. **Collector** starts the fetch and clean, reports what arrived and what is missing.
2. **Analyst** explains which factors are linked to today's pollution, using the summary table.
3. **Reviewer** checks each claim against the numbers and sends unsupported claims back (max twice).
4. **Advisor** turns the reviewed findings into one clear action.
5. The **Streamlit** page shows the charts, the agents' steps and the action.

## Data sources

| Source | What it gives | Key needed | Status |
| --- | --- | --- | --- |
| [London Air](https://api.erg.ic.ac.uk/AirQuality/Hourly/MonitoringIndex/GroupName=London/Json) | Hourly readings per monitoring site | No | Checked 17 Nov 2026, works |
| [Open-Meteo](https://open-meteo.com/) | Weather and modelled air quality | No | Checked 17 Nov 2026, works |
| Air Quality England | Site readings | ? | Not checked yet (Daniel) |
| Scottish Air Quality | Site readings | ? | Not checked yet (Daniel) |

## Team and folders

| Folder | Owner | Support | Contents |
| --- | --- | --- | --- |
| `data/` | Carlos | Daniel | Fetch, clean and summarise scripts |
| `data/sample/` | PercyAbs | Everyone | Agreed sample files everyone builds against |
| `agents/` | PercyAbs (build), Precious (instructions) | | Four agent instruction files, Copilot Studio setup notes |
| `streamlit/` | Ade | | The Streamlit page and charts |
| `tests/` | Daniel | Carlos | Test days, expected answers, results table |
| `docs/` | PercyAbs (integration), Precious (presentation) | Everyone | Decision log, handover formats, slides |

## Working rules

1. Work only in your own folder, on your own branch (e.g. `carlos/fetch`). PercyAbs merges into `main`.
2. Not comfortable with git? Upload files through the GitHub website into your folder.
3. Never commit API keys or passwords. Put them in a `.env` file (already ignored). Copy `.env.example`.
4. Do not change the columns of `data/sample/sample_summary.csv` or the fields of
   `data/sample/sample_result.json` without telling PercyAbs. Everyone's work depends on them.
5. Any decision goes in `docs/decision_log.md` with the date and the reason.

## Timeline

| By | Target |
| --- | --- |
| 24 Nov 2026 | Fetch works for London; summary columns agreed; first draft of four agent instructions |
| 1 Dec 2026 | One full run from fetch to action works, even if rough; page works on sample files; 10 test days written |
| 8 Dec 2026 | Review step, page and test results done. No new features after this |
| 14 Dec 2026 | Slides, video (under 10 min) and two rehearsals done |
| 21 Jan 2027, 16:00 | Turnitin submission (to confirm) |

## Setup

```
git clone <repo url>
cd air-quality-agent
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # then fill in any keys
```

## Out of scope

Forecasting, extra datasets beyond the four sources, logins, public hosting, follow-up chat.
