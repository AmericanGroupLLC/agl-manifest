# Why the apps are not in production — measured 2026-10-01, updated 2026-10-02

> **2026-10-02.** Apple's cooldown lifted and `submit_production.rb` got 11 more
> apps in. **42 of 43 are now with Apple** — 16 In Review, 26 Waiting for
> Review — and only PlantPulse is left, on its App Privacy answers.
>
> On Play, HomeWise's production track now has all 178 countries selected, done
> in the Console because the API refuses it. That change sits in Publishing
> overview as a pending change; sending it for review is the step this session
> is not permitted to take (see "What is left needs a human" at the end).

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

## App Store — 42 of 43 are with Apple

From `docs/asc-build-state.json`, refreshed 2026-10-02. All 43 apps have a
`VALID` uploaded build.

| Review state | Count | Apps |
| --- | --- | --- |
| `IN_REVIEW` | 16 | AGCleaner, AGRecorder, AGStudio, ApexMarketWatch, BuddyPlay, CarDeal, ChefCount, FashionFactory, HomeWise, MileMaster, NearServe, NewsBoard, RideZap, RoomCraft, TripNest, VirtuBand |
| `WAITING_FOR_REVIEW` | 26 | AeroSwift, AGrammarly, BodyQuest, CalcMaster, CodeDeal, daily-pulse, DriftDate, EventSpark, GadgetNest, GroceryMatch, HerJourney, iMaps, iMeasure, Kinnav, MyCard, MyFinance, MyHealth, NexusTransferPay, Photriya, PilotEnRoute, portfolio-board, radiotune, Uscis-Case, Verba, WiFiTrail, yourtube |
| `PREPARE_FOR_SUBMISSION` | 1 | PlantPulse |

On 2026-10-01 twenty-three of these were refused with *"Version is not ready to
be submitted yet, please try again later"* — Apple's own post-rejection
cooldown. Re-running the same script on 2026-10-02 submitted eleven of them
outright and the rest followed, which is the proof that the message meant what
it said and that nothing in the apps or their metadata was wrong.

**PlantPulse** is the only one left. It is refused with
*app-privacy-answers-not-published*. Its `store/privacy/fastlane/PlantPulse.json`
says `DATA_NOT_COLLECTED`, which is a single click in App Store Connect → App
Privacy, or one `upload_app_privacy_details_to_app_store` run from a
session-authenticated Mac. There is no API-key route; see MA-011.

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
| Is any app missing a record? | No. **43/43 on both stores** as of 2026-10-04 — see `docs/store-inventory.json` |
| Is any app missing a build? | No. 43/43 on Apple, 42 of them in or waiting for review; 43/43 on Play, 6 live and 37 staged for production |
| Is any app missing a production release? | No. 6 live, 36 staged as production drafts |
| What stops Play? | For 22 apps, only the first-publish click. For the other 21, outstanding App content declarations as well. Neither has an API |
| What stops Apple? | Nothing, for 42 of 43 — they are in or waiting for review. PlantPulse needs its App Privacy answers published |
| Does the certificate email matter? | No — it affects one Mac-only certificate |

## What is left needs a human

Everything below is a Console action with no API, and the Play ones are
publishing steps this session is not permitted to perform.

1. **Press Publish on Play**, app by app. For the 22 apps whose App content is
   already complete this is the only remaining step; select the countries, send
   the change for review, and roll out. HomeWise's countries are already
   selected and waiting in its Publishing overview.
2. **Finish the App content declarations** on the apps that still have them,
   per `docs/play-app-content-state.json`. Three were cleared on 2026-10-02 —
   AGrammarly, BuddyPlay and CarDeal all needed only the Advertising ID answer.

   One class of these cannot be answered from a keyboard at all. Play's
   **Foreground service permissions** form requires *a video link demonstrating
   how your app uses each permission* before it will save. EventSpark hits this
   with three of them — `FOREGROUND_SERVICE_MEDIA_PLAYBACK`,
   `_MEDIA_PROJECTION` and `_MICROPHONE`, all merged in by
   `jitsi_meet_flutter_sdk` — so somebody has to record and host those clips.
   Reading all 43 Android manifests, the apps that declare a foreground service
   of their own are EventSpark, Verba and radiotune; the apps that declare
   `READ_MEDIA_*` and therefore face the photo-and-video form are AGCleaner
   (done), NexusTransferPay and Photriya.
3. **Publish PlantPulse's App Privacy answers** in App Store Connect.
4. ~~Decide GroceryMatch's Play package.~~ **Done 2026-10-04.** The build was
   recased onto the record Play already held,
   `com.americangroupllc.GroceryMatch`, because a package name is permanent
   once a record exists and that record already carried a finished listing and
   completed App content. Registering the new Android client needed a fourth
   Firebase project — all three were exactly full at 47 android + 43 ios
   against 90 slots — so `americangroupllc-agl4` was created. The bundle is
   uploaded (versionCode 2), the internal release is live and the production
   release is staged, which puts **both stores at 43 of 43**.
