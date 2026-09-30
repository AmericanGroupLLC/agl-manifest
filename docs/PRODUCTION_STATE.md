# Are all 43 apps in production?

No. Measured against both stores on 2026-09-29 by asking each one directly.

## Apple — 0 in production, 16 in review

| State | Apps |
| --- | --- |
| In review now | 16 |
| Rejected once, awaiting Apple's resubmission window | 23 |
| No record | 4 |

Nothing has reached the App Store yet because nothing has finished review. The
16 in review are moving normally. The 23 are one rejection reason, not 23:
Guideline 2.1, an information request for a developer account with limited
review history (MA-028). Their answers are written into App Review Notes, and
`watch_resubmit.sh` retries them every 30 minutes because Apple answers "Version
is not ready to be submitted yet, please try again later" (MA-030).

## Google — 6 in production, 36 still Draft

**Live on production:** CalcMaster, TripNest, Uscis-Case, VirtuBand, iMaps,
iMeasure.

These six are the apps that were published before this work began, which is also
why their upload keys do not match the local keystores (MA-020) — the same six
appear in both lists.

**36 are still Draft**, and a Draft app cannot be promoted by API at all:

```
Only releases with status draft may be created on draft app
```

Promotion was attempted for every one of them today. The first production
release of a Draft app is made in Play Console, after the App content
declarations, and those have no API (MA-021, MA-025). Once an app is published
once, `python3 scripts/play_release.py --all --production` promotes every later
release.

GroceryMatch has no Play entry at all.

## What has to happen, and who can do it

| Step | Who |
| --- | --- |
| Finish Apple review on the 16 | Apple |
| Resubmit the 23 once Apple's hold lifts | automated, running |
| Screen recording per app for Guideline 2.1 | a person, on a device |
| New bundle ids for BodyQuest, MyHealth, radiotune | a decision (MA-031) |
| Play App content declarations, then first production release | a person, in Console |
| Reset 8 Play upload keys | a person, in Console |

## Verification

This was measured through the two store APIs. It could not be verified in the
browser: the Claude in Chrome extension cannot read any page on this Mac,
including `example.com`, on either local browser — Chrome DevTools Protocol
itself times out. See `docs/KNOWN_ISSUES.md`.
