# App Store delivery

**Goal:** all 43 apps live on the App Store and Google Play with real data.
**Acceptance:** every app passes `apple_requirements.py` and `screenshot_audit.py`; Apple shows READY_FOR_SALE; Play production.

| Task | Owner | Status | Evidence / blocker |
| --- | --- | --- | --- |
| Reply to 16 Guideline 5.6 findings | founder | open | MA-043 |
| Answer 4.3 questions for 26 apps | founder + store-compliance | open | MA-041 |
| Fresh screenshots for daily-pulse, DriftDate, GroceryMatch, Kinnav, yourtube | qa-screenshots | open | capture stopped at sign-in/onboarding |
| Re-capture AGrammarly, CalcMaster (stale after lib change) | qa-screenshots | open | deliver_metadata freshness guard |
| Daily delivery green | release-manager | verifying | ship.yml run 38031862223 |
