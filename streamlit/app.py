import streamlit as st

from loaders import load_summary
from components.headline import show_headline
from components.weather_links import show_weather_links
from components.daily_pattern import show_daily_pattern

st.title("London air quality")

summary = load_summary()
st.dataframe(summary)

show_headline(summary)
show_weather_links(summary)
show_daily_pattern(summary)