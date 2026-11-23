import plotly.express as px
import streamlit as st

FACTORS = {
    "link_wind": "Wind speed",
    "link_rain": "Rain",
    "link_temp": "Temperature",
    "link_mixing": "Mixing height",
}


def show_weather_links(summary):
    st.subheader("What the weather is linked to")
    st.write(
        "Each bar shows how closely a weather factor moves with a pollutant "
        "over the past year, from -1 to +1. Below zero means higher values of "
        "that factor go with lower pollution. These are links, not causes."
    )

    links = summary.melt(
        id_vars="pollutant",
        value_vars=list(FACTORS),
        var_name="factor",
        value_name="link",
    )
    links["factor"] = links["factor"].map(FACTORS)

    fig = px.bar(
        links,
        x="factor",
        y="link",
        color="pollutant",
        barmode="group",
        labels={"link": "Link (-1 to +1)", "factor": "", "pollutant": "Pollutant"},
    )
    fig.update_yaxes(range=[-1, 1])
    st.plotly_chart(fig, use_container_width=True)