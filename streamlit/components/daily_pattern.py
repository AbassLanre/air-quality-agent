import plotly.graph_objects as go
import streamlit as st

from config import POLLUTANT_COLOURS

NEUTRAL = "#5B6770"


def hour_text(hour):
    return f"{int(hour):02d}:00"


def show_daily_pattern(summary):
    st.subheader("When pollution usually peaks")
    st.write(
        "The hollow dot is the hour pollution usually peaks over the past year. "
        "The filled dot is the hour yesterday's peak actually happened."
    )

    pollutants = summary["pollutant"]
    usual = summary["typical_peak_hour"]
    yesterday = summary["peak_hour"]
    colours = [POLLUTANT_COLOURS.get(p, NEUTRAL) for p in pollutants]

    fig = go.Figure()

    # Usual peak: hollow dots, coloured by pollutant
    fig.add_trace(
        go.Scatter(
            x=usual,
            y=pollutants,
            mode="markers",
            showlegend=False,
            marker=dict(
                size=18,
                symbol="circle-open",
                color=colours,
                line=dict(width=3),
            ),
            customdata=[hour_text(h) for h in usual],
            hovertemplate="%{y}<br>Usual peak: %{customdata}<extra></extra>",
        )
    )

    # Yesterday's peak: filled dots, coloured by pollutant
    fig.add_trace(
        go.Scatter(
            x=yesterday,
            y=pollutants,
            mode="markers",
            showlegend=False,
            marker=dict(size=11, color=colours),
            customdata=[hour_text(h) for h in yesterday],
            hovertemplate="%{y}<br>Yesterday's peak: %{customdata}<extra></extra>",
        )
    )

    # Two grey dummy traces, only so the legend explains hollow vs filled
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            name="Usual peak",
            marker=dict(
                size=14, symbol="circle-open", color=NEUTRAL, line=dict(width=3)
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            name="Yesterday's peak",
            marker=dict(size=10, color=NEUTRAL),
        )
    )

    fig.update_xaxes(
        range=[-0.5, 23.5],
        tickvals=[0, 4, 8, 12, 16, 20],
        ticktext=[hour_text(h) for h in [0, 4, 8, 12, 16, 20]],
        showgrid=True,
        gridcolor="#E3E7EB",
    )
    fig.update_yaxes(autorange="reversed", title="")
    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig)

    st.caption(
        "The day runs from 00:00 to 23:00, and the hours loop around midnight, "
        "so 22:00 and 00:00 are only two hours apart."
    )

    with st.expander("See the exact hours"):
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
