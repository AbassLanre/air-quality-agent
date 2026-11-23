BASE_URL = "https://raw.githubusercontent.com/abasslanre/air-quality-agent/main/data/latest"

SUMMARY_URL = f"{BASE_URL}/summary.csv"
REPORT_URL = f"{BASE_URL}/summary_report.txt"

# Official UK air quality index (DAQI): number -> colour
DAQI_COLOURS = {
    1: "#9CFF9C", 2: "#31FF00", 3: "#31CF00",
    4: "#FFFF00", 5: "#FFCF00", 6: "#FF9A00",
    7: "#FF6464", 8: "#FF0000", 9: "#990000",
    10: "#CE30FF",
}

POLLUTANT_COLOURS = {
    "NO2": "#1F6F78",
    "PM2.5": "#E07A5F",
    "PM10": "#3D5A80",
    "O3": "#B08D57",
}

# Paste the published Copilot Studio agent link here (leave empty until PercyAbs sends it)
AGENT_URL = ""