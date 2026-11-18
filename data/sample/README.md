# data/sample/ (agreed handover files)

These files are INVENTED example data. Everyone builds against them until the real pipeline works.

- `sample_summary.csv`: what Carlos's code produces each day. Read by the agents and the Streamlit page.
- `sample_result.json`: what the agents hand to the Streamlit page.

## sample_summary.csv columns

| Column | Meaning | Unit |
| --- | --- | --- |
| city | City name | |
| date | Day the data covers | YYYY-MM-DD |
| pollutant | NO2, PM2.5, PM10 or O3 | |
| avg_ugm3 | Daily average across reporting sites | µg/m³ |
| peak_ugm3 | Highest hourly value | µg/m³ |
| peak_hour | Hour of the peak | 0 to 23 |
| sites_reporting | Sites with data that day | count |
| sites_missing | Sites with no data | count |
| wind_avg_kmh | Average wind speed | km/h |
| rain_total_mm | Total rain | mm |
| temp_avg_c | Average temperature | °C |
| link_wind | Correlation with wind speed, last 30 days | -1 to 1 |
| link_rain | Correlation with rain, last 30 days | -1 to 1 |
| link_temp | Correlation with temperature, last 30 days | -1 to 1 |
| link_hour | Correlation with hour of day, last 30 days | -1 to 1 |
| window_days | Days of history behind the link figures | count |

Changing a column means telling PercyAbs first, because the agents and the page both read these names.
