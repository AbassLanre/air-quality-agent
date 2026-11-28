# streamlit/ (Ade)

The page shows the **data**; the Copilot Studio agent shows the **thinking**. Streamlit is the
evidence wall: what actually happened. The agents read the same numbers and decide what they mean
and what to do. In the demo the two sit side by side, so markers can see the agent's claims match
real data.

| | Copilot Studio agent | Streamlit page |
| --- | --- | --- |
| Shows | Decisions, review loop, action, early warning | Charts, trends, the forecast and how accurate it has been |
| Answers | "What does it mean and what should we do?" | "What happened, and what is forecast?" |
| Updates | When someone asks the agent | Every morning, automatically |

## Data to read

Read the same files the agents read, straight from GitHub, so the page and the agent always show
the same day. GitHub Actions refreshes them at 06:00 and 12:00 UTC.

| File | Address | Contents |
| --- | --- | --- |
| Summary | https://raw.githubusercontent.com/abasslanre/air-quality-agent/main/data/latest/summary.csv | Yesterday, one row per pollutant (NO2, PM2.5, PM10, O3) |
| Report | https://raw.githubusercontent.com/abasslanre/air-quality-agent/main/data/latest/summary_report.txt | Missing sites, whether the official index is published |
| History | https://raw.githubusercontent.com/abasslanre/air-quality-agent/main/data/latest/daily.csv | Every day of the past year, for charts |
| Forecast | https://raw.githubusercontent.com/abasslanre/air-quality-agent/main/data/latest/forecast.csv (once `forecast.py` runs; until then build against `data/sample/sample_forecast.csv`) | Today and tomorrow, one row per pollutant and day |

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
6. **Forecast panel**: cards for today and tomorrow coloured by `likely_level`, and a chart of the
   last 14 days measured followed by today and tomorrow predicted (dashed), with
   `typical_error_ugm3` as a shaded band. Label it "forecast", never "will be".
7. **How good is the forecast?**: model error vs the simple guess (`typical_error_ugm3` vs
   `persistence_error_ugm3`), and later the chart from `docs/forecast_evaluation.md`.
8. **"Ask the agent" link** to the published Copilot Studio agent.
9. **Saved-results mode** (demo backup): a few agent answers saved as JSON in `data/results/`,
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

1. Streamlit: yesterday's levels and the forecast cards ("tomorrow NO2 forecast Serious").
2. Copilot: "Is tomorrow going to be bad?" It rates yesterday, today and tomorrow, gets its
   explanation checked, and gives an action for the bad day.
3. Tomorrow is forecast Serious, so the early-warning draft arrives by Outlook for approval;
   approve it live.
4. Back to Streamlit: the figures the agent quoted are on the page, and the accuracy chart shows
   how far to trust the forecast.

## Done when

Someone who has never seen the project can open the page and understand yesterday's air quality
and the forecast without help, and every figure on it matches `data/latest/summary.csv` and
`data/latest/forecast.csv`.
