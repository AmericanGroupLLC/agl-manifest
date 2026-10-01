# "The requested app is not available or doesn't exist"

Diagnosed 2026-09-30 by reading both stores directly. Nothing in the pipeline is
broken — three different things each need one action, and they are easy to
confuse because the symptom looks the same.

## 1. Google Play — this is the message you are seeing

That exact wording is Play's, and it appears when the Google account opening an
internal-testing link is **not on that app's tester list**.

Measured: **42 of 42 internal tracks have no testers at all.**

```
GET /edits/{id}/testers/internal  ->  {}      (every app)
```

The builds are there and the releases are live — 36 apps have a bundle and 34
are live on the internal track. Nobody is authorised to see them, so every
internal link gives that error to everyone.

**Why it has not been fixed:** Play's `Testers` resource takes **Google Groups
only**. Its schema has exactly one property, `googleGroups`. There is no way to
add a tester by email address through the API.

**Fix:** create one Google Group containing the testers, then set
`PLAY_TESTER_GOOGLE_GROUP` and the sync attaches it to all 42 in one pass. Or add
an email list per app in Console under Testing → Internal testing → Testers.

## 2. Apple TestFlight — it works; the invitations are unaccepted

TestFlight is correctly wired. For AGCleaner, as an example:

| Group | Internal | All builds | Latest build attached | Testers |
| --- | --- | --- | --- | --- |
| Internal testers | yes | yes | yes | 6 |
| AGL Internal | yes | yes | yes | 6 |

And the proof it works — the per-tester state on that group:

| Tester | State |
| --- | --- |
| rainbow472.sri@gmail.com | **INSTALLED** |
| srikanth.patchava@outlook.com | INVITED |
| suresh.alaparti@gmail.com | INVITED |
| aadiboddapati@gmail.com | INVITED |
| nehuwakhare04@gmail.com | INVITED |
| sirishapatchava@gmail.com | INVITED |

One account has already installed the build. The rest are `INVITED`, meaning
Apple sent the invitation and it has not been accepted yet. An invited tester
sees nothing in TestFlight until they accept.

**Fix, per Apple ID:** install TestFlight, sign in with *that* Apple ID, and
accept the invitation — from the emailed link or the Redeem option. The builds
are valid and unexpired, so they appear immediately afterwards.

## 3. App Store links — nothing has been released yet

No app has finished review, so any `apps.apple.com` link will say the app is not
available. 16 are In Review and 23 are held by Apple's post-rejection window.
This resolves itself when review completes; it is not a configuration problem.

## The short version

| Link you clicked | Why it fails | Who fixes it |
| --- | --- | --- |
| Play internal testing | no testers on any track; Play takes Google Groups only | create one Google Group |
| TestFlight | invitation not accepted on that Apple ID | accept it in TestFlight |
| App Store | not released; still in review | Apple |
