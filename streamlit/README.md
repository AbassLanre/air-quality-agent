# streamlit/ (Ade)

The page shows the **data**; the Copilot Studio agent shows the **thinking**. Streamlit is the
evidence wall: what actually happened. The agents read the same numbers and decide what they mean
and what to do. In the demo the two sit side by side, so markers can see the agent's claims match
real data.

| | Copilot Studio agent | Streamlit page |
| --- | --- | --- |
| Shows | Decisions, review loop, action, alert | Charts, trends, yesterday against the past year |
| Answers | "What does it mean and what should we do?" | "What actually happened?" |
| Updates | When someone asks the agent | Every morning, automatically |

The page is **read-only**. It never fetches air data, calculates anything new, or calls the agents.
It downloads the same files the agents read and draws them.

---

## Run the page

You need Python 3.11 or newer and Git. These steps are for Windows using Git Bash. Run all
commands from the **repo root** (the `air-quality-agent` folder), not from inside `streamlit/`.
The root matters because `.streamlit/config.toml` (the page theme) is read from where you start
Streamlit.

**1. Create the virtual environment (first time only).**

```
python -m venv ~/aqenv
```

The environment is deliberately made in a short location (`C:\Users\<you>\aqenv`). If the repo
sits in a folder with a long name, installing Streamlit inside the repo fails with a Windows
"path not found" error, because some of its files have very long paths.

**2. Switch it on (every time you open a new terminal).**

```
source ~/aqenv/Scripts/activate
```

You should see `(aqenv)` at the start of the line. Use forward slashes in Git Bash.
(In Command Prompt it is `%USERPROFILE%\aqenv\Scripts\activate`. On Mac or Linux it is
`source ~/aqenv/bin/activate`.)

**3. Install the libraries (first time only).**

```
pip install streamlit pandas plotly requests
```

**4. Start the page.**

```
streamlit run streamlit/app.py
```

A browser tab opens at http://localhost:8501. If Streamlit asks for an email, press Enter to skip.
Leave the terminal running. The page refreshes when you save a file. To stop it, click in the
terminal and press **Ctrl+C**.

---

## Data the page reads

The page reads the same files the agents read, straight from GitHub, so both always show the same
day. GitHub Actions refreshes them every morning at 06:00 UTC. No key is needed.

| File | Address | Used for |
| --- | --- | --- |
| Summary | `https://raw.githubusercontent.com/abasslanre/air-quality-agent/main/data/latest/summary.csv` | Yesterday, one row per pollutant |
| Report | `https://raw.githubusercontent.com/abasslanre/air-quality-agent/main/data/latest/summary_report.txt` | When the report was made, and which sites are missing |
| History | `https://raw.githubusercontent.com/abasslanre/air-quality-agent/main/data/latest/daily.csv` | Trend charts (not published yet) |

Column meanings are at the top of `data/summarise.py`. Downloads are remembered for one hour
(`@st.cache_data(ttl=3600)`), so the page does not re-download on every click.

---

## What is built

Last updated: 23 Nov 2026.

| Spec item | Status |
| --- | --- |
| Headline panel: yesterday's average, percentile, official index with colour badge, date, never "live" | Done |
| Yesterday's weather (wind, rain, temperature, mixing height) | Done |
| Weather link chart (each pollutant against wind, rain, temperature, mixing height), worded "linked to", not "caused by" | Done |
| Typical daily pattern: usual peak hour against yesterday's peak hour | Done |
| Data issues: missing monitoring sites by name, and whether the official index was published | Done |
| Friendly message and "Try again" button if the data cannot be loaded | Done |
| Mobile layout (cards stack, charts fit the screen) | Done, checked at phone width |
| "Ask the agent" button | Built, waiting for the published agent link |
| Saved-results tab (demo backup from `data/results/`) | Not started, waiting for `data/sample/sample_result.json` |
| Trend charts, last 30 to 90 days | Not started, waiting for `daily.csv` to be published |
| Scatter charts (pollutant against wind, rain, mixing height) | Not started, waiting for `daily.csv` |
| Hosting on Streamlit Community Cloud | Not started, needs the branch merged into `main` |

Every figure on the page matches `data/latest/summary.csv`. The collapsed "Source data" box at the
bottom of the page shows the exact rows for checking.

---

## How the code is organised

Each section of the page is its own small file, so one can be changed, added or removed without
touching the others.

```
streamlit/
├── app.py                  Builds the page. Loads the data, then calls each section in order.
├── config.py               Web addresses, colours and the agent link. Change settings here.
├── loaders.py              Downloads and reads the files, and handles download failures.
└── components/
    ├── __init__.py         Empty file that marks this folder as a package.
    ├── ask_agent.py        "Ask the agent" box.
    ├── badge.py            Coloured official-index label (UK DAQI colours).
    ├── headline.py         The four pollutant cards.
    ├── weather_strip.py    Yesterday's weather tiles.
    ├── weather_links.py    Weather link bar chart.
    ├── daily_pattern.py    Usual peak against yesterday's peak chart.
    └── data_issues.py      Missing-site warnings.
.streamlit/
└── config.toml             Page theme (in the repo root, outside this folder).
```

### Add a new section

1. Create `components/my_section.py` with a function such as `show_my_section(summary)`.
2. In `app.py`, import it and add one call in the order you want it on the page.

### Change a setting

- **Agent link:** paste the published Copilot Studio link into `AGENT_URL` in `config.py`. The
  greyed-out button becomes a working one.
- **Pollutant colours:** edit `POLLUTANT_COLOURS` in `config.py`. They apply to every chart.
- **Index colours:** edit `DAQI_COLOURS` in `config.py`.
- **Data addresses:** edit `BASE_URL` in `config.py`.

---

## Testing the error message

1. In `config.py`, change `summary.csv` in the address to `summaryXX.csv` and save.
2. Stop Streamlit (Ctrl+C) and start it again, because a restart clears the remembered data.
3. The page should show a red message and a "Try again" button, and nothing else.
4. Change the address back and click **Try again**.

---

## Demo flow

1. Streamlit: "Yesterday NO2 was worse than 81% of days this year, and wind was low."
2. Copilot: ask the agent. It rates the day, fetches the forecast because it is bad, gets its
   explanation checked, and gives an action.
3. On a Serious day, the alert draft arrives in Teams for approval; approve it live.
4. Back to Streamlit: the figures the agent quoted are on the page.

---

## Done when

Someone who has never seen the project can open the page and understand yesterday's air quality
without help, and every figure on it matches `data/latest/summary.csv`.

## Working rules

- Work on branch `ade/page` and only change files in `streamlit/` (plus `.streamlit/config.toml`).
- Do not rename the columns of `data/sample/sample_summary.csv` or the fields of
  `data/sample/sample_result.json`.
- Never commit keys or passwords.
- Any decision goes in `docs/decision_log.md` with the date and the reason.