import pandas as pd
import requests
import streamlit as st

from config import REPORT_URL, SUMMARY_URL


@st.cache_data(ttl=3600)
def _fetch_summary():
    return pd.read_csv(SUMMARY_URL)


@st.cache_data(ttl=3600)
def _fetch_report():
    response = requests.get(REPORT_URL, timeout=10)
    response.raise_for_status()
    return response.text


def load_summary():
    """Return the summary table, or None if it can't be loaded."""
    try:
        return _fetch_summary()
    except Exception:
        return None


def load_report():
    """Return the report text, or None if it can't be loaded."""
    try:
        return _fetch_report()
    except Exception:
        return None


def parse_report(text):
    """Pull the made-at time and the missing site codes out of the report text."""
    info = {"made": None, "missing_sites": {}}
    if not text:
        return info

    lines = text.splitlines()

    # First line looks like: Summary for London, 2026-11-22  (made 2026-11-23 12:26)
    if lines and "(made " in lines[0]:
        info["made"] = lines[0].split("(made ", 1)[1].rstrip(") ").strip()

    # Last block looks like:
    #    NO2    BT4, KC1
    #    PM2.5  none
    in_section = False
    for line in lines:
        if line.startswith("Panel sites without a full day"):
            in_section = True
            continue
        if in_section and line.strip():
            parts = line.split(None, 1)
            if len(parts) == 2:
                pollutant, sites = parts
                if sites.strip().lower() == "none":
                    info["missing_sites"][pollutant] = []
                else:
                    info["missing_sites"][pollutant] = [
                        s.strip() for s in sites.split(",") if s.strip()
                    ]

    return info
