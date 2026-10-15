# Spec: ApexMarketWatch — a market-stress gauge with 36 years of history behind it

Author: product-manager (AI office), 2026-10-12
Project: real-apps (`../plan.md`, criteria 1–7)
Repo: `/Users/spatchava/agl/ApexMarketWatch` (app in `mobile/`)
Base: `main` @ `c37e1aa912ec8530e9917ccf8eddd95cb85b7711` (`git rev-parse HEAD`, `git branch --show-current`, run 2026-10-12)
Baseline: `flutter analyze`: "No issues found! (ran in 130.6s)". `flutter test`: "+336: All tests passed!" (both run 2026-10-12 against the base above).

Other people's uncommitted work is in this repo. Do not touch it: `git status --short` shows modified files under `mobile/fastlane/**` (descriptions, notes.txt, screenshots), `mobile/ios/Podfile.lock`, and new screenshots 04/05. None of the files this spec changes are in that list. If one of them gains someone else's edits before you start, stop and report it.

---

## 1. Problem

**Apple's state.** The app was rejected under 5.6 on 2026-10-08T14:19:57Z (`/Users/spatchava/agl/.dist/rejections.json` → "ApexMarketWatch"): "the app contains features that appear to have been intentionally hidden during the review process." Google Play: PRODUCTION_DRAFT_STAGED.

**What in this binary reads as "hidden" (evidence):**
- A whole Deals tab is compiled in, and the reviewer never sees it. It is gated on a build-time define: `lib/core/env.dart:20` `String.fromEnvironment('API_GATEWAY_URL')`, `lib/features/shell/home_shell.dart:42` `_showDeals = widget.showDeals ?? AppEnv.hasGateway`. The binary also carries the sentence "the Deals tab is not shown in this build" (`lib/core/env.dart:105-107`). `lib/services/deals_gateway_api.dart:15-17` records that the gateway host "does not resolve".
- Four more compile-time switches change what the app does: `FINNHUB_API_KEY` (env.dart:14), `ENABLE_YAHOO` (env.dart:34), `ENABLE_SEC_EDGAR` (env.dart:39), `SEC_USER_AGENT` (env.dart:25). In the binary these produce "No live provider is enabled in this build" (`lib/features/settings/data_sources_screen.dart:55`) and "No Finnhub API key in this build" (`lib/services/finnhub_quote_api.dart:41,69`).
- A "sample data" mode that production never uses: `DataOrigin.sample` / `Sourced.sample` (`lib/core/data_origin.dart:20,52`), and the banner "SAMPLE DATA — NOT LIVE MARKET PRICES … bundled offline dataset" (`lib/widgets/provenance.dart:57-73`). Only `test/support/sample_market_data_source.dart` ever produces sample data. A reviewer who sees those strings, or a second mode, sees a hidden switch.

**Why it reads as a template (4.3 portfolio context; this app was not itself rejected under 4.3):**
- Its icon comes from the generator: `scripts/generate_app_icons.py:64` `"ApexMarketWatch": ("candlestick_chart", "#0D2818", "#2E7D32")`.
- Its splash is the shared one: `ios/Runner/Base.lproj/LaunchScreen.storyboard` shasum `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, the same hash as 37 of 43 apps.
- It uses the shared shell: `AglAdBanner` directly above the Material `NavigationBar` (`home_shell.dart:60,65`), plus an interstitial on every tab switch (`AglAds.onTransition()`, home_shell.dart:72).
- Its look is "near-black plus neon" in dark mode only (`lib/app/app.dart:21` `ThemeMode.dark`), built from Tailwind defaults: `lib/app/theme.dart:22-33` has 10B981, EF4444, F59E0B, 3B82F6, 8B5CF6, 06B6D4, 34D399, F87171, FBBF24, plus slate F1F5F9/94A3B8/64748B. There is no font of its own (`pubspec.yaml` declares none), and every card has 16px "glass" corners.
- It overlaps daily-pulse. The watchlist is seeded with AAPL/MSFT/NVDA/AMZN/TSLA (`lib/services/watchlist_store.dart:16-22`), and the store screenshots show those tickers with "Delayed · Yahoo Finance", which is what daily-pulse shows (`overlap.md` G2).
- It uses web-port jargon: "Market Ingest" (`watchlist_screen.dart:362`, from the web app's "High-Frequency Market Ingest" panel). On 45-day-old filings it labels moves "Buy Alert" / "Sell Alert" (`whales_screen.dart:291-299`).
- The 13F-tracker idea on its own is already widely available on the App Store. An iTunes Search API lookup (`itunes.apple.com/search?term=13F`, run 2026-10-12) returns Whalex: Insider & 13F Tracker (id6770400771), WhaleSignals: 13F Tracker (id6787177894; its description says "TRACK 59 LEGENDARY FUNDS"), Eaves: Hedge Fund Tracker (id6754205255) and 13F Hub (id6755756022). A watchlist plus a 13F feed does not give Apple a distinct product.

**What already works and should be kept (read in full on 2026-10-12):**
- Watchlist with live Yahoo quotes. It persists, supports reorder and swipe-to-delete with undo, and has an empty state (`providers.dart:48-118`, `watchlist_store.dart`).
- Symbol search sheet (`add_symbol_sheet.dart`).
- Ticker detail: range chart from 1D to 5Y, key stats, 52-week bar, max drawdown, and 13F moves in that security (`ticker_detail_screen.dart`).
- 13F whales. It walks SEC EDGAR for real (`sec_edgar_api.dart`), handles amendments, multi-manager rows, PRN rows and the 2023 thousands-to-dollars change, and prices each trade at the filing's implied mark rather than by revaluation (`whale_activity.dart:186-200`). Buy/sell filter.
- Crash Index: a transparent four-term heuristic, with every weight shown (`crash_index_calculator.dart`, `crash_index_screen.dart`).
- Provenance footers, with ages taken from the provider's timestamp.
- There is no fake data in production paths.

The engineering is real. The problems are the hidden surface, the template skin, and a product that has no clear centre.

## 2. User and core job

**User:** a self-directed, long-term US-market investor. They own a handful of stocks or index funds, and they get rattled by "crash" headlines. They do not trade intraday. The question they bring to the app:

> "Is the market actually under unusual stress right now, compared with every bad stretch since 1990? And what did the big funds do last quarter with the stocks I own?"

**Core job:** in under a minute, show today's market-stress reading (the Crash Index) and say how it ranks against history. Then show their own tickers and the latest 13F moves behind that reading. Every number names its source and its age.

**Signature feature: Stress Replay.** The Crash Index's market terms are recomputed on the device for every trading day since 1990, from public daily VIX and S&P 500 closes. The user can:
- see how today ranks ("higher than N% of trading days since 1991"),
- scrub to any date (for example 2008-09-29 or 2020-03-12) and see that day's score with its three inputs,
- list the largest stress peaks the data itself finds.

All of it works offline from a cache on the device, and the formula is on screen.

*Competitor check (iTunes Search/Lookup API, 2026-10-12; descriptions only, the apps themselves were not run):*
- "Fear & Greed Index - VIX" (id6758426458) describes "Trend analysis with history charts (1M / 3M / 6M / 1Y)".
- "Fear and Greed Index Meter" (id1638482661, 484 ratings) describes a fear & greed reading, but its description publishes no formula or weights and mentions no multi-decade history.
- The 13F trackers above (Whalex, WhaleSignals, Eaves) describe no market-stress reading at all.

So the claimed gap is: **a stress reading whose formula is published, whose history covers 1990 to today, and which can be checked day by day, joined to 13F institutional flow.** That claim rests on store descriptions, not on hands-on use. **The competitors' actual behaviour is not verified.**

## 3. Data sources (real only; verified 2026-10-12)

| Data | Source | Proof |
|---|---|---|
| Daily VIX closes since 1990 | `https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?period1=631152000&period2=<now>&interval=1d` (keyless) | curl: HTTP 200, 971,640 bytes, 9,595 rows, 1990-01-02 → 2026-10-12, 331 null closes, last 15.21 |
| Daily S&P 500 closes since 1990 | same, `%5EGSPC` | curl: HTTP 200, 997,737 bytes, 9,262 rows, 1990-01-02 → 2026-10-12, 0 nulls, last 7807.24 |
| Quotes, charts, symbol search | Yahoo chart/search (already in `yahoo_quote_api.dart:35`) | `^VIX range=1y` answered (regularMarketPrice 15.21) |
| 13F filings | `data.sec.gov/submissions/CIK##########.json` + `www.sec.gov/Archives/...` (already in `sec_edgar_api.dart`) | `data.sec.gov/submissions/CIK0001067983.json` answered ("BERKSHIRE HATHAWAY INC"). The archive host was **not re-curled this session** (see Not verified) |
| Watchlist, followed funds, onboarding flag, replay cache | on-device (shared_preferences + one file in app documents) | — |

**Gotcha found while verifying:** `range=max&interval=1d` silently downsamples to monthly bars (VIX returned 442 rows, S&P 169). Use `period1`/`period2`. VIX and S&P rows do not line up one to one (9,595 vs 9,262), and VIX has nulls. Join on calendar date in the exchange's own time zone (`meta.gmtoffset`), and drop dates missing either close.

**Prototype result.** This is a Python reimplementation of the existing three market terms, using the curl data above. VIX weight 0.40 over 10→40, spike 0.20 over 0→50% against a 22-day mean, drawdown 0.25 over 0→20% against a 252-day high, total rescaled by 1/0.85. Warm-up is the first 252 aligned days. Output: 9,262 aligned days; today (2026-10-12, an intraday bar) scores **8.4**, at the **23.1st percentile** of 9,010 scored days. The largest peaks, at least 180 days apart, are 2001-09-17 (100), 2008-09-29 (100), 2020-03-12 (100), 2025-04-08 (98.4), 2011-08-08 (96.9) and 2002-07-23 (95.7). The method finds the known stress episodes from the data alone. These figures are a check for the developer, **not copy for the app**. The app shows whatever it computes at run time.

No API keys, no Supabase, no paid feed, no backend.

## 4. Acceptance criteria

### MUST (what Apple has to see for a real, distinct app)

**M1. One build, nothing hidden (5.6).**
Delete:
- the Deals feature: `features/deals/`, `services/deals_gateway_api.dart`, `models/deal.dart`, `dealsProvider`, `MarketDataSource.fetchDeals`, `HomeShell.showDeals`, `AppEnv.apiGatewayUrl/hasGateway`;
- the Finnhub path: `services/finnhub_quote_api.dart`, `FINNHUB_API_KEY`;
- the `ENABLE_YAHOO` / `ENABLE_SEC_EDGAR` switches;
- the in-app sample mode: `DataOrigin.sample`, `Sourced.sample`, `SampleDataBanner`, `SampleChip`. Test fakes may keep their own type under `test/`.

Make `SEC_USER_AGENT` a plain `const`.

Acceptance:
- (a) `grep -rnE "fromEnvironment" mobile/lib` → 0 hits. Ad unit ids live inside `agl_ads`, which is out of scope.
- (b) `grep -rniE "deal|finnhub|API_GATEWAY|ENABLE_|in this build|this build|sample data|bundled offline|not configured" mobile/lib` → 0 hits, apart from legitimate words that need a written justification.
- (c) In a release iOS build, `strings build/ios/iphoneos/Runner.app/Frameworks/App.framework/App | grep -ciE "this build|deals tab|sample data|bundled offline|finnhub"` → 0. Check the binary, which is what Apple inspects, not just the source.
- (d) Every feature is reachable from the first screen on a fresh install, in every region.

**M2. Signature: Stress Replay.**
- New pure module `lib/services/stress_history.dart`. It takes two daily close series and returns per-day `{date, vix, vixMean22, spx, spxHigh252, drawdownPct, spikePct, score}`. It must use the **same constants** as `CrashIndexCalculator` (import them, do not copy the numbers), with the 13F term excluded and the three market weights rescaled to total 100%.
- New `ReplayScreen`, reached from the home gauge ("See every day since 1990") and from the Stress tab app bar.
  - Range chips 1Y / 5Y / 10Y / All.
  - The line is shaded by risk band.
  - Scrubbing shows the date, the score, and the three inputs for that day.
  - A sentence reads "Today's market-only reading is higher than N% of trading days since <first scored date>."
  - A "Largest readings" list shows peaks the data itself finds, at least 180 days apart, top 10, by date and score only. No editorial event names.
  - A permanent caption: "Market-only history: the 13F flow term is quarterly and is left out of the replay, so the three market terms are rescaled to 100%. Today's full score on the Stress tab includes it."
- Acceptance:
  - Scrubbing to 2020-03-12 shows a High or Severe band, computed live from fetched data.
  - The percentile on screen equals the unit-tested function's output for the same series.
  - The replay renders 9,000+ points without jank: decimate for drawing, keep full data for scrubbing.

**M3. Depth: persistence, offline, export.**
- *Replay cache.* After the first fetch (about 2 MB over two requests), the aligned series is stored in one file in app documents with its fetch date. Later launches fetch only `period1 = last cached date − 7 days` and merge. With no network, the replay renders from cache and shows "Offline · data to <last date>". With no network and no cache, an honest empty state reads "Stress Replay needs one download of daily VIX and S&P 500 history (~2 MB) from Yahoo Finance." with a Retry button.
- *Followed funds.* The user picks which `TrackedFund`s to follow (at least 1, at most 5; the default is the current first 3). The choice persists. The Filings tab and the 13F term use only followed funds. Copy states the rate-limit reason for the cap.
- *Search and filter in Filings.* A text field filters moves by issuer, ticker or fund name. Keep the existing All/Buys/Sells chips and add a per-fund chip row.
- *Share and export.*
  - "Share this reading" on the Stress tab shares plain text through the system share sheet: score, band, the four inputs with observed values, sources and timestamp.
  - "Export CSV" on Replay shares `date,vix,vix_mean_22d,spx,spx_high_252d,drawdown_pct,vix_spike_pct,market_score`.
  - Use `share_plus` (a new dependency; it collects no data, so the privacy label is unchanged).
- Acceptance: kill the app in airplane mode and relaunch. The replay shows cached data with the offline label, and the watchlist and followed funds are intact.

**M4. A home built around the core job (not the shared shell).**
- Three tabs: **Stress** (home) · **Tickers** · **Filings**.
- The Stress home stacks, top to bottom:
  - the live four-term gauge,
  - the percentile sentence from M2,
  - a one-year replay sparkline (tap for Replay),
  - "Your tickers": up to 5 compact rows from the watchlist, with "See all",
  - "Funds last quarter": followed funds' gross buy, gross sell and net, with the quarter pair, linking to Filings.
- The "Market Ingest" card and its name are gone. The S&P 500 / Nasdaq 100 / VIX levels move into the gauge's input rows.
- `AglAdBanner` is **not** in the shell above the tab bar. One banner sits inline in the Filings list after the 10th move card, and none on Stress or Replay. (The interstitial is a founder question, Q2.)
- Acceptance:
  - `grep -n "AglAdBanner" mobile/lib/features/shell/` → 0.
  - A widget test asserts exactly three tab labels.

**M5. Own identity: colour, type, shape, icon, splash.**
- *Palette "Ledger".* Default `ThemeMode.system`. Light: paper `#F6F3EC` surface, ink `#1B1F24` text, seed/primary petrol `#0F4C5C`. Dark: `#0E1A20` surface, `#E9E4D8` text, petrol lifted to `#5FA3B3`. Risk bands: low sage `#4E7D5B`, elevated ochre `#C8962E`, high rust `#B5562B`, severe oxblood `#7A1F2B`. Up `#1E7F4F`, down `#B23A3A`, flat ink at 60%.
  - Acceptance: `grep -rhoiE "10B981|EF4444|F59E0B|3B82F6|8B5CF6|06B6D4|34D399|F87171|FBBF24|F1F5F9|94A3B8|64748B|050508" mobile/lib` → 0.
- *Typography* (revised 2026-10-14, issue #39: IBM Plex stays with AGCleaner only). **Host Grotesk** for UI and **Intel One Mono** for every number (prices, scores, percentages, dates in tables). Host Grotesk keeps the same advance width at every weight, so a figure that turns bold does not shift its row. Intel One Mono was drawn for legibility at small sizes. Bundle the TTFs under `assets/fonts/` (`HostGrotesk[wght].ttf`, one variable file that Flutter drives from FontWeight, and `IntelOneMono-Regular/Medium/SemiBold.ttf`, from `github.com/google/fonts/tree/main/ofl/hostgrotesk` and `…/ofl/intelonemono`), with both copyright notices and the SIL OFL 1.1 in `OFL.txt`, which is also on the licences page (Sources & method). Declare them in `pubspec.yaml`, and do no runtime download. Every `pubspec.yaml` in the portfolio was checked on 2026-10-14: no other app bundles either family. Previously: IBM Plex Sans + Mono (commit 74801e7).
- *Shape.* 4px card corners, hairline 1px rules, flat fills, no glass/blur/gradients. Remove the `glassCard`/`neon*` names.
- *Icon.* Hand-built art: a half-dial gauge whose needle is drawn as a seismograph trace, petrol on paper. It must not come from `generate_app_icons.py`. Ask store-compliance to delete line 64 (`"ApexMarketWatch": ("candlestick_chart", ...)`) so a rerun cannot overwrite the new icon. That file is not in this app's repo. Regenerate every `AppIcon.appiconset` size and the Android mipmaps.
- *Splash.* A new `LaunchScreen.storyboard` with background `#F6F3EC` and the new mark. Android `launch_background.xml` uses the same colour.
  - Acceptance: shasum ≠ `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`.

**M6. Own onboarding (first run only), and no ticker seeding.**
Three cards:
1. "What the Crash Index measures": the live score plus its four inputs in one line each.
2. "Follow funds": the picker from M3.
3. "Add what you own": the symbol search. "Skip" is allowed.

Remove `WatchlistStore.defaultSymbols` seeding. A fresh install starts with an empty watchlist and the existing empty state. Users who already have a stored list keep it, so no migration loses data. Onboarding can be reopened from "How the index works" on the Sources screen.

Acceptance: widget tests cover:
- onboarding shown once,
- skip works,
- a fresh store returns `[]`,
- an existing stored list is preserved.

**M7. Honest, specific copy.**
- "Data sources" becomes **"Sources & method"**. It lists only Yahoo Finance and SEC EDGAR: what each covers, the delay, and the 13F 45-day lag. It shows the Crash Index formula, links to Replay, and keeps the **Privacy choices** row (legal; keep the existing `PrivacyChoicesRow` behaviour). Remove "Active source: …", "Not configured" and "Works without an API key".
- Badges "Buy Alert" / "Sell Alert" become the action label ("Added", "Trimmed", "New position", "Exited").
- The tab title "13F Whale Activity" becomes **"Filings"**, with the screen heading "13F filings: <prev quarter> → <current quarter>".
- No "coming soon", "not connected", "unavailable in this build" or "simulator" text anywhere. Error states keep the existing honest "SEC EDGAR is not responding…" pattern.

**M8. Proven.**
- `flutter analyze` is clean, `flutter test` passes, and new tests cover:
  - `stress_history`: a frozen fixture of **real** closes cut from the 2026-10-12 curl and committed under `test/fixtures/`, including a null-VIX row and a date present in only one series; the score per day against the calculator constants; percentile; peak spacing,
  - cache merge and offline load,
  - followed-funds store,
  - onboarding once,
  - three-tab shell,
  - Filings text filter,
  - CSV header and row format,
  - a `release_sanity_test` that greps `lib/` for the M1 forbidden strings.
- Tests for the Deals and Finnhub code are removed **only together with the code they test** (`test/widget/screens_test.dart` "DealsScreen" group; `test/foldable_layout_test.dart:145,166-172,244,268-272`). The commit message lists each one. No other test is deleted or skipped.
- Launch on the iOS simulator. Screenshot the Stress home, Replay scrubbed to 2020-03-12, Filings, and onboarding card 1, and look at them (no white screen). Commit path-limited and push to `main`.

### SHOULD (if time allows, in this order)

- S1. **New-filing marker.** On launch, compare each followed fund's newest 13F-HR accession with the one stored on the device. When it differs, the Filings tab and the fund chip show "New filing since your last visit (filed <date>)". The data is on-device only, and there are no push notifications.
- S2. **Stress overlay on ticker charts.** On 1Y/5Y ticker charts, shade the dates where the replay was in High or Severe.
- S3. **iOS-native feel.** On iOS, `CupertinoTabBar` and `CupertinoIcons`, and Cupertino page transitions. Material stays on Android.
- S4. **More funds.** Extend `TrackedFund.tracked` (for example Pershing Square, Baupost, Scion), but only with CIKs whose `data.sec.gov/submissions` response the developer has fetched and whose `name` field matches. Record each fund's evidence in a code comment.

## 5. Store impact (proposed; store-compliance applies it later, and nothing here was written to store/ or fastlane/)

**Name.** Founder decision, Q1. Copy below uses "ApexMarketWatch" until decided.

**Subtitle (≤30):** `Market stress, since 1990` (25 chars)

**Play short description (≤80):** `How stressed is the market today? Compare with every day since 1990.` (68 chars)

**Promotional text (≤170):** `Today's Crash Index, ranked against every trading day since 1990 — with the formula on screen and the big funds' latest 13F moves beside it.`

**Description (draft; drops the shared ALL-CAPS skeleton and the house ads paragraph):**
> When the headlines say "crash", check the number instead. ApexMarketWatch scores market-wide stress from 0 to 100 using four public inputs — the VIX level, the VIX against its past month, the S&P 500's fall from its 1-year high, and net selling in the latest SEC 13F filings of the funds you follow — and shows you every input and weight.
>
> Stress Replay recomputes the market part of that score for every trading day since 1990 from daily VIX and S&P 500 closes, so you can see where today ranks, scrub to any date, and find the largest stress peaks yourself. The history is kept on your phone and works offline.
>
> Follow up to five large institutions and see what they added, trimmed, opened and exited between their last two 13F filings, read directly from SEC EDGAR. Filter by fund, by direction, or search a company. Keep a list of the tickers you own, with delayed quotes and charts from Yahoo Finance.
>
> Export the replay as CSV or share a reading with its sources. Every screen says where its numbers came from and how old they are. 13F filings are published up to 45 days after quarter end.
>
> ApexMarketWatch is free with ads from Google AdMob; where the law requires consent, you choose first, and you can change it in Sources & method. It reports public data, does not recommend trades, and does not connect to a broker.

**Keywords:** `crash index,market stress,vix,fear,13f,sec,edgar,hedge funds,s&p 500,drawdown,watchlist`

**Screenshots to retake** (all from live data at capture time; no seeded AAPL/MSFT/TSLA list; iPhone 6.9", iPad 13", Play phone/tablet):
1. Stress home: gauge, percentile sentence, one-year sparkline.
2. Stress Replay: All range, scrubbed to 2020-03-12 with the three inputs visible.
3. Replay "Largest readings" list.
4. Filings: fund chips plus a search term applied.
5. Sources & method, showing the formula.

The current fastlane screenshots carry someone else's uncommitted edits. Coordinate with their owner; do not overwrite them from this workstream.

**Play feature graphic.** Rebuild it from the new icon and wordmark in the Ledger palette. The current one shows the old "AM" monogram.

**Review notes (rewrite for this app only; do not reuse the 2–7 skeleton):**
- Drop the "simulators … a build that cannot start never ships" paragraph. State the real test devices honestly. A physical-device run is a human step and is not verified here.
- State plainly: "This build has no hidden or switchable features. Earlier builds contained an unreachable Deals screen and build-time switches; they have been removed. Every feature is reachable from the first screen without an account, identical in every region."
- Path to the signature feature: "Stress tab → 'See every day since 1990' → drag across the chart."
- First launch downloads about 2 MB of daily history from Yahoo Finance. After that the replay works offline.
- Intended audience, in place of the pasted subtitle: "Self-directed long-term investors who want to check whether current market stress is unusual by historical standards before reacting to headlines."
- External services: Yahoo Finance (chart, search), SEC EDGAR, Google AdMob, Firebase Crashlytics. Remove Finnhub and any gateway.

**Privacy label.** No change needed: it remains ad device ID, advertising data and crash data, all not linked. The new on-device storage and `share_plus` collect nothing. That this label is shared with 3 other apps is correct here, because the practices are the same.

**differentiation (store json):**
- §3 gap: use the competitor paragraph in section 2, keeping its "descriptions only" caveat.
- §6: "Not a feature of HomeWise/MyFinance: those compute personal finances; this measures market-wide stress from public market and SEC data."
- §4 (beta testing) remains a founder item.

## 6. Out of scope

- News feeds and headlines (daily-pulse owns them, `overlap.md` G2).
- Retail deals or coupons: deleted, not deferred.
- Broker linking, trading, portfolios with cost basis, accounts, Supabase, sign-in.
- Push notifications or background fetch.
- Form 4 insider and congressional trades: competitors cover them, and they were not verified here.
- CUSIP→ticker beyond the existing hand-verified map: OpenFIGI and similar were not verified.
- Back-testing claims or predictions. The replay is a description of history, and copy must not claim it predicts anything.
- Localisation beyond English.
- A home-screen widget.

## 7. Not verified

- `www.sec.gov/Archives` and EDGAR's entity search were not re-curled this session. The office's command reviewer refused my second and third SEC requests ("outside the AI office's charter scope"), so I stopped. Only `data.sec.gov/submissions` (Berkshire) was confirmed. The app's existing 13F code and comments cite a Berkshire Q2 2026 filing, but I did not run it today.
- Competitor behaviour is known only from App Store descriptions. WebSearch is disabled in this environment ("Internet mode is not enabled").
- I have not checked whether "Stressline" or any other rename (Q1) is free on either store.
- Physical-device behaviour.
- Whether Apple will accept the resubmission.

## 8. Founder questions (Charter decisions; the office does not take them)

- **Q1 Name.** "MarketWatch" is the name of a Dow Jones financial news site. A listing called "ApexMarketWatch" that shows quotes can read as imitation (4.3 "already widely available"). Keep it, or rename to something centred on the signature, for example "Stressline" or "Crash Index: Market Stress"? Availability not checked. The bundle id is permanent either way (`../../../../CLAUDE.md`, "Bundle ids … are permanent").
- **Q2 Interstitial ads.** Today a full-screen ad can show on tab switches (`home_shell.dart:72` `AglAds.onTransition()`). This spec keeps one inline banner in Filings. Drop the interstitial (less revenue, less template feel), or keep it? This is a money decision (Charter §3).
- **Q3 Deals removed for good.** Confirm the Deals feature is deleted rather than kept for a future gateway. The code comment says the gateway host did not resolve (verified 2026-09-11 per `deals_gateway_api.dart:15-17`; not re-checked today). Keeping it compiled in is the 5.6 problem.
- **Q4 Resubmission.** Replying to Apple and resubmitting stay frozen under the 5.6 hold (MA-043, Charter §1).
- **Q5 Beta testing statement.** differentiation §4 needs a true account of TestFlight testing, which only the founder can give.
