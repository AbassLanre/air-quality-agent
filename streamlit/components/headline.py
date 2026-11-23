import pandas as pd
import streamlit as st


def index_text(value):
    if pd.isna(value):
        return "Official index: not published"
    value = int(value)
    if value <= 3:
        band = "Low"
    elif value <= 6:
        band = "Moderate"
    elif value <= 9:
        band = "High"
    else:
        band = "Very high"
    return f"Official index: {value} ({band})"


def show_headline(summary):
    st.subheader("Summary for " + str(summary["date"].iloc[0]))

    columns = st.columns(4)
    for col, (_, row) in zip(columns, summary.iterrows()):
        col.metric(row["pollutant"], f"{row['avg_ugm3']} µg/m³")
        col.write(f"Worse than {row['today_percentile']}% of days this year")
        col.write(index_text(row["daqi_max"]))