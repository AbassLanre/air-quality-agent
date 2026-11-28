# Send Air Quality Alert (agent flow, owner: PercyAbs)

The coordinator calls this only during the scheduled **DAILY CHECK** (Recurrence trigger, 07:30 UTC), and only when today or tomorrow is **forecast** Serious (an early warning). Chat questions never call it, so the approver gets at most one alert a day. A person must approve before any email goes out.
Based on Microsoft Learn: "Request information from human review in agent flows" and "Agent flows
overview". Screen names may differ slightly in the school's Copilot Studio.

## Flow steps

| # | Step | Settings |
| --- | --- | --- |
| 1 | Trigger: **When an agent calls the flow** | Text inputs: `AlertTitle`, `AlertMessage`, `Seriousness` (no spaces in names) |
| 2 | **Respond to the agent** | Output `Status` = "Sent to a person for approval". Placed here so the chat does not wait for the approver |
| 3 | **Request for information** (under Human review) | Title: `AlertTitle`. Message: `AlertMessage`. Assigned to: PercyAbs's university email. Inputs: `Approve` (Yes/No), `ReviewerNote` (Text, optional) |
| 4 | **Condition**: `Approve` is equal to true | |
| 5 | If yes: **Send an email (V2)** (Office 365 Outlook) | To: team emails only. Subject: `AlertTitle`. Body: `AlertMessage` plus "Approved by a person. This is a forecast, not a measurement, and may be wrong." |
| 6 | If no: nothing is sent | |

## Rules

- Recipients are team members only, inside the university tenant. Never real external contacts.
- The approval email comes through Outlook (the "Request for information" action is Outlook only).
- Test runs in the designer or the test chat do not use Copilot Credits; real runs do.

## Tests

| Test | Expected |
| --- | --- |
| Call the flow from the designer with a sample title and message, approve it | Approval email arrives, then the alert email to the team |
| Same, but reject it | Approval email arrives; no alert email |
| Forecast with today and tomorrow both Elevated or Normal (even if yesterday was Serious) | Agent does not call the flow; "Alert: not needed" |
| Forecast with a Serious day (use `data/sample/sample_forecast.csv`: NO2 on 2026-11-28, predicted_percentile 92) | Agent calls the flow with a title starting "Forecast:", replies "Sent to a person for approval" |
| Forecast tool fails | No alert; "Forecast unavailable" under Data issues |
| Ordinary chat question on a day forecast Serious | No flow call; Alert line says early warnings are sent by the daily check |
| "Test trigger" on the Recurrence trigger (or type a message starting "DAILY CHECK") with a Serious forecast | Flow called once; approval email arrives |
