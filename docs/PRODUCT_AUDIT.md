# Portfolio product audit and backlog

Generated on 2026-09-13 by `scripts/audit_product_quality.py`, which counts
signals in `lib/` for every app in `apps.json`, in the local mirror of the
org. Every number below comes from that run — re-run the script rather than
editing this file, or it starts lying. Raw data:
[`quality-audit.json`](quality-audit.json).

`LOC` is every line of every `*.dart` under `lib/`, generated files included,
because that is the metric the earlier audits used. The scorecard also carries
hand-written non-blank non-comment lines so the difference is visible.

## The shape of the portfolio

43 apps measured, 43 listed in `apps.json`. 526,475 lines of Dart, 643 test files.

| Group | Count | LOC range | Apps |
| --- | ---: | ---: | --- |
| Substantial (10,000+ LOC) | 20 | 10,325–45,370 | MyHealth, PilotEnRoute, Photriya, GroceryMatch, iMaps, daily-pulse, EventSpark, Verba, CalcMaster, DriftDate, NexusTransferPay, BuddyPlay, iMeasure, Kinnav, Uscis-Case, yourtube, FashionFactory, TripNest, HerJourney, radiotune |
| Mid-sized (2,000–9,999 LOC) | 18 | 2,620–9,063 | AGStudio, BodyQuest, VirtuBand, ApexMarketWatch, PlantPulse, CarDeal, AeroSwift, NearServe, RideZap, HomeWise, portfolio-board, NewsBoard, GadgetNest, CodeDeal, MyCard, MyFinance, WiFiTrail, AGrammarly |
| Thin (under 2,000 LOC) | 5 | 1,059–1,924 | ChefCount, AGCleaner, MileMaster, AGRecorder, RoomCraft |

Every app in `apps.json` is a Flutter app with a populated `lib/` — there is no
non-Flutter group left in this portfolio. Nor is there a template group: the
smallest app measured is RoomCraft at 1,059 LOC across 5 files,
and no two apps share both a line count and a file count.

## Movement since the previous recorded run

Apps whose `lib/` changed size by half or more since the numbers that were
previously in `quality-audit.json`. Anything asserted about these apps in an
older revision of this file should be treated as retired, not as background.

| App | LOC then | LOC now | Change |
| --- | ---: | ---: | ---: |
| CarDeal | 939 | 7,390 | ×7.9 |
| NearServe | 939 | 6,408 | ×6.8 |
| RideZap | 939 | 6,255 | ×6.7 |
| HomeWise | 939 | 5,582 | ×5.9 |
| portfolio-board | 939 | 5,522 | ×5.9 |
| WiFiTrail | 962 | 3,335 | ×3.5 |
| MileMaster | 505 | 1,467 | ×2.9 |
| AGRecorder | 553 | 1,172 | ×2.1 |
| AGCleaner | 902 | 1,817 | ×2.0 |

## Portfolio-wide gaps

- **Every one of the 43 apps names something for a screen reader**, but the coverage is shallow: 13 apps touch `Semantics(`/`semanticLabel` in only one or two files.
- **Accessibility reaches under a quarter of the widget files in 32 apps.** Largest first: MyHealth (9/214 files), PilotEnRoute (11/76 files), Photriya (9/82 files), GroceryMatch (6/108 files), iMaps (9/83 files), daily-pulse (10/60 files).
- **Responsive layout is absent or token in 12 apps** (≤1 file using `LayoutBuilder`/`MediaQuery`): DriftDate, Uscis-Case, RideZap, HomeWise, portfolio-board, MyFinance, WiFiTrail, ChefCount, AGCleaner, MileMaster, AGRecorder, RoomCraft.
- **7 apps have no central theme or design-token file**: AGCleaner, AGRecorder, ChefCount, MileMaster, PilotEnRoute, RoomCraft, WiFiTrail.
- **Test coverage is thinner than 2,000 lib LOC per test file in 1 app.** Worst first:
  - MyHealth: 45,370 LOC, 22 test files — 2,062 LOC/test file

## Backlog

Everything below is derived from the table at the end of this file. Items that
cannot be measured from `lib/` — bundle ids, store records, AdMob ids, signing
— live in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) and are not restated here.

### P0 — blocks a credible release

| Item | Apps |
| --- | --- |
| Cover startup, navigation and the primary flow — largest apps with the least test signal | MyHealth |

### P1 — important

| Item | Apps |
| --- | --- |
| Deepen accessibility past the one or two files that have it — `Semantics`, labels, 48dp targets, contrast | 32 apps under 25% file coverage, 13 apps at 1–2 files |
| Add a central theme / design tokens | AGCleaner, AGRecorder, ChefCount, MileMaster, PilotEnRoute, RoomCraft, WiFiTrail |
| Add responsive breakpoints (tablet/landscape) | DriftDate, Uscis-Case, RideZap, HomeWise, portfolio-board, MyFinance, WiFiTrail, ChefCount, AGCleaner, MileMaster, AGRecorder, RoomCraft |
| Clear TODO/FIXME debt | PilotEnRoute (29), VirtuBand (4), BodyQuest (2), GroceryMatch (2), MyHealth (2) |
| Raise test depth in the largest apps — the thinnest ratios in the portfolio | MyHealth (2,062 LOC/test), NexusTransferPay (1,783 LOC/test), PilotEnRoute (1,542 LOC/test), EventSpark (1,507 LOC/test), Photriya (1,469 LOC/test) |

### P2 — polish

- Consistent empty / loading / error states on every screen
- Intentional motion: shared-axis transitions, hero continuity
- 4/8px spacing discipline and typographic scale
- Dark mode verified per app

### P3 — nice to have

- Onboarding flows, richer search/discovery, retention hooks

## Per-app scorecard

| App | LOC | hand-written | files | tests | LOC/test | theme | a11y files | responsive files | loading | TODO |
| --- | ---: | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: | ---: |
| MyHealth | 45,370 | 40,873 | 214 | 22 | 2,062 | yes | 9 | 11 | 31 | 2 |
| PilotEnRoute | 40,100 | 36,262 | 76 | 26 | 1,542 | — | 11 | 3 | 40 | 29 |
| Photriya | 36,721 | 34,182 | 82 | 25 | 1,469 | yes | 9 | 22 | 10 | 0 |
| GroceryMatch | 33,592 | 30,153 | 108 | 47 | 715 | yes | 6 | 5 | 18 | 2 |
| iMaps | 33,289 | 22,352 | 83 | 29 | 1,148 | yes | 9 | 3 | 13 | 1 |
| daily-pulse | 20,019 | 11,954 | 60 | 15 | 1,335 | yes | 10 | 2 | 5 | 0 |
| EventSpark | 19,585 | 15,640 | 58 | 13 | 1,507 | yes | 11 | 8 | 1 | 0 |
| Verba | 18,212 | 15,208 | 64 | 34 | 536 | yes | 1 | 3 | 7 | 0 |
| CalcMaster | 18,155 | 10,630 | 80 | 24 | 756 | yes | 10 | 4 | 4 | 0 |
| DriftDate | 16,589 | 13,829 | 68 | 19 | 873 | yes | 6 | 1 | 15 | 0 |
| NexusTransferPay | 16,044 | 5,508 | 51 | 9 | 1,783 | yes | 12 | 3 | 5 | 1 |
| BuddyPlay | 15,801 | 13,452 | 80 | 11 | 1,436 | yes | 8 | 2 | 4 | 0 |
| iMeasure | 15,448 | 13,544 | 37 | 12 | 1,287 | yes | 6 | 8 | 2 | 0 |
| Kinnav | 12,775 | 6,951 | 60 | 27 | 473 | yes | 4 | 5 | 6 | 0 |
| Uscis-Case | 12,346 | 10,576 | 46 | 11 | 1,122 | yes | 12 | 1 | 9 | 0 |
| yourtube | 11,938 | 10,560 | 31 | 16 | 746 | yes | 5 | 4 | 11 | 0 |
| FashionFactory | 11,558 | 8,384 | 44 | 44 | 263 | yes | 13 | 6 | 0 | 0 |
| TripNest | 11,518 | 9,787 | 37 | 15 | 768 | yes | 11 | 4 | 0 | 0 |
| HerJourney | 10,402 | 9,450 | 36 | 8 | 1,300 | yes | 5 | 2 | 8 | 0 |
| radiotune | 10,325 | 8,689 | 49 | 12 | 860 | yes | 4 | 2 | 5 | 0 |
| AGStudio | 9,063 | 3,678 | 52 | 12 | 755 | yes | 1 | 2 | 4 | 0 |
| BodyQuest | 8,437 | 7,376 | 21 | 12 | 703 | yes | 13 | 3 | 4 | 2 |
| VirtuBand | 8,038 | 6,900 | 37 | 8 | 1,005 | yes | 6 | 2 | 1 | 4 |
| ApexMarketWatch | 7,991 | 6,559 | 37 | 11 | 726 | yes | 2 | 2 | 2 | 0 |
| PlantPulse | 7,962 | 6,695 | 37 | 12 | 664 | yes | 11 | 10 | 0 | 0 |
| CarDeal | 7,390 | 6,171 | 32 | 17 | 435 | yes | 11 | 4 | 1 | 0 |
| AeroSwift | 6,505 | 5,368 | 34 | 11 | 591 | yes | 11 | 4 | 2 | 0 |
| NearServe | 6,408 | 5,250 | 32 | 21 | 305 | yes | 8 | 5 | 3 | 0 |
| RideZap | 6,255 | 5,033 | 38 | 16 | 391 | yes | 1 | 1 | 2 | 0 |
| HomeWise | 5,582 | 4,399 | 30 | 9 | 620 | yes | 4 | 1 | 3 | 0 |
| portfolio-board | 5,522 | 4,734 | 22 | 9 | 614 | yes | 7 | 1 | 5 | 0 |
| NewsBoard | 5,499 | 4,696 | 26 | 8 | 687 | yes | 4 | 2 | 1 | 0 |
| GadgetNest | 5,459 | 4,518 | 27 | 11 | 496 | yes | 11 | 3 | 0 | 0 |
| CodeDeal | 4,886 | 2,469 | 38 | 11 | 444 | yes | 8 | 5 | 8 | 0 |
| MyCard | 4,815 | 3,902 | 27 | 10 | 482 | yes | 1 | 4 | 4 | 0 |
| MyFinance | 3,482 | 3,299 | 7 | 5 | 696 | yes | 1 | 1 | 0 | 0 |
| WiFiTrail | 3,335 | 1,166 | 17 | 7 | 476 | — | 1 | 1 | 0 | 0 |
| AGrammarly | 2,620 | 2,087 | 16 | 7 | 374 | yes | 1 | 4 | 1 | 0 |
| ChefCount | 1,924 | 1,740 | 4 | 6 | 321 | — | 1 | 1 | 0 | 0 |
| AGCleaner | 1,817 | 755 | 15 | 5 | 363 | — | 1 | 1 | 1 | 0 |
| MileMaster | 1,467 | 531 | 14 | 4 | 367 | — | 1 | 1 | 0 | 0 |
| AGRecorder | 1,172 | 435 | 17 | 6 | 195 | — | 1 | 1 | 0 | 0 |
| RoomCraft | 1,059 | 861 | 5 | 6 | 176 | — | 1 | 1 | 0 | 0 |

## Order of work

Ranked by lib LOC per test file weighted by how little of the app is named
for a screen reader, because a large app with few tests and no labels is
where a regression is least likely to be caught and most likely to hurt:

1. **MyHealth** — 45,370 LOC, 22 test files (2,062 LOC/test), a11y in 9/214 files
2. **NexusTransferPay** — 16,044 LOC, 9 test files (1,783 LOC/test), a11y in 12/51 files
3. **PilotEnRoute** — 40,100 LOC, 26 test files (1,542 LOC/test), a11y in 11/76 files
4. **Photriya** — 36,721 LOC, 25 test files (1,469 LOC/test), a11y in 9/82 files
5. **BuddyPlay** — 15,801 LOC, 11 test files (1,436 LOC/test), a11y in 8/80 files
6. **EventSpark** — 19,585 LOC, 13 test files (1,507 LOC/test), a11y in 11/58 files
7. **HerJourney** — 10,402 LOC, 8 test files (1,300 LOC/test), a11y in 5/36 files
8. **daily-pulse** — 20,019 LOC, 15 test files (1,335 LOC/test), a11y in 10/60 files

Then the theme and responsive gaps in the smaller apps.
