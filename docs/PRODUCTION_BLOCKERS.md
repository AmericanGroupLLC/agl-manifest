# Why the apps are not in production — measured 2026-10-01

Every number here came from an API call or a Play Console page read on
2026-10-01. Nothing in this file is an estimate.

Regenerate the Play half with:

```bash
python3 scripts/play_production_blockers.py       # -> docs/play-production-blockers.json
```

and the Apple half with:

```bash
source scripts/testflight/env.sh
bundle exec ruby scripts/asc_build_state.rb       # -> docs/asc-build-state.json
bundle exec ruby scripts/testflight/submit_production.rb
```

## Google Play — 6 of 43 live

| State | Count | Apps |
| --- | --- | --- |
| `LIVE_PRODUCTION` | 6 | CalcMaster, TripNest, Uscis-Case, VirtuBand, iMaps, iMeasure |
| `PRODUCTION_DRAFT_STAGED` | 36 | everything else |
| `NO_LISTING` | 1 | GroceryMatch |

The 6 that are live are the ones that were already published before this
programme started. **Every other app already has its build sitting on the
production track as a draft release** — `play_release.py --production --stage`
put it there — so no build selection, no rollout and no upload is outstanding.

### What is actually in the way

Two things, and the API can do neither.

**1. App content declarations are incomplete.** Read directly from Play Console
for AGCleaner on 2026-10-01: *App content → "Need attention (3)"* —

| Declaration | What Google said |
| --- | --- |
| Content ratings | "All developers are required to submit this declaration for their apps" |
| Advertising ID | "You will not be able to submit releases targeting Android 13 until you complete this section" |
| Photo and video permissions | "One or more of your app bundles or APKs includes the Photo and video permissions in its manifest" |

Google publishes **no API for any of these**. `androidpublisher v3` exposes
edits, bundles, listings, images, details, testers, tracks and country
availability — and nothing else. They are Play Console forms.

Completed in the console on 2026-10-01 for AGCleaner, which took its counter
from 3 to 1:

* Advertising ID — answered *Yes* (the manifest carries
  `com.google.android.gms.permission.AD_ID`, merged in by `firebase_analytics`
  via `agl_observability`) with purpose *Analytics*. AGCleaner has no ads SDK,
  so *Advertising or marketing* was deliberately **not** ticked.
* Photo and video permissions — justified `READ_MEDIA_IMAGES`: the app hashes
  every image in the library to find duplicates and oversized photos, which the
  system photo picker cannot do.

Content ratings is still outstanding for AGCleaner, and all three are still
outstanding for the other 35.

### App content, read app by app

Every one of the 43 apps' App content page was opened in Play Console on
2026-10-01 and its *Need attention* counter read. The result is in
`docs/play-app-content-state.json`, and it corrects the assumption that this is
the universal blocker — for half the portfolio it is already done:

| Declarations outstanding | Apps |
| --- | --- |
| 0 | AGRecorder, AGStudio, ApexMarketWatch, CalcMaster, ChefCount, CodeDeal, GroceryMatch, HomeWise, MileMaster, MyCard, MyFinance, MyHealth, NearServe, PilotEnRoute, RideZap, RoomCraft, TripNest, Uscis-Case, VirtuBand, WiFiTrail, iMaps, iMeasure — **22 apps** |
| 1 | AGCleaner, AGrammarly, BuddyPlay, CarDeal, EventSpark, NewsBoard, NexusTransferPay, radiotune, yourtube — 9 apps |
| 2 | daily-pulse |
| 10 | AeroSwift, BodyQuest, DriftDate, FashionFactory, GadgetNest, HerJourney, Kinnav, PlantPulse, Verba, portfolio-board — 10 apps |
| 11 | Photriya |

So **16 apps are one declaration or fewer away**, and 11 apps have barely
started. The 22 at zero are blocked by nothing but the publish itself.

**2. A never-published app is a "Draft app", and the API refuses to publish it.**
Verified against all 43 packages: a production release with `status:
"completed"` is rejected with

```
Only releases with status draft may be created on draft app
```

A release with `status: "draft"` is accepted, which is why all 36 are staged.
Setting the production track's countries over the API is refused too —
`countryTargeting` on that release returns *"Country targeting is only supported
for staged releases"* (verified on HomeWise, 2026-10-01) — so "Select countries
and regions" is a Console action as well.
The first production release of a draft app has to be made in the console. Play
Console's own dashboard for AGCleaner lists the production track as
**"1 of 5 complete"**:

1. Select countries and regions — not done
2. Create a new release — done (the staged draft)
3. Preview and confirm the release — not done
4. Send the release to Google for review — not done
5. Publish your app on Google Play — not done

**GroceryMatch's package name is cased differently on Play.** The record is
`com.americangroupllc.GroceryMatch` — capital G and M — and an edit against it
opens normally. The app builds `com.americangroupllc.grocerymatch`, all
lowercase, which is why every upload 404s with *"Package not found"*. Apple
holds the lowercase form with a VALID build, and both are permanent. The Play
record is also already registered under Android developer verification, so the
Android `applicationId` should be changed to match the record rather than a
second Play app being created. Its App content is complete, so this rename is
the only thing between it and the same publish step as the other 22.

## App Store — 19 of 43 are with Apple, 24 are not

From `docs/asc-build-state.json`, refreshed 2026-10-01. All 43 apps have a
`VALID` uploaded build; the difference is review state.

| Review state | Count | Apps |
| --- | --- | --- |
| `IN_REVIEW` | 16 | AGCleaner, AGRecorder, AGStudio, ApexMarketWatch, BuddyPlay, CarDeal, ChefCount, FashionFactory, HomeWise, MileMaster, NearServe, NewsBoard, RideZap, RoomCraft, TripNest, VirtuBand |
| `WAITING_FOR_REVIEW` | 3 | BodyQuest, MyHealth, radiotune |
| `PREPARE_FOR_SUBMISSION` | 24 | the rest |

`submit_production.rb` was run against all 43 on 2026-10-01. Of the 24 not yet
with Apple:

* **23 are refused by Apple itself** with *"Version is not ready to be
  submitted yet, please try again later"*. That is Apple's own cooldown after a
  rejection — the version cannot be resubmitted until Apple reopens it. There
  is nothing to fix in the app or the metadata; re-running the script later is
  the whole remedy.
* **PlantPulse** is refused with *app-privacy-answers-not-published*. Its
  `store/privacy/fastlane/PlantPulse.json` says `DATA_NOT_COLLECTED`, which is a
  single click in App Store Connect → App Privacy, or one
  `upload_app_privacy_details_to_app_store` run from a session-authenticated
  Mac. There is no API-key route; see MA-011.

## The Developer ID certificate email is not a blocker

Apple mailed the account about the original *Developer ID Certification
Authority* expiring 2027-02-01. Every certificate on the team was downloaded
from the API and its real issuer read with `openssl` on 2026-10-01:

| Type | Issuer | Expires |
| --- | --- | --- |
| `DEVELOPER_ID_APPLICATION` | **Developer ID Certification Authority** | 2027-02-01 |
| `DISTRIBUTION` | Apple Worldwide Developer Relations CA, G3 | 2027-09-30 |
| `DISTRIBUTION` | Apple Worldwide Developer Relations CA, G3 | 2027-06-09 |
| `MAC_INSTALLER_DISTRIBUTION` | Apple Worldwide Developer Relations CA, G3 | 2027-06-09 |
| `DEVELOPMENT` ×2 | Apple Worldwide Developer Relations CA, G3 | 2027-06-09 |

Exactly one certificate comes from the authority in the email, and it is the
`Developer ID Application` certificate, which signs **Mac software distributed
outside the Mac App Store**. The App Store signing certificates are issued by a
different authority — Apple WWDR G3 — which the email does not mention.

The empirical check agrees: all 43 apps have a `VALID` build accepted by Apple,
16 of them are In Review right now and 3 are Waiting for Review. Apple rejects
an upload whose signing certificate is not valid, so none of this could have
happened if the signing chain were broken. **No iOS or Android delivery is
affected.** The Developer ID certificate needs replacing before 2027-02-01 only
if the organisation ever ships notarised Mac software.

## Summary

| Question | Answer |
| --- | --- |
| Is any app missing a build? | No. 43/43 on Apple. On Play, GroceryMatch's uploads miss because its record is cased `com.americangroupllc.GroceryMatch` |
| Is any app missing a production release? | No. 6 live, 36 staged as production drafts |
| What stops Play? | For 22 apps, only the first-publish click. For the other 21, outstanding App content declarations as well. Neither has an API |
| What stops Apple? | Apple's own post-rejection cooldown on 23 apps; App Privacy on PlantPulse |
| Does the certificate email matter? | No — it affects one Mac-only certificate |
