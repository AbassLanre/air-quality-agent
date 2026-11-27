# Instruction changes log

| Date | Agent | What changed | Why (which test failed) | By |
| --- | --- | --- | --- | --- |
| 2026-11-23 | Analyst | Bullet 2 template states direction (lower/higher) from the link sign; link_temp excluded from bullet 2; fallback to sites_missing count when no site list; date taken from the date column; mixing_height_m; removed rounding note and stray line; added opening code fence | Review found "higher NO2 is linked to wind" hides direction, and the report tool was failing so site codes may be missing | PercyAbs |
| 2026-11-27 | Coordinator | Rates yesterday (measured), today and tomorrow (forecast); always calls the new GetAirQualityForecast tool; weather tool removed; alerts only when today or tomorrow is forecast Serious, titled "Forecast:"; new answer format with three day lines | Project moved from reporting to forecasting (decision log 27 Nov) | PercyAbs |
| 2026-11-27 | Analyst | Receives the forecast table; bullet 3 is the forecast row with the highest predicted_percentile, with typical error, "is forecast at" never "will be"; optional forecast-weather bullet; 3 to 5 bullets | Same | PercyAbs |
| 2026-11-27 | Reviewer | Forecast figures checked against the forecast row by target_date; FORECAST rule extended (certainty wording, missing error, notes); ORDER covers bullet 3; FORMAT allows 5 bullets; fixed the "- - SEASONAL" typo | Same | PercyAbs |
| 2026-11-27 | Advisor (brief) | Action aimed at the worst forecast day; confidence rule suggested | Same | PercyAbs |
