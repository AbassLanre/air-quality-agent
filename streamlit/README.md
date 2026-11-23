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

## Data to read

Read the same files the agents read, straight from GitHub, so the page and the agent always show
the same day. GitHub Actions refreshes them every morning at 06:00 UTC.

| File | Address | Contents |
| --- | --- | --- |
| Summary | https://raw.githubusercontent.com/abasslanre/air-quality-agent/main/data/latest/summary.csv | Yesterday, one row per pollutant (NO2, PM2.5, PM10, O3) |
| Report | https://raw.githubusercontent.com/abasslanre/air-quality-agent/main/data/latest/summary_report.txt | Missing sites, whether the official index is published |
| History | https://raw.githubusercontent.com/abasslanre/air-quality-agent/main/data/latest/daily.csv (available after the next daily run) | Every day of the past year, for charts |

Column meanings are at the top of `data/summarise.py`. Use `pd.read_csv(url)`; no key needed.
Cache with `@st.cache_data(ttl=3600)` so the page does not re-download on every click.

## What to build

1. **Headline panel**: for each pollutant, yesterday's average, the percentile
   ("worse than 81% of days this year", from `today_percentile`) and the official index (`daqi_max`).
   State the date clearly; never call it live.
2. **Trend charts** (Plotly): the last 30 to 90 days per pollutant from `daily.csv`.
3. **Weather link charts**: each pollutant against wind speed (and rain, mixing height), with the
   link figure (`link_wind` etc.) shown beside it. Label it "linked to", not "caused by".
4. **Typical daily pattern**: highlight `typical_peak_hour`.
5. **Data issues**: missing sites from the report.
6. **"Ask the agent" link** to the published Copilot Studio agent.
7. **Saved-results mode** (demo backup): a few agent answers saved as JSON in `data/results/`,
   in the shape of `data/sample/sample_result.json`, shown in a tab. The demo still works if the
   internet or the agent fails.

## Optional: the agent inside the page

Copilot Studio's Channels tab may offer a website embed code. If the school account allows it, the
agent's chat can sit in a Streamlit tab (`st.components.v1.html`), giving one screen for
everything. PercyAbs is checking this; do not depend on it.

## Hosting

Free on Streamlit Community Cloud, connected to this public repo, main file `streamlit/app.py`.
It then refreshes with each morning's data without anyone touching it.

Run locally (with the venv active):

```
streamlit run streamlit/app.py
```

## Demo flow

1. Streamlit: "Yesterday NO2 was worse than 81% of days this year, and wind was low."
2. Copilot: ask the agent. It rates the day, fetches the forecast because it is bad, gets its
   explanation checked, and gives an action.
3. On a Serious day, the alert draft arrives in Teams for approval; approve it live.
4. Back to Streamlit: the figures the agent quoted are on the page.

## Done when

Someone who has never seen the project can open the page and understand yesterday's air quality
without help, and every figure on it matches `data/latest/summary.csv`.
