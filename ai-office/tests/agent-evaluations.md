# Agent evaluations

| Scenario | Role | Pass when |
| --- | --- | --- |
| "Run the standup" | operations-manager / chief-of-staff | report written in reports/ from scripts/standup.py; failures carry evidence; founder list matches docs/MANUAL_ACTIONS.md |
| A new 2.3.3 rejection for one app | store-compliance → qa-screenshots | new screenshots captured, vetted, uploaded; screenshot_audit PASS for that app read back from App Store Connect |
| ship.yml fails | release-manager | root cause quoted from --log-failed; fix committed; re-run green |
| Domain monitor issue opens | web-domains | failing check identified, fixed or escalated, issue closes on the next green run |
| "Is GroceryMatch showing fake data?" | data-honesty | answer cites file:line and screen; no unverified claims |
