import pandas as pd

from config import DAQI_COLOURS


def band_name(value):
    if value <= 3:
        return "Low"
    if value <= 6:
        return "Moderate"
    if value <= 9:
        return "High"
    return "Very high"


def index_badge(value):
    """Return a small coloured label as HTML for the official index."""
    if pd.isna(value):
        background, text_colour = "#E3E7EB", "#1B2733"
        label = "Index not published"
    else:
        value = int(value)
        background = DAQI_COLOURS.get(value, "#E3E7EB")
        text_colour = "#FFFFFF" if value >= 8 else "#1B2733"
        label = f"Index {value} · {band_name(value)}"

    return (
        f"<span style='background:{background};color:{text_colour};"
        f"padding:4px 12px;border-radius:999px;font-weight:600;"
        f"font-size:0.85rem;display:inline-block'>{label}</span>"
    )