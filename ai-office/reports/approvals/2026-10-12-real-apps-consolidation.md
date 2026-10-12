# Approval: consolidate or retire overlapping apps (Apple 4.3 questions 5 and 6)

Prepared by portfolio-director, 2026-10-12, for the real-apps project
(`projects/real-apps/plan.md`). Full evidence table: `projects/real-apps/overlap.md`.
Charter §8 makes retiring, merging or unpublishing an app a founder decision. D5 and D6
also touch §3 (money) and §4 (accounts), because they depend on paying for a data feed.

- **Decision needed:** approve or reject six portfolio changes, D1 to D6 below. Each one
  merges an app into another or retires it, because two of our apps do the same job, or
  because an app does no public job at all.

- **Why now:** Apple holds 26 apps under 4.3/4.2.6 (`docs/store-holds.json`, mtime
  2026-10-12 13:47). Its questions 5 and 6 ask whether an app belongs to a suite and
  whether it could be a feature of another of our apps. For the apps below, the honest
  answer to Q6 is "yes", and no wording in the reply changes that (MA-041, issue #11).
  Deciding now also stops the office spending real-apps build effort on apps that will be
  merged away.

- **What it unblocks:** truthful Q5 and Q6 answers for the remaining apps. Product-manager
  specs can be written against a final app list. Six fewer listings need template-tell
  work.

## The decisions

| # | Change | Why (evidence, condensed; full citations in overlap.md) | Store state now (`docs/REJECTION_ANALYSIS.md`, 2026-10-12 14:22) |
|---|--------|------------------------------------------------------------|------|
| **D1** | **Merge RideZap into TripNest.** TripNest adds a ride-fare hand-off (Uber/Lyft/Bolt) as the ground leg of a trip. RideZap is retired. | RideZap prices ride, flight and hotel and hands off to providers (`RideZap/mobile/lib/models/travel_mode.dart:3-6`, `travel_provider.dart:5-6`). Without `RIDEZAP_API_BASE_URL` it has no live prices (`lib/core/env.dart:21,37`). TripNest already searches flights, hotels, cars and airport transfers and hands off to partners (`TripNest/mobile/lib/core/engine/travel_engine.dart:26-33`, `partner_links.dart:98-151`). | RideZap: Apple rejected (5.6), Play draft staged. TripNest: Apple rejected (5.6), **Play live**. |
| **D2** | **Merge NewsBoard into daily-pulse.** daily-pulse adds NewsBoard's topic rail, following and hashtag views. NewsBoard is retired. | Both read publisher RSS, BBC included (`NewsBoard/mobile/lib/core/data/feed_sources.dart:51-122`; `daily-pulse/lib/core/services/news_service.dart:23-37`). Both have search and bookmarks. | NewsBoard: Apple rejected (5.6), Play draft. daily-pulse: Apple rejected (4.3), Play draft. |
| **D3** | **Merge NexusTransferPay into CalcMaster.** CalcMaster adds ECB rate history to its currency converter. NexusTransferPay is retired. | Both convert with Frankfurter/ECB (`NexusTransferPay/flutter-mobile-app/lib/core/api_service.dart:372`; `CalcMaster/lib/lib_currency.dart:159`). A default NexusTransferPay build routes only Convert, Rates and Settings (`lib/main.dart:217-219`). Its account screens sit behind the compile flag `NEXUSPAY_ACCOUNTS` (`lib/core/features.dart:20`, `lib/main.dart:198-214`), which is itself a 5.6 ("hidden features") risk. | NexusTransferPay: Apple rejected (4.3), Play draft. CalcMaster: Apple rejected (4.3), **Play live**. |
| **D4** | **Retire portfolio-board from the public stores.** Keep it for internal use (TestFlight internal / web). | Its own listing says it "contains no content other than this one company's portfolio and is not a general project-management tool for other users' projects" (`store/apps/portfolio-board.json`, `differentiation_overrides.2`). | Apple rejected (4.3), Play draft. |
| **D5** | **FashionFactory and GadgetNest: choose one.** (a) Fund a real product-price feed, then merge GadgetNest into FashionFactory as one cross-category price tracker. FashionFactory is the larger base: add-by-link, on-device price alerts, 10,712 vs 5,690 Dart lines. Or (b) retire both. **Recommended: (b), unless you already intend to pay for a feed.** | Neither shows a single product in a release build. FashionFactory: "every fetch fails with PriceFeedNotConnected" (`FashionFactory/lib/data/unconnected_product_repository.dart:1-6`), and its subtitle is "Price comparison, coming soon". GadgetNest: the sample catalog is invented (`GadgetNest/lib/core/engine/catalog.dart:137-160`) and blocked in release (`lib/core/config/app_config.dart:28-47`), and its store copy says "Not yet connected to any retailer". Both fail acceptance criteria 1 and 5 by construction. | FashionFactory: Apple rejected (5.6), Play draft. GadgetNest: Apple rejected (4.3), Play draft. |
| **D6** | **Retire CodeDeal**, unless you fund a promo-code source and backend. | The API base is empty by default and "the client makes no requests at all" (`CodeDeal/mobile/codedeal_app/lib/core/network/trpc_client.dart`, `kDefaultBaseUrl`). The repo has no server (`CodeDeal/src` contains only `gps_integration.ts`). With no code source, the core job cannot work. | Apple rejected (4.3), Play draft. |

**None of the six apps proposed for retirement is live on either store.** All are
Apple-rejected and at most a Play production draft, so no user loses an installed,
published app. The two absorbing apps live on Play (TripNest, CalcMaster) gain features
and lose nothing.

### Not asking you to decide (office work, recorded here so you see it)

These "sharpen" items remove overlapping features inside apps that stay. Removing a
feature is not on the Charter §8 list, so the office will do them through the normal
product-manager → software-developer → qa-reviewer chain:

- ChefCount owns "cook from what you have". GroceryMatch drops its pantry and meal planner
  and owns the shopping trip.
- MyHealth drops its cycle tracker (→ HerJourney), demo food ordering and generated-menu
  vendors, and anatomy screen. BodyQuest drops water and sleep tracking. iMeasure drops its
  unit converter (→ CalcMaster) and pedometer (→ MyHealth).
- iMaps drops its radio screen (→ radiotune). Photriya drops its DALL-E playground
  (→ AGStudio). daily-pulse keeps only a glance line per symbol (charts stay in
  ApexMarketWatch).
- CarDeal must gain a car-specific job beyond loan maths, or it remains a CalcMaster
  duplicate. If it cannot, it comes back to you as a retire decision.

## Exact action

Reply in the GitHub issue, or in chat, with one line per decision, for example:
`D1 yes · D2 yes · D3 yes · D4 yes · D5 b · D6 yes`. A "no" on any item means the office
treats that app as a "sharpen" item and writes its spec to a distinct job.

Once you approve, the office will:
1. Port the absorbed feature into the surviving app (TripNest, daily-pulse, CalcMaster),
   with tests, pushed to main after `flutter analyze` and the tests pass.
2. Prepare, but not perform, the store steps for each retired app: App Store Connect
   "Remove from sale" and Play "Unpublish". These go back to you as a separate checklist,
   because changing availability is store communication (§1) and the 5.6 freeze (MA-043)
   is in force.
3. Keep every retired repo and bundle id. Nothing is deleted. Bundle ids are permanent once
   a store record exists (`agl-manifest/CLAUDE.md`, "Rules that have already cost something").
4. Rewrite the Q5 and Q6 answers in the 4.3 reply drafts (MA-041) for the surviving apps.

## Evidence (checks run, 2026-10-12)

- Read `store/apps/*.json` for all 43 files (name, subtitle, `primary_category`,
  `differentiation`). The PilotEnRoute file exists but PilotEnRoute was not in scope.
- Read the `lib/` file inventory and line counts for each of the 42 in-scope apps, then
  read the specific source lines cited above with `grep -n` and `sed -n`.
- Ran a pairwise comparison of `lib/` relative paths and an md5 pass for byte-identical
  Dart files over 1 KB. Only infrastructure files are byte-identical (`app_env.dart`,
  `crash_reporting.dart`, `supabase_config.dart`). EventSpark and TripNest share 21
  relative paths, the most of any pair, which is a template tell but not a job overlap.
- `docs/store-holds.json` grouped by guideline gives 26 under 4.2.6 and 16 under 5.6.

**Not verified:**
- Nothing was run on a device or simulator, and no IPA was inspected. In particular I have
  not checked whether NexusTransferPay's flagged account screens are compiled into the
  shipped binary.
- I did not re-run `scripts/rejection_report.py`. The store states above are copied from
  its 2026-10-12 14:22 output.
- I have not checked the cost or availability of a product-price feed (D5) or of a
  promo-code source (D6).

## Risks and how to undo

- **Apple may still flag the survivors under 4.3.** Consolidation removes the "feature of
  another app" problem but not template tells. Those are handled by the rest of the
  real-apps plan.
- **Larger survivors:** absorbed features must meet the same acceptance criteria, so no new
  empty shells.
- **Undo:** retiring here means removing the app from sale and unpublishing it, not
  deleting it. An app removed from sale in App Store Connect and an unpublished Play app
  can both be made available again. The repos and bundle ids stay intact, so a merged
  feature can be split back out from git history.
