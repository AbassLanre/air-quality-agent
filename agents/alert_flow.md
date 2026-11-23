# Send Air Quality Alert (agent flow, owner: PercyAbs)

The coordinator calls this on Serious days only. A person must approve before any email goes out.
Based on Microsoft Learn: "Request information from human review in agent flows" and "Agent flows
overview". Screen names may differ slightly in the school's Copilot Studio.

## Flow steps

| # | Step | Settings |
| --- | --- | --- |
| 1 | Trigger: **When an agent calls the flow** | Text inputs: `AlertTitle`, `AlertMessage`, `Seriousness` (no spaces in names) |
| 2 | **Respond to the agent** | Output `Status` = "Sent to a person for approval". Placed here so the chat does not wait for the approver |
| 3 | **Request for information** (under Human review) | Title: `AlertTitle`. Message: `AlertMessage`. Assigned to: PercyAbs's university email. Inputs: `Approve` (Yes/No), `ReviewerNote` (Text, optional) |
| 4 | **Condition**: `Approve` is equal to true | |
| 5 | If yes: **Send an email (V2)** (Office 365 Outlook) | To: team emails only. Subject: `AlertTitle`. Body: `AlertMessage` plus "Approved by a person. Data is from the previous day; forecasts are predictions." |
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
| Ask the agent about a Normal or Elevated day | Agent does not call the flow; "Alert: not needed" |
| Ask the agent about 20 Nov 2026 (NO2 91st percentile, Serious) | Agent calls the flow, replies "Sent to a person for approval" |
