# Who can install, and who cannot

Measured from App Store Connect on 2026-10-01, after reducing account access.

## App Store Connect account users (2)

| Email | Name | Role |
| --- | --- | --- |
| `srikanth.patchava@outlook.com` | Srikanth Patchava | ACCOUNT_HOLDER, ADMIN |
| `rainbow472.sri@gmail.com` | Srikanth Patchava | ADMIN — also the Google Play admin |

These two can install any build immediately: internal groups carry
`hasAccessToAllBuilds`, so no Beta App Review and no contract is involved.

## External testers (8)

Everyone else is external only, on `AGL Testers`:

| Email | Groups |
| --- | --- |
| `aadiboddapati@gmail.com` | AGL Testers |
| `nehuwakhare04@gmail.com` | AGL Testers |
| `pranathim95@gmail.com` | AGL Testers, Kinnav |
| `rashmi.advani@gmail.com` | AGL Testers |
| `siddarthaandalu@gmail.com` | AGL Testers |
| `sirishapatchava@gmail.com` | AGL Testers |
| `suresh.alaparti@gmail.com` | AGL Testers |
| `vspatel24@gmail.com` | AGL Testers, Kinnav |

**None of them can install yet**, and that is not about their membership. An
external group receives a build only after Beta App Review, and submitting it
fails with "Beta contract is missing for the app" — MA-019. Once that
agreement is accepted, all eight get every build with no further work.

## What changed, and one thing worth knowing

Four people lost App Store Connect account access:
aadiboddapati, sirishapatchava, nehuwakhare04 and suresh.alaparti.

Removing an account user also deletes their beta-tester record. Two of the
four disappeared from TestFlight entirely and one was left with no groups at
all, so all four were re-added to the external group afterwards — 162
assignments across the 43 apps. Re-add the testers *after* removing the user,
not before.

Checked before removing anyone: no certificate belongs to any of them. The
certificate the pipeline signs with, `2S2F6CDFY2`, is issued to
"American Group LLC", and the only per-person certificates are development
ones belonging to the account holder. Two of the four held
CLOUD_MANAGED_DEVELOPER_ID, which can take cloud-managed signing assets with
it, so this was verified rather than assumed.
