# data/sample/ (agreed handover files)

- `sample_summary.csv`: real output of `python data/summarise.py` for 20 Nov 2026, in exactly the
  shape the daily run publishes to `data/latest/summary.csv`. The agents, the Streamlit page and the
  tests build against it. NO2 that day was at the 91st percentile, so it is a useful "Serious day"
  test case.
- `sample_forecast.csv`: the agreed shape of the daily forecast (`data/latest/forecast.csv`, made by
  `data/forecast.py`). The numbers are **invented** so the agents and the page can be built before
  the model exists. Tomorrow's NO2 is set to Serious on purpose, to test the early-warning alert.
- `sample_result.json`: example of what the agents hand to the Streamlit page (invented), matching
  the two samples above: yesterday measured, today and tomorrow forecast, and a Reviewer loop
  that rejects a forecast stated as certain.

Changing a column means telling PercyAbs first, because the agents and the page both read these names.

## sample_summary.csv columns

One row per pollutant (NO2, PM2.5, PM10, O3) for one day. All times are GMT. Every number comes
from code; the agents never calculate.

| Column | Meaning | Unit |
| --- | --- | --- |
| city | City name (London) | |
| date | Day the data covers, usually yesterday | YYYY-MM-DD |
| pollutant | NO2, PM2.5, PM10 or O3 | |
| avg_ugm3 | Average of the panel sites that had a full day (at least 18 of 24 hourly values) | µg/m³ |
| peak_ugm3 | Highest single hourly value at any panel site that day | µg/m³ |
| peak_hour | Hour of that peak | 0 to 23 |
| sites_reporting | Panel sites with a full day of data for this pollutant | count |
| sites_missing | Panel sites without a full day of data for this pollutant | count |
| wind_avg_kmh | Mean wind speed, central London (Open-Meteo) | km/h |
| rain_total_mm | Total rain that day | mm |
| temp_avg_c | Mean temperature | °C |
| mixing_height_m | Mean mixing height: how deep the air layer is that pollution can spread into | m |
| link_wind | Spearman correlation between the daily pollutant average and daily wind, over the 365 days up to this date. Negative = more wind, less pollution | -1 to 1 |
| link_rain | Same, with daily rain | -1 to 1 |
| link_temp | Same, with daily mean temperature. Over a year this mostly reflects the seasons | -1 to 1 |
| link_mixing | Same, with daily mixing height | -1 to 1 |
| typical_peak_hour | Hour of day with the highest average over the same 365 days | 0 to 23 |
| weekday_vs_weekend_pct | How much higher (+) or lower (-) the average is on weekdays (Mon to Fri) than at weekends, over the same 365 days | % |
| today_percentile | % of the past 365 days with an average at or below this day's average. 91 = worse than 91% of days | 0 to 100 |
| daqi_max | Highest official Daily Air Quality Index for this pollutant across all London Air sites that day. Blank if not published yet | 1 to 10 |
| window_days | Days of history behind the link figures | count |

Links are correlations: they show that two things move together, not that one causes the other.
See `data/limitations.md`.

## sample_forecast.csv columns

One row per pollutant (NO2, PM2.5, PM10, O3) and forecast day: 8 rows. Every number comes from
`data/forecast.py`; the agents never calculate or predict.

| Column | Meaning | Unit |
| --- | --- | --- |
| city | City name (London) | |
| made_on | Day the forecast was made (the morning run) | YYYY-MM-DD |
| based_on_date | Last full day of measured data, usually yesterday; the same as `date` in summary.csv | YYYY-MM-DD |
| target_date | Day being forecast | YYYY-MM-DD |
| lead_days | Days after based_on_date: 1 = today, 2 = tomorrow | 1 or 2 |
| pollutant | NO2, PM2.5, PM10 or O3 | |
| predicted_ugm3 | Forecast daily average across the panel sites | µg/m³ |
| typical_error_ugm3 | Our model's average miss in the backtest (mean absolute error) for this pollutant and lead | µg/m³ |
| persistence_error_ugm3 | Average miss of the simple guess "same as the last measured day", for comparison. Lower typical_error_ugm3 = our model does better | µg/m³ |
| predicted_percentile | % of the past 365 days with an average at or below predicted_ugm3. Same idea as today_percentile | 0 to 100 |
| likely_level | Serious (predicted_percentile 90 or more), Elevated (75 to 89), Normal (below 75). Set by code with the same thresholds the Coordinator uses | |
| forecast_wind_kmh | Open-Meteo forecast mean wind, central London, that day | km/h |
| forecast_rain_mm | Forecast total rain that day | mm |
| forecast_temp_c | Forecast mean temperature | °C |
| forecast_mixing_height_m | Forecast mean mixing height (boundary layer height) | m |
| note | Anything the agents must mention, e.g. "no measured data for 2026-11-26, forecast less reliable". Blank if nothing | |

A forecast is a prediction, not a measurement. The model is trained on the weather that actually
happened but runs on forecast weather, so live errors may be larger than typical_error_ugm3.
