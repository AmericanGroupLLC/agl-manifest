# Portfolio product audit and backlog

Measured across every Flutter app on 2026-09-09 by counting real signals in
`lib/` — not impressions. Raw data: [`quality-audit.json`](quality-audit.json).

## The shape of the portfolio

| Group | Count | What it means |
| --- | --- | --- |
| Substantial apps (10k+ LOC) | 18 | Real products; need polish, states, a11y, tests |
| Smaller real apps | 13 | Working but shallow |
| **Identical shells** | 5 | CarDeal, HomeWise, NearServe, RideZap, portfolio-board — the *same* 4-screen scaffold (home/search/profile/settings) with only the brand changed. No domain functionality. These need building, not polishing. |
| Not yet Flutter | 6 | AGStudio, ApexMarketWatch, BuddyPlay, CodeDeal, MyCard, PlantPulse |

## Portfolio-wide gaps

- **Accessibility is absent in 24 of 36 apps** (no `Semantics`, no `semanticLabel`).
  Worst offenders by size: MyHealth, PilotEnRoute, Photriya, daily-pulse, CalcMaster.
- **Responsive layout is absent or token in 18 apps** (≤1 use of `LayoutBuilder`/`MediaQuery`).
- **9 apps have no central theme/design-system file**: AGCleaner, AGRecorder, ChefCount, MileMaster, MyFinance, NexusTransferPay, PilotEnRoute, RoomCraft, WiFiTrail.
- **Test coverage is far too thin for the size** in 4 apps:
  - MyHealth: 44,591 LOC, only 3 test file(s)
  - daily-pulse: 16,644 LOC, only 2 test file(s)
  - yourtube: 11,280 LOC, only 1 test file(s)
  - HerJourney: 10,219 LOC, only 5 test file(s)

## Backlog

### P0 — blocks a credible release

| Item | Apps |
| --- | --- |
| Build actual product functionality; today they are one shared shell | CarDeal, HomeWise, NearServe, RideZap, portfolio-board |
| Port to Flutter | AGStudio, ApexMarketWatch, BuddyPlay, CodeDeal, MyCard, PlantPulse |
| Fix wrong AdMob publisher id | yourtube |
| Fix unresolved `$(ADMOB_APP_ID)` (launch crash) | iMaps |
| Resolve the taken bundle id | MyHealth |
| Reconcile iOS/Android identifier mismatch before publish | HerJourney, PilotEnRoute, daily-pulse |

### P1 — important

| Item | Apps |
| --- | --- |
| Add accessibility: `Semantics`, labels, 48dp targets, contrast | 24 apps |
| Raise test coverage to match size | MyHealth, daily-pulse, yourtube, HerJourney |
| Add a central theme / design tokens | AGCleaner, AGRecorder, ChefCount, MileMaster, MyFinance, NexusTransferPay, PilotEnRoute, RoomCraft, WiFiTrail |
| Add responsive breakpoints (tablet/landscape) | 18 apps |
| Clear TODO/placeholder debt | PilotEnRoute (65), Verba (38), MyHealth (21), DriftDate (16), Uscis-Case (16) |

### P2 — polish

- Consistent empty / loading / error states on every screen
- Intentional motion: shared-axis transitions, hero continuity
- 4/8px spacing discipline and typographic scale
- Dark mode verified per app

### P3 — nice to have

- Onboarding flows, richer search/discovery, retention hooks

## Per-app scorecard

| App | LOC | tests | theme | loading | empty | error | a11y | responsive | motion | TODO |
| --- | ---: | ---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MyHealth | 44,591 | 3 | ✅ | 50 | 44 | 42 | 0 | 15 | 4 | 21 |
| PilotEnRoute | 39,443 | 10 | — | 162 | 39 | 143 | 0 | 3 | 18 | 65 |
| Photriya | 36,170 | 15 | ✅ | 94 | 23 | 52 | 0 | 33 | 80 | 4 |
| GroceryMatch | 33,574 | 44 | ✅ | 32 | 21 | 107 | 7 | 5 | 9 | 7 |
| iMaps | 32,201 | 20 | ✅ | 60 | 30 | 86 | 9 | 2 | 49 | 5 |
| EventSpark | 19,364 | 7 | ✅ | 8 | 48 | 27 | 37 | 6 | 6 | 11 |
| Verba | 17,613 | 27 | ✅ | 27 | 16 | 23 | 1 | 2 | 39 | 38 |
| daily-pulse | 16,644 | 2 | ✅ | 9 | 20 | 45 | 0 | 2 | 33 | 11 |
| DriftDate | 16,503 | 17 | ✅ | 15 | 10 | 53 | 8 | 1 | 14 | 16 |
| CalcMaster | 15,985 | 12 | ✅ | 10 | 19 | 57 | 0 | 4 | 23 | 8 |
| NexusTransferPay | 15,738 | 6 | — | 29 | 16 | 11 | 0 | 3 | 19 | 4 |
| iMeasure | 14,576 | 8 | ✅ | 2 | 13 | 50 | 14 | 9 | 21 | 4 |
| Uscis-Case | 12,096 | 7 | ✅ | 11 | 10 | 35 | 0 | 1 | 3 | 16 |
| Kinnav | 11,850 | 22 | ✅ | 5 | 9 | 26 | 10 | 8 | 3 | 1 |
| FashionFactory | 11,550 | 40 | ✅ | 0 | 12 | 28 | 58 | 1 | 2 | 14 |
| TripNest | 11,373 | 11 | ✅ | 7 | 21 | 28 | 39 | 1 | 10 | 10 |
| yourtube | 11,280 | 1 | ✅ | 24 | 17 | 28 | 0 | 5 | 31 | 8 |
| HerJourney | 10,219 | 5 | ✅ | 30 | 9 | 39 | 0 | 2 | 19 | 0 |
| radiotune | 9,672 | 7 | ✅ | 9 | 33 | 48 | 8 | 2 | 8 | 5 |
| VirtuBand | 7,818 | 4 | ✅ | 1 | 5 | 25 | 0 | 2 | 6 | 7 |
| BodyQuest | 7,817 | 2 | ✅ | 11 | 5 | 12 | 0 | 3 | 44 | 2 |
| GadgetNest | 4,990 | 7 | ✅ | 0 | 9 | 1 | 0 | 1 | 3 | 0 |
| NewsBoard | 4,944 | 4 | ✅ | 1 | 1 | 8 | 7 | 2 | 3 | 4 |
| MyFinance | 3,317 | 2 | — | 1 | 0 | 2 | 0 | 1 | 0 | 0 |
| AGrammarly | 2,315 | 3 | ✅ | 1 | 3 | 7 | 4 | 0 | 0 | 0 |
| ChefCount | 1,618 | 2 | — | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| WiFiTrail | 962 | 2 | — | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| CarDeal 🐚 | 939 | 3 | ✅ | 1 | 3 | 1 | 0 | 0 | 0 | 0 |
| HomeWise 🐚 | 939 | 2 | ✅ | 1 | 3 | 1 | 0 | 0 | 0 | 0 |
| NearServe 🐚 | 939 | 3 | ✅ | 1 | 3 | 1 | 0 | 0 | 0 | 0 |
| RideZap 🐚 | 939 | 3 | ✅ | 1 | 3 | 1 | 0 | 0 | 0 | 0 |
| portfolio-board 🐚 | 939 | 2 | ✅ | 1 | 3 | 1 | 0 | 0 | 0 | 0 |
| AGCleaner | 902 | 2 | — | 4 | 1 | 1 | 0 | 1 | 0 | 1 |
| RoomCraft | 796 | 2 | — | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| AGRecorder | 553 | 2 | — | 0 | 0 | 5 | 0 | 0 | 0 | 0 |
| MileMaster | 505 | 1 | — | 1 | 0 | 2 | 0 | 0 | 5 | 0 |

🐚 = shared placeholder shell, not a real product yet.

## Order of work

Largest and least-covered first, because those carry the most user-visible
risk per hour spent:

1. **MyHealth** — 44,591 LOC, 3 tests, a11y 0
2. **yourtube** — 11,280 LOC, 1 tests, a11y 0
3. **daily-pulse** — 16,644 LOC, 2 tests, a11y 0
4. **PilotEnRoute** — 39,443 LOC, 10 tests, a11y 0
5. **EventSpark** — 19,364 LOC, 7 tests, a11y 37
6. **NexusTransferPay** — 15,738 LOC, 6 tests, a11y 0
7. **Photriya** — 36,170 LOC, 15 tests, a11y 0
8. **HerJourney** — 10,219 LOC, 5 tests, a11y 0

Then the smaller real apps, then the five shells (which need product
definition, not polish), then the five ports.

