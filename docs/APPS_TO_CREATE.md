# Records to create, and records to delete

Generated from the table the account owner supplied on 2026-09-22 and checked
against `apps.json`, `store/apps/` and the Developer Portal. Every bundle id
below is already registered in the portal, so App Store Connect will offer it
in the Bundle ID list when the record is created.

The App Store Connect API cannot do either job. Verified 2026-09-22:

```
POST   v1/apps  ->  The resource 'apps' does not allow 'CREATE'
DELETE v1/apps  ->  The resource 'apps' does not allow 'DELETE'
        Allowed operations are: GET_COLLECTION, GET_INSTANCE, UPDATE
```

## Create these 14 in App Store Connect

| App Store name | Bundle ID and Android package | SKU | Version | Category |
| --- | --- | --- | --- | --- |
| AeroSwift | `com.americangroupllc.aeroswift` | aeroswift-001 | 1.0.0 | Travel |
| BodyQuest: Health Game | `com.americangroupllc.bodyquest` | bodyquest-001 | 1.1.0 | Health And Fitness |
| Daily Pulse: Morning Brief | `com.americangroupllc.dailypulse` | dailypulse-001 | 1.0.0 | Lifestyle |
| Fashion Factory: Deals | `com.americangroupllc.fashionfactory` | fashionfactory-001 | 2.2.0 | Lifestyle |
| GadgetNest | `com.americangroupllc.gadgetnest` | gadgetnest-001 | 1.0.0 | Shopping |
| GroceryMatch: Save on Food | `com.americangroupllc.grocerymatch` | grocerymatch-001 | 2.1.0 | Shopping |
| HerJourney: Cycle & Health | `com.americangroupllc.herjourney` | herjourney-001 | 1.2.0 | Health And Fitness |
| iMeasure: Measure & Level | `com.americangroupllc.imeasure` | imeasure-001 | 5.0.1 | Utilities |
| MyHealth: Fitness Tracker | `com.americangroupllc.myhealth` | myhealth-001 | 1.0.0 | Health And Fitness |
| PlantPulse | `com.americangroupllc.plantpulse` | plantpulse-001 | 1.0.0 | Utilities |
| Portfolio Board | `com.americangroupllc.portfolioboard` | portfolioboard-001 | 1.0.0 | Productivity |
| Ratio Tune: Live Radio | `com.americangroupllc.radiotune` | radiotune-001 | 2.0.1 | Music |
| Verba: Voice Translator | `com.americangroupllc.verba` | verba-001 | 1.0.0 | Education |
| YourTube: Watch & Discover | `com.americangroupllc.yourtube` | yourtube-001 | 1.0.2 | Entertainment |

Listing copy, screenshots, categories and age ratings for all fourteen are
already prepared, so nothing needs typing beyond the row above. Start
`scripts/testflight/watch_records.sh` and each app is built, uploaded, added to
the tester group and submitted for beta review within five minutes of its
record appearing.

## Delete these from App Store Connect

Three records still carry a bundle id without `llc`. All three are
`PREPARE_FOR_SUBMISSION`, never released, so App Store Connect allows deletion.
Their replacements are in the table above.

| Delete | Reason |
| --- | --- |
| `com.americangroup.aeroswift` (AeroSwift) | superseded by `com.americangroupllc.aeroswift` |
| `com.americangroup.radiotune` (Ratio Tune: Live Radio) | superseded by `com.americangroupllc.radiotune` |
| `com.americangroup.bodyquest` (BodyQuest: Health Game) | superseded by `com.americangroupllc.bodyquest` |
| `com.americangroupllc.styleradar` (Fashion Factory: Deals) | same app under the wrong identifier; the table calls for `com.americangroupllc.fashionfactory` |

Three further records belong to no app in `apps.json` and look abandoned:
`com.americangroupllc.offlinebuddy` (OfflineBuddy), `com.americangroupllc.Mykarma`
(iMykarma) and `com.americangroupllc.dealzap` (iDealZap). They are left alone
because nothing in this portfolio claims them; delete them only if you know
they are dead.

## Delete from Google Play

`com.americangroup.yourtube` exists in Play under the old naming. The Play
Developer API cannot create or delete an app, so this is a Play Console action
too. Create YourTube under `com.americangroupllc.yourtube` and abandon the old
entry.

## Developer Portal

45 bundle ids under `com.americangroup.` remain registered in the Developer
Portal. They are registrations, not store records, and nothing builds against
them any more. They are deliberately left in place: three are still referenced
by the app records above and must outlive them, and removing the rest buys
nothing while risking a profile that is still in use. Say the word and they go.
