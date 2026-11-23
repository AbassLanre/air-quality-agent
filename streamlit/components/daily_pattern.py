import streamlit as st


def hour_text(hour):
    return f"{int(hour):02d}:00"


def show_daily_pattern(summary):
    st.subheader("When pollution usually peaks")
    st.write(
        "The usual peak hour over the past year, next to the hour "
        "yesterday's peak actually happened."
    )

    table = summary[["pollutant", "typical_peak_hour", "peak_hour"]].copy()
    table["typical_peak_hour"] = table["typical_peak_hour"].apply(hour_text)
    table["peak_hour"] = table["peak_hour"].apply(hour_text)
    table = table.rename(
        columns={
            "pollutant": "Pollutant",
            "typical_peak_hour": "Usual peak",
            "peak_hour": "Yesterday's peak",
        }
    )
    st.dataframe(table, hide_index=True)