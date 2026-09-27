# Records still to create, both stores

Measured 2026-09-24 by asking each store for every package in `apps.json`.
The portfolio is **43 apps**: the account owner decided on 2026-09-24 that
portfolio-board goes to the stores too, which is the decision its listing block
was waiting for.

Neither API can create an app. Apple answers `POST v1/apps` with "The resource
'apps' does not allow 'CREATE'"; Play's discovery document exposes exactly one
method on the applications resource, `dataSafety`. See `status.csv` item 0
for the single Apple sign-in that lets a script create the Apple side.

| App Store name | Package (identical on both stores) | SKU | Version | Category | Apple | Play |
| --- | --- | --- | --- | --- | :-: | :-: |
| AeroSwift | `com.americangroupllc.aeroswift` | aeroswift-001 | 1.0.0 | Travel | needed | needed |
| BodyQuest: Health Game | `com.americangroupllc.bodyquest` | bodyquest-001 | 1.1.0 | Health And Fitness | needed | needed |
| DriftDate: Layered Dating | `com.americangroupllc.driftdate` | driftdate-001 | 1.0.0 | Lifestyle | — | needed |
| Fashion Factory: Deals | `com.americangroupllc.fashionfactory` | fashionfactory-001 | 2.2.0 | Lifestyle | needed | needed |
| GadgetNest | `com.americangroupllc.gadgetnest` | gadgetnest-001 | 1.0.0 | Shopping | needed | needed |
| GroceryMatch: Save on Food | `com.americangroupllc.grocerymatch` | grocerymatch-001 | 2.1.0 | Shopping | needed | needed |
| HerJourney: Cycle & Health | `com.americangroupllc.herjourney` | herjourney-001 | 1.2.0 | Health And Fitness | needed | needed |
| MyHealth: Fitness Tracker | `com.americangroupllc.myhealth` | myhealth-001 | 1.0.0 | Health And Fitness | needed | — |
| Photriya | `com.americangroupllc.photriya` | photriya-001 | 1.0.0 | Photo And Video | — | needed |
| PlantPulse | `com.americangroupllc.plantpulse` | plantpulse-001 | 1.0.0 | Utilities | needed | needed |
| Verba: Voice Translator | `com.americangroupllc.verba` | verba-001 | 1.0.0 | Education | needed | needed |
| iMeasure: Measure & Level | `com.americangroupllc.imeasure` | imeasure-001 | 5.0.1 | Utilities | needed | — |
| Portfolio Board | `com.americangroupllc.portfolioboard` | portfolioboard-001 | 1.0.0 | Productivity | needed | needed |
| Radio Tune: Live Radio | `com.americangroupllc.radiotune` | radiotune-001 | 2.0.1 | Music | needed | — |
| YourTube: Watch & Discover | `com.americangroupllc.yourtube` | yourtube-001 | 1.0.2 | Entertainment | needed | — |

Apple: 13 to create, 30 already exist.
Play: 11 to create, 32 already exist.

The two entries deleted on 2026-09-24 (`com.americangroup.yourtube`,
`com.americangroup.myhealth`) were the old naming. Both apps already exist
under `com.americangroupllc.*` on Play and were verified intact after the
deletion; they need no re-creation there. YourTube and MyHealth do still need
an **App Store** record.

`scripts/testflight/watch_records.sh` is running: each Apple record is built,
uploaded, put in the internal tester group and submitted within five minutes
of being created.
