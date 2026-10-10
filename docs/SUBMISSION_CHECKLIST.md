# The gate an app passes before it is submitted

Run it:

```bash
python3 scripts/store_checklist.py            # all 43 -> docs/store-checklist.json
python3 scripts/store_checklist.py --app Verba
```

Every row is measured against the tree, the store records, or an artefact on
disk. `HUMAN` means a machine cannot settle it, not that it passed.

## Why this document exists

On 2026-10-05, 26 of 43 apps were rejected. **All 28 checks in the previous
checklist passed for every one of them.** They verified that a thing was
*present*, not that it was *right*:

| What the old check said | What Apple saw |
| --- | --- |
| "Per-app review notes — PASS" | notes answering Apple's **older five-item** request |
| "Screenshots (Apple ≥1, Play ≥2) — PASS" | two near-identical **login screens** |
| nothing | no demo account on an app that cannot be used without signing in |
| nothing | no answer to the 4.3 question Apple asks every large portfolio |

The six checks below were added for exactly those gaps. The rule they encode:
*a check that cannot fail has not been written.*

## The checks that came from real rejections

### Review notes answer Apple's 7 items
Apple's current Guideline 2.1 request lists seven items and says to put them
in the Notes field. The notes answered a five-item version. The check counts
numbered headings `2.`–`7.`; `review_notes.rb` writes them, and writes the
same text into `store/apps/<repo>.json` so the repository and App Store
Connect cannot drift apart again — they had.

Item 1, a screen recording on a physical device, is the one thing no script
produces. It is required for every app rejected under 2.1.

### Demo account when the app gates on sign-in
`login_gate()` reads the app's Dart for a sign-in call with no guest path.
Five apps have one, and the only bypass is compiled out of release builds
(`!kReleaseMode`), so a reviewer meets a wall. All 43 declared
`demoAccountRequired: false`. See MA-036 — the documented test accounts do
not authenticate.

### Screenshots show the app, not a login screen
`screenshots.py` records whether it saw a sign-in gate and whether it got
past it. Before this, the capture photographed the login form and the
checklist counted the files and said PASS.

### App preview video
Optional for approval; checked so its absence is a decision rather than an
oversight.

### Launches on a simulator and stays up
Read from the newest `sim_install.py` report: built, installed, launched, and
still running seconds later. A binary that dies on launch is the fastest
possible 2.1.

### 4.3 differentiation statement
Fourteen apps were rejected under Guidelines 4.3 and 4.2.6 — spam and app
generation services. Apple asks, per app, what gap it fills and how it
differs from the others in the same account.

`differentiation_scaffold.py` drafts the answerable parts and leaves two as
`TODO`: the market gap, and the beta testing that actually happened. The
check fails while a TODO remains. **Inventing those answers is precisely
what 4.2.6 screens for.**

Measured input for that conversation: no two of the 43 apps share more than
22% of their description vocabulary. The copy is not duplicated, so the
trigger is more likely the shared code scaffold and the number of apps
submitted together.

### Every API host the app calls exists

Added 2026-10-07. **18 apps** called hosts with no DNS record at all, and
seven of those hosts were our own: `api.americangroupllc.com` (11 apps),
`api.americangroup.ai`, `api.verba.americangroupllc.com`, `photriya.cloud`,
`grocerymatch.app`, `uscis-case94.manus.app`, `api.ridezap.americangroupllc.com`.
GroceryMatch's *sign-in* posted to one of them.

The org has no API server. Every app talks to Supabase directly, so a
first-party API hostname in an app is a placeholder that shipped. Analyze,
tests and the simulator all pass it, because none of them leave the laptop —
the only thing that catches it is asking DNS.

The gate distinguishes ours from theirs because the fix differs. Ours never
existed: move the call to Supabase. Theirs existed and went away —
`feeds.reuters.com`, the retired `at1`/`fi1`/`nl1` radio-browser mirrors —
and needs a live replacement.

Measured by `scripts/verify_api_hosts.py`; the detail names file and line.

### Adopts the UIScene lifecycle, and has a launch screen

Added 2026-10-08, from a launch on an iOS 27.1 simulator that died within
seconds:

```
EXC_BREAKPOINT  UIKitCore  _UIApplicationEvaluateRuntimeIssueForNoSceneLifecycleAdoption
```

Apple said at WWDC25 that the release after iOS 26 would require the UIScene
lifecycle. iOS 27 does. **21 of the 43 apps had no
`UIApplicationSceneManifest`**, so each crashed on launch for every user on
iOS 27 — App Review included. Fifteen of them had also stripped both
storyboards out of the Runner target (a workaround for a time this machine
could not run `ibtool`) and built their window by hand, which left them with
no launch screen.

`scripts/ios_scene_lifecycle.py` brings them to the shape AeroSwift ships:
storyboards back in Resources, a scene manifest naming `FlutterSceneDelegate`,
and an AppDelegate on `FlutterImplicitEngineDelegate`. The proof is a launch on
an iOS 27 simulator (`scripts/sim_install.py <app> --ios`), not a green build.

## Before the next submission

1. `python3 scripts/store_checklist.py` — no FAIL rows.
2. Every `TODO` in `differentiation` answered by a person.
3. A screen recording per app, captured on a physical device.
4. For the five sign-in-walled apps: a demo account that actually
   authenticates, or a guest path.
5. Do **not** resubmit anything rejected under 4.3 until the apps have
   changed. Apple's own words: *"If the app is resubmitted without
   substantial improvements, it will be rejected again, and may be rejected
   for additional issues."*

## Known limits

* `Play IARC questionnaire`, `Play reaches Console account users` — no API.
* Age rating is not editable while a version is in review; FashionFactory
  fails that row for this reason and will clear when review ends.
