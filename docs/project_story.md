# Project story (for the pitch and the reports)

## The problem

London publishes hourly air quality readings from dozens of monitoring sites, and weather data is
freely available. But the numbers only say what has already happened. By the time anyone looks,
a bad air day is over and the people it affects (children walking to school, people with
breathing problems, outdoor workers) found out too late. A council officer or a school needs to
know **before** the day: will the air be bad, why, and what should we do? Working that out takes
time and expertise, so most days nobody does it.

## Our solution

A team of AI agents that looks ahead every morning, warns about bad air days before they happen,
and only involves a person when it matters.

1. **Reliable numbers (code).** At 06:00 and 12:00 UTC every day, GitHub Actions runs our Python. It
   downloads a year of hourly readings from 8 reliable London Air monitoring sites and Open-Meteo
   weather (including how deep the air layer is that pollution can spread into), cleans them, and
   calculates yesterday's summary: levels, peaks, how yesterday ranks against the past year, and
   how strongly each pollutant is linked to wind, rain, temperature and mixing height.
2. **The forecast (code).** The same run trains a simple model on the past year, takes the
   weather forecast for today and tomorrow, and predicts each pollutant's level for both days,
   how it would rank against the past year, and how far off the model typically is. Code does
   every calculation, so the numbers are the same every time and can be checked.
3. **Judgement (agents).** In Copilot Studio, the Coordinator reads yesterday's summary and the
   forecast and rates yesterday, today and tomorrow as Serious, Elevated or Normal, stating the
   figure that decided it.
4. **Explanation and self-checking.** The Analyst explains what the pollution is linked to and
   why the forecast looks the way it does (for example low wind and a shallow mixing layer). The
   Reviewer checks every claim against the numbers, makes sure forecasts are labelled as
   forecasts with their typical error, and sends unsupported claims back, at most twice.
5. **Action.** The Advisor turns the findings into one clear action. Every day at 07:30 UTC a
   Copilot Studio Recurrence trigger starts the Coordinator by itself, with nobody asking. If
   today or tomorrow is forecast Serious, it drafts an early warning and sends it for a person to
   approve before it goes out by email. Anyone can also ask the agent at any time.

## How we know the forecast is worth using

We test it on the past: for each of the last 90 days we pretend it is that morning, predict the
day using only earlier data, and compare with what actually happened. The model has to beat the
simplest possible guess, "tomorrow will be the same as today". We also compare it with CAMS, the
professional European air quality forecast, over the days we have collected it. The results,
good or bad, are reported in `docs/forecast_evaluation.md`.

## Why it is agentic, not a dashboard

- It has a goal, not a script: "work out whether the air will be bad and whether anyone needs
  warning".
- It decides: it weighs the measured past against the forecast and chooses whether to alert.
- It checks itself: the Reviewer can reject the Analyst's work, including overconfident forecasts.
- It acts ahead of time: it drafts and routes early warnings, with a human approving.
- It explains every decision it made, so the user can see why.

## Responsible design

- Code calculates, agents interpret; agents may not invent, predict or change numbers.
- "Linked to", never "caused by": the links are correlations.
- A forecast is always called a forecast and comes with its typical error; it is never stated
  as certain.
- The forecast looks at most 2 days ahead, because weather forecasts get much less reliable
  after that.
- No alert reaches anyone without a person approving it, and alerts only go out on Serious days.
- Limitations are recorded in `data/limitations.md` (8 sites, modelled weather, provisional
  readings, seasonal effects in year-long links, forecast trained on actual weather but run on
  forecast weather).

## One-line pitch

Our agents warn London about bad air days before they happen, and explain why. The code makes
the numbers reliable; the agents decide what they mean and what to do about them.
