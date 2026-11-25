# Data limitations (Carlos, Role 1)

- Coverage: 8 fixed London Air sites (4 roadside, 4 background), chosen because each had data
  for at least 80% of hours over the past year. Not every borough is represented.
- Missing data: a site's day only counts with at least 18 of 24 hourly values. Sites drop out
  on some days (e.g. 20 Nov 2026: NO2 at KC1 and TH4); this is shown in `sites_missing`.
- Recent readings are provisional: London Air figures for recent days may be revised later.
- Weather is modelled: Open-Meteo gives modelled weather for one point in central London, not
  measurements at each monitoring site.
- Short history: links are calculated over one year (365 days). Another year could give
  different values, and seasonal patterns can dominate.
- Links are correlations: they show that two things move together, not that one causes the other.
- The official index (`daqi_max`) covers all London Air sites, not only our 8-site panel.
- Traffic is TfL's disruption status for 24 main London roads (not vehicle counts, and not the streets next to each monitor). Most hours show no delays, so the signal sits in the bad hours.
- Traffic history only starts when polling started, and only 12 hours a day are polled (more often in rush hours). Hours not polled are blank.
- Before 8 Dec there will not be enough traffic history (30 days) for a traffic link in summary.csv.
- Boundary layer height is modelled for one point in central London, not measured.
- Hourly values may be one hour out if the providers' timestamp conventions differ (not yet checked).