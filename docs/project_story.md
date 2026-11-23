# Project story (for the pitch and the reports)

## The problem

London publishes hourly air quality readings from dozens of monitoring sites, and weather data is
freely available. But the numbers alone do not tell a council officer or a school what to do.
Someone has to work out how bad a day was, why, whether it will continue, and who needs to know.
That takes time and expertise, so most days nobody does it.

## Our solution

A team of AI agents that does that job every morning and only involves a person when it matters.

1. **Reliable numbers (code).** Every morning at 06:00 UTC, GitHub Actions runs our Python. It
   downloads a year of hourly readings from 8 reliable London Air monitoring sites and Open-Meteo
   weather, cleans them, and calculates yesterday's summary: levels, peaks, how yesterday ranks
   against the past year, and how strongly each pollutant is linked to wind, rain, temperature
   and mixing height. Code does every calculation, so the numbers are the same every time.
2. **Judgement (agents).** In Copilot Studio, the Coordinator reads the summary and decides how
   serious the day is (Serious, Elevated or Normal). On bad days it chooses to fetch tomorrow's
   weather forecast; on normal days it does not bother.
3. **Explanation and self-checking.** The Analyst explains what the pollution is linked to. The
   Reviewer checks every claim against the numbers and sends unsupported claims back, at most
   twice. Only approved findings go forward.
4. **Action.** The Advisor turns the findings into one clear action. On Serious days the
   Coordinator drafts an alert and sends it for a person to approve before it goes out by Teams
   or email.

## Why it is agentic, not a dashboard

- It has a goal, not a script: "work out how serious it is and whether anyone needs telling".
- It decides which tools to use: the forecast only when the day is bad or someone asks.
- It checks itself: the Reviewer can reject the Analyst's work.
- It acts: it drafts and routes alerts, with a human approving.
- It explains every decision it made, so the user can see why.

## Responsible design

- Code calculates, agents interpret; agents may not invent or change numbers.
- "Linked to", never "caused by": the links are correlations.
- The data is yesterday's, and forecasts are labelled as forecasts; nothing is called live.
- No alert reaches anyone without a person approving it, and alerts only go out on Serious days.
- Limitations are recorded in `data/limitations.md` (8 sites, modelled weather, provisional
  readings, seasonal effects in year-long links).

## One-line pitch

The code makes the numbers reliable; the agents decide what the numbers mean and what to do
about them.
