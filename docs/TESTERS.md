# Who can install, and who cannot

The roster itself lives in `store/testers.json`, which is what
`scripts/testflight/external_testers.rb` and `scripts/sync_play_testers.py` read.
This file is the explanation; that file is the source.

Measured from App Store Connect and Google Play on 2026-10-01.

## App Store Connect account users (2)

| Email | Name | Role |
| --- | --- | --- |
| `srikanth.patchava@outlook.com` | Srikanth Patchava | ACCOUNT_HOLDER, ADMIN |
| `rainbow472.sri@gmail.com` | Srikanth Patchava | ADMIN — also the Google Play admin |

These two can install any build immediately: internal groups carry
`hasAccessToAllBuilds`, so no Beta App Review and no contract is involved.

## External testers (9)

Nobody else holds an account on either store. All nine are on the
`AGL Testers` external group of **all 43 apps**:

| Email | Apps |
| --- | --- |
| `aadiboddapati@gmail.com` | 43 |
| `mouni123.nekkalapudi@gmail.com` | 43 |
| `nehuwakhare04@gmail.com` | 43 |
| `pranathim95@gmail.com` | 43 |
| `rashmi.advani@gmail.com` | 43 |
| `siddarthaandalu@gmail.com` | 43 |
| `sirishapatchava@gmail.com` | 43 |
| `suresh.alaparti@gmail.com` | 43 |
| `vspatel24@gmail.com` | 43 |

Counted from `GET v1/betaTesters/{id}/apps` for every record of every address.
`nehuwakhare04@gmail.com` has 44 tester records against 43 apps — one orphan
with no app, left over from that account being removed and re-added. Harmless.

**None of them can install yet**, and that is not about their membership. An
external group receives a build only after Beta App Review, and submitting it
fails with "Beta contract is missing for the app" — MA-019. Once that
agreement is accepted, all nine get every build with no further work.

## Google Play: zero of 43, and the API cannot fix it

Every app has an empty tester list on `internal`, `alpha` and `beta`
(`python3 scripts/sync_play_testers.py --audit`). This is not an oversight and not a permissions
problem. Play's `Testers` resource has exactly one field, `googleGroups`:

```
PUT .../edits/{id}/testers/internal  {"testers": ["someone@gmail.com"]}
400 INVALID_ARGUMENT  Unknown name "testers" at 'testers': Cannot find field.
```

So individual addresses can only be entered in Play Console, 43 times per
track. Naming a Google Group in the `google_groups` key of
`store/testers.json` and passing it as `PLAY_TESTER_GOOGLE_GROUP` makes
`scripts/sync_play_testers.py` apply it to all 43 apps across all three
tracks instead. See MA-033.

## Two API facts worth not rediscovering

**The bulk assignment endpoint is gone.** Spaceship's
`post_bulk_beta_tester_assignments` posts to `v1/bulkBetaTesterAssignments`,
and Apple answers every call with

```
409  The URL path is not valid - The resource 'v1/bulkBetaTesterAssignments' does not exist
```

`set_team_access.rb` called it inside a bare `rescue`, so its "external
assignments" count was reporting attempts rather than successes. It says so now.

**Attaching an existing tester by relationship only works once.**
`POST v1/betaGroups/{id}/relationships/betaTesters` succeeds for the first
group an address joins and then answers every later one with
`409 STATE_ERROR  Tester(s) cannot be assigned`. The call that works for all
43 is `POST v1/betaTesters` carrying the group in `relationships` — despite
reading like a create, Apple keys on the email and simply adds the group.

That is also why a tester shows "1 group" when queried: Apple keeps one
`betaTester` record per *(email, app)* pair, so membership must be counted
across records, not within one. Counting within one record is what made an
earlier pass report nine people on one app each when they were on all 43.

## What changed on the Apple side, and one thing worth knowing

Four people lost App Store Connect account access:
aadiboddapati, sirishapatchava, nehuwakhare04 and suresh.alaparti.

Removing an account user also deletes their beta-tester record. Two of the
four disappeared from TestFlight entirely and one was left with no groups at
all, so all four were re-added to the external group afterwards. Re-add the
testers *after* removing the user, not before.

Checked before removing anyone: no certificate belongs to any of them. The
certificate the pipeline signs with, `2S2F6CDFY2`, is issued to
"American Group LLC", and the only per-person certificates are development
ones belonging to the account holder. Two of the four held
CLOUD_MANAGED_DEVELOPER_ID, which can take cloud-managed signing assets with
it, so this was verified rather than assumed.
