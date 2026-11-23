import streamlit as st


def show_weather_strip(summary):
    # The weather is the same on every row, so the first row is enough.
    row = summary.iloc[0]

    st.subheader("Weather yesterday")

    tiles = [
        ("Wind", f"{row['wind_avg_kmh']:.0f} km/h"),
        ("Rain", f"{row['rain_total_mm']:.1f} mm"),
        ("Temperature", f"{row['temp_avg_c']:.1f} °C"),
        ("Mixing height", f"{row['mixing_height_m']:.0f} m"),
    ]

    columns = st.columns(4)
    for col, (label, value) in zip(columns, tiles):
        with col.container(border=True):
            st.metric(label, value)

    st.caption(
        "Mixing height is how deep the layer of air is that pollution can "
        "spread through. A low value means pollution stays closer to the ground."
    )