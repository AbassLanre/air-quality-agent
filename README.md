# City Air Quality Agent

LD7237 Hackathon group project, Northumbria University London (AI Agents Unleashed).

A set of AI agents that warn London about bad air days before they happen, and explain why.
Every morning, code measures yesterday and forecasts today and tomorrow from the past year of air
quality and the weather forecast; the agents judge how serious each day is, check their own
claims, give one clear action and draft an early warning that a person approves.

## How it works

There are two kinds of workers:

- **Code** (Python, in GitHub Actions at 06:00 and 12:00 UTC) fetches, cleans, calculates and forecasts.
  Same job every time, no AI involved. Results are published to `data/latest/`.
- **Agents** (Copilot Studio) read what the code produced through REST tools, judge it, explain
  it, check it and advise. Agents never calculate or predict.

Daily run:

1. **Code**: `summarise.py --fetch` downloads a year of London Air and Open-Meteo data and writes
   yesterday's summary. `forecast.py` predicts each pollutant for today and tomorrow, with how it
   ranks against the past year and the model's typical error.
2. **Coordinator** (started by a Copilot Studio Recurrence trigger at 07:30 UTC, or by anyone
   asking) rates yesterday (measured), today and tomorrow (forecast) as Serious, Elevated or Normal.
3. **Analyst** explains what the pollution is linked to and what the forecast shows.
4. **Reviewer** checks each claim against the numbers and sends unsupported claims back (max twice).
5. **Advisor** turns the reviewed findings into one action for the worst forecast day.
6. In the 07:30 daily check, if today or tomorrow is forecast **Serious**, the Coordinator drafts
   an early warning; a person approves it before it is emailed.
7. The **Streamlit** page shows the measured history, the forecast and how accurate it has been.

Full story: `docs/project_story.md`. Plan to 14 Dec: `docs/next_steps.md`.

## Data sources

| Source | What it gives | Key needed | Status |
| --- | --- | --- | --- |
| [London Air](https://api.erg.ic.ac.uk/AirQuality/Hourly/MonitoringIndex/GroupName=London/Json) | Hourly readings per monitoring site | No | Checked 17 Nov 2026, works |
| [Open-Meteo](https://open-meteo.com/) | Weather history; CAMS air quality forecast (benchmark for our forecast) | No | Checked 17 Nov 2026, works |
| [Open-Meteo forecast](https://open-meteo.com/en/docs) | Weather forecast for today and tomorrow (the forecast's input) | No | Used by the daily run |

Air Quality England and Scottish Air Quality are not used (London only), and TfL traffic was
tried and dropped. See `docs/decision_log.md`.

## Team and folders

| Folder | Owner | Support | Contents |
| --- | --- | --- | --- |
| `data/` | Carlos | Daniel | Fetch, clean, summarise and forecast scripts |
| `data/sample/` | PercyAbs | Everyone | Agreed sample files everyone builds against |
| `agents/` | PercyAbs (build), Precious (instructions) | | Four agent instruction files, Copilot Studio setup notes |
| `streamlit/` | Ade | | The Streamlit page and charts |
| `tests/` | Daniel | Carlos | Forecast backtest, test days, expected answers, results table |
| `docs/` | PercyAbs (integration), Precious (presentation) | Everyone | Decision log, handover formats, slides |

## Working rules

1. Work only in your own folder, on your own branch (e.g. `carlos/fetch`). PercyAbs merges into `main`.
2. Not comfortable with git? Upload files through the GitHub website into your folder.
3. Never commit API keys or passwords. Put them in a `.env` file (already ignored). Copy `.env.example`.
4. Do not change the columns of `data/sample/sample_summary.csv` or `sample_forecast.csv`, or the
   fields of `data/sample/sample_result.json`, without telling PercyAbs. Everyone's work depends on them.
5. Any decision goes in `docs/decision_log.md` with the date and the reason.

## Timeline

| By | Target |
| --- | --- |
| 24 Nov 2026 | Fetch works for London; summary columns agreed; first draft of agent instructions (done) |
| 27 Nov 2026 | Traffic dropped; project moves to forecasting (done) |
| 2 Dec 2026 | `forecast.py` writes a forecast in the agreed shape |
| 4 Dec 2026 | Backtest done (`docs/forecast_evaluation.md`); forecast published daily |
| 6 Dec 2026 | Agents use the forecast in Copilot Studio |
| 9 Dec 2026 | Streamlit forecast page and test results done. No new features after this |
| 14 Dec 2026 | Live presentation; backup video recorded |
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

Forecasts beyond 2 days, cities other than London, extra datasets (traffic, other regional
networks), logins, public alerts to real people, follow-up chat.
