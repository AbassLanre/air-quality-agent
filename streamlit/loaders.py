import pandas as pd

from config import SUMMARY_URL


def load_summary():
    return pd.read_csv(SUMMARY_URL)