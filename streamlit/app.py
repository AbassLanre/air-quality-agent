import streamlit as st

from loaders import load_summary, load_report, parse_report
from components.ask_agent import show_ask_agent
from components.headline import show_headline
from components.weather_strip import show_weather_strip
from components.weather_links import show_weather_links
from components.daily_pattern import show_daily_pattern
from components.data_issues import show_data_issues

st.set_page_config(
    page_title="London air quality",
    page_icon="🌫️",
    layout="wide",
)

st.title("London air quality")

summary = load_summary()

if summary is None or summary.empty:
    st.error(
        "Couldn't load the latest air quality data. This is usually a "
        "temporary connection problem."
    )
    if st.button("Try again"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

report_info = parse_report(load_report())

show_ask_agent()
show_headline(summary)
show_weather_strip(summary)
show_weather_links(summary)
show_daily_pattern(summary)
show_data_issues(summary, report_info)

with st.expander("Source data (summary.csv)"):
    st.dataframe(summary, hide_index=True)

st.caption("Data refreshed daily at 06:00 UTC. Figures are for the previous day, not live.")