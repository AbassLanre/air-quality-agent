# streamlit/ (Ade)

The page the audience sees. Start now using the files in `data/sample/`; real data comes later.

## To build

- `app.py`: choose a city or site and see today's air quality.
- Plotly charts: pollutant levels over the day, and each pollutant against wind and the other factors.
- Show the agents' steps in order, from `sample_result.json` `steps`, including any claim the Reviewer sent back.
- Show the Advisor's `action` at the top with its `supporting_figures`.
- Saved-results mode so the live demo works if the internet or the model fails.

Run with `streamlit run streamlit/app.py`.

## Done when

Someone who has never seen the project can open the page and understand today's result without help.
