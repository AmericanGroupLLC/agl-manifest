# Spec v2: portfolio-board → a work portfolio of case studies you can match to a job posting and present offline

Author: product-manager (AI office), 2026-10-14
Project: real-apps (`../plan.md`, criteria 1–7)
Supersedes: `specs/portfolio-board.md` (the internal "docket" spec). Decision: `company/decision-log.md`, row 2026-10-14 "#25 D4". portfolio-board is **not** retired. It is rebuilt as a public product that overlaps none of the other 42 apps. Issue #25's comment (read 2026-10-14 with `gh issue view 25 --comments`) says the same thing: "rebuilt as a public product that overlaps none of the other 42 apps (new spec first)".
Repo: `/Users/spatchava/agl/portfolio-board` (app in `mobile/`). The GitHub repo is private (`gh repo view` → `"isPrivate":true`).
**Permanent identifiers** (`apps.json`, read 2026-10-14): `application_id` and `bundle_id` are both `com.americangroupllc.portfolioboard`, and `version` is `1.0.0+2`. They do not change. Only the display name and the store name may change.
Base: `main` @ `063144d7b7904775a78cbd6ec05cc15129eb8504` (`git rev-parse HEAD`, 2026-10-14).
Baseline: **not re-run for this spec.** The last measured baseline was at `87d5ae0` (old spec, lines 7–9): "No issues found!" and "+244: All tests passed!". The builder takes a fresh `flutter analyze` / `flutter test` baseline at `063144d` before changing anything, and reports it.

**Other people's uncommitted work is in this repo. Do not touch it.** `git status --short` (2026-10-14) shows the same set as on 2026-10-12:
- `mobile/fastlane/**`: both description files, `review_information/notes.txt`, every screenshot, and 4 untracked `05.png`;
- `mobile/ios/Runner.xcodeproj/project.pbxproj`. Its diff is 6 lines, and only the provisioning profile changes (`c09f3297-…` → `7689ddf8-…`).

`mobile/ios/Podfile.lock` is **clean**. The project uses CocoaPods, not SwiftPM: `grep -c FlutterGeneratedPluginSwiftPackage project.pbxproj` → `0`. So adding `share_plus` and `file_picker` changes `Podfile.lock`, which may be committed. Before committing, run `git diff --stat mobile/ios/Runner.xcodeproj/project.pbxproj`. If it shows anything beyond the other person's 6 lines, stop and report it. Never commit that file or `fastlane/**`.

---

## 0. Evidence base

| Fact | Source (read 2026-10-14 unless stated) |
|---|---|
| Apple's state: 2.1 Information Needed (with the 3.2 "specific businesses" note), then a 2.1(a) launch crash (iPhone 17 Pro Max, iOS 27.0), then 4.3(a)/(b) + 4.2.6 | old spec §1 (lines 37–41), from `.dist/rejections.json`. I did not re-read it. `docs/store-holds.json:102` lists portfolio-board. `docs/APPLE_REQUIREMENTS.md:8` lists portfolio-board under "2.1(a) Launches on iOS 27, iPhone and iPad" |
| The app bundles one company's strategy: `assets/roadmap/portfolio.json`, 960 KB | `du -h` |
| 23 Dart files in `lib/`, about 5.8k lines; 13 test files | `find lib test` + `wc -l` |
| Ads today: one shell banner plus an interstitial on tab switches | `lib/app/router.dart:95`, `:104`; `lib/main.dart:26-30` |
| The founder's ad plan already marks this app "Banner keep, Interstitial remove" | `store/admob/ad-units-plan.csv` rows 409/415 (`keep`) and 410/416 (`remove`); `docs/ADMOB_PLAN.md:9` (the "fit per app" decision, 2026-10-14) and `:46` |
| Unused dependencies: `dio`, `cached_network_image`, `shimmer`, `connectivity_plus`, `flutter_secure_storage`. Only `url_launcher` is imported | `grep -rn` on `lib/` (only `widgets/markdown_view.dart:3` imports a network/plugin package) |
| `path_provider` and `sqflite` are already in the pod set, as transitive dependencies | `pubspec.lock:642`, `:831` |
| Dart SDK 3.12.2 (Flutter 3.44.2) | `.flutter-sdk/bin/cache/dart-sdk/version` |
| Packages to add: `pdf` 3.13.1 (Dart ≥3.12), `share_plus` 13.3.1, `file_picker` 13.1.0, `path_provider` 2.1.6 | `https://pub.dev/api/packages/<name>` (curl) |
| Android auto-backup is on: no `allowBackup` attribute in the manifest | `grep` on `android/app/src/main/AndroidManifest.xml` → no match |
| No camera, location or photo permissions | `release_config_test.dart:36-49` guards it; the manifest declares only `INTERNET` and `ACCESS_NETWORK_STATE` |
| The icon is the generator's: `"portfolio-board": ("dashboard", "#37474F", "#78909C")` | `agl-manifest/scripts/generate_app_icons.py:86` |
| The splash is the shared storyboard | `shasum LaunchScreen.storyboard` → `3f6a9b27d80dda327ce7df82d4887e3adbac50e4` |
| Current privacy label: DEVICE_ID and ADVERTISING_DATA (third-party advertising), CRASH_DATA, PRODUCT_INTERACTION, PERFORMANCE_DATA, all not linked | `store/privacy/portfolio-board.json` |
| `status.csv` row 34 records an age rating of `18+`. Why is not recorded | `status.csv:851` |

---

## 1. Choosing the concept

The name has to be credible, the app has to collide with nothing, and it has to work offline with no new backend. I compared five candidates. iTunes figures come from `itunes.apple.com/search` and `/lookup` (keyless; run 2026-10-14). Rating counts are as returned.

| Candidate | Fit with "Portfolio Board" | Collision with our 42 | Market (iTunes, 2026-10-14) | Verdict |
|---|---|---|---|---|
| **A. Work portfolio of written case studies** (job seekers, students, freelancers, people preparing a review) | Strong: "portfolio" of work, "board" of case studies by readiness | **None** (§2) | Brag/career journals exist but are new and small: *The Brag Book* (id6788805722, 3 ratings), *Hype Doc* (id6778119440, 1), *Bloomly* (id6759821648, 16), *I Got Receipts!* (id6803004835, 0, needs Apple Intelligence), *Chronicle – Work Journal* (id6761791840, 0). All are **daily win logs**. Portfolio *makers* are web/visual: *eFolio* (2), *ShowcaseMe* (240), *Behance* (4,376) | **Chosen** |
| B. Creative/visual portfolio (images) | Strong | **Photriya**: its spec deletes its own "Portfolio" screen (`specs/Photriya.md:21,137`). Picking that job up again re-creates a slice Photriya just dropped, and image-first means photo handling (G8 territory) | Behance, Adobe Portfolio, ShowcaseMe, ArtUp (id6444745430) | Rejected |
| C. Student portfolio for schools | Medium | None | Seesaw (100,070), Brightspace Portfolio, spikeview: teacher- or school-run. Under-13 users bring COPPA and Kids-category duties | Rejected (kids and school accounts) |
| D. Collector's board (coins, cards, vinyl) | Weak ("portfolio" of collectibles implies value) | Valuation drifts into finance (ApexMarketWatch, MyFinance), and item photos into photos | Crowded catalog apps | Rejected |
| E. Solo maker's idea board (stages, scoring) | Medium | None | The old spec found it saturated (old spec §1, lines 73–80: Idea Score, Idea Log, Pulse, Kill My Idea, Trello, Notion) | Rejected (4.3(b)) |

**Why A is the strongest.**
1. It reuses the engine this app already has: an offline Markdown renderer, full-text search with verbatim snippets and highlighting, lanes with notes and an append-only history, and a "health" view with measured rules.
2. The name keeps working. An iTunes search for "portfolio board" returns *Moneycontrol* (Finance) first, so the subtitle and category must say "work case studies" plainly (§11).
3. Every competitor found is either a daily-wins log or a web/visual portfolio builder. None advertises our signature (§3): a deterministic, on-device match of your case studies against a pasted job posting, followed by an offline presentation. **That is limited to what their store descriptions say.** I did not install them, so "none of them does X" is **not verified** and must not appear in store copy.

---

## 2. Overlap check against the other 42 apps

Sources: the first line (title) of every file in `specs/`, `overlap.md`, and a keyword grep over `specs/*.md` for `resume|CV|case study|career|job posting|job description|cover letter|linkedin|recruiter|interview|brag|journal|kanban|todo|markdown`. Findings: no spec has a résumé, career-portfolio, job-matching or case-study job. The only "career" hit is PilotEnRoute's BLS pilot-career module, and its own spec deletes it (`specs/PilotEnRoute.md:321`, F1). "Journal" hits are PlantPulse-v2's plant journal only. "Interview" hits are AGRecorder (recording interviews) and Uscis-Case (USCIS interview dates).

| App | Its job (spec title / overlap.md) | Why portfolio-board v2 does not collide |
|---|---|---|
| AeroSwift | aircraft landing nearby + spotter log | no aviation data |
| AGCleaner | contact dedup | no contacts access |
| AGrammarly | replies in your own voice | **Nearest writing neighbour.** v2 generates **no text**: no rewriting, no suggestions, no AI. The user writes every word. Fit check counts shared words only |
| AGRecorder | lecture/meeting recorder with marks | no audio, no microphone |
| AGStudio | prompt-to-picture | no image generation |
| ApexMarketWatch | market-stress gauge, 13F | **Name risk only.** v2 has no money, price, holding or quote field anywhere, and its spec rules out "portfolios with cost basis" (`specs/ApexMarketWatch.md:239`) |
| BodyQuest | body-map learning | – |
| BuddyPlay | two-player games | – |
| CalcMaster | ruled-sheet calculator + ECB rates | no calculation |
| CarDeal | used-car check | – |
| ChefCount | cook from what you have | – |
| CodeDeal | promo-code wallet | – |
| daily-pulse / NewsBoard | news | no feeds |
| DriftDate | dating | no profiles shared, no other users |
| EventSpark | door list for hosts | – |
| FashionFactory | size-and-returns file | – |
| GadgetNest | device security-update dates | – |
| GroceryMatch | shopping trip list | – |
| HerJourney / MyHealth | reproductive / health record | no health data |
| HomeWise | top offer before you tour | – |
| iMaps / Kinnav | driving / walking safety | no location |
| iMeasure | slope-and-fall level | – |
| MileMaster | mileage logbook | – |
| MyCard | wallet copy and loss plan | stores no cards, IDs or documents. Evidence is **links** only |
| MyFinance | hand-kept ledger | **Name risk only.** No money fields; it must never add invoices, rates or earnings |
| NearServe | call around for a local pro | – |
| NexusTransferPay | transfer cost from receipts | – |
| Photriya | colour reader | no camera, no photo editing. Photriya dropped its portfolio screen (`Photriya.md:137`), and v2 is text-first with **no images in MUST** |
| PilotEnRoute | pilot logbook | its career module is being deleted (above) |
| PlantPulse (both specs) | local-network remote / plant journal | – |
| radiotune | radio for language learners | – |
| RideZap (game) | racing game (#46) | – |
| RoomCraft | furniture fit | – |
| TripNest | trip legs | – |
| Uscis-Case (both specs) | immigration case file | different domain. **Naming:** Uscis-Case uses a "Docket" view (`Uscis-Case.md:94`), so v2 must not use "Docket" (the old spec did) |
| Verba | phrasebook | – |
| VirtuBand | songwriter's sketchbook | creative work, but music, not written case studies |
| WiFiTrail | Wi-Fi survey | – |
| yourtube | archival films | – |

**Boundary rules for v2 (so collisions cannot creep in later):**
- No AI text generation, rewriting or "improve my bullet" (AGrammarly).
- No money fields (ApexMarketWatch, MyFinance, CalcMaster).
- No photo capture, editing or grading (Photriya, AGStudio).
- No audio (AGRecorder, VirtuBand).
- No document or ID storage (MyCard).
- No job search, listings or applying through the app. v2 never fetches postings; the user pastes one.

**Apple Q5/Q6 answer this enables:** "Not part of a suite. No other app of ours stores or presents a person's work history." This is true once M1 removes the bundled company content.

---

## 3. User, core job, signature, competitors

**User.** Anyone who has to *show* work they did, typically one of:
- a job seeker before an interview;
- a student applying for an internship or a programme;
- a freelancer pitching a client;
- an employee writing a self-review.

They have done the work, but it is scattered and undocumented. They need it written up once, as a few strong case studies, and then reused many times.

**Core job.** Write each project once as a case study (context → what I did → outcome, plus skills and evidence links). Keep the set on a board by readiness. When an opportunity comes, pick and order the right ones, then present or export them, entirely on the phone and offline.

**Signature feature: Fit check.** Paste a job posting or a client brief. The app shows, deterministically and on the device:
1. **Ranked evidence:** your case studies ranked by how many of the posting's terms they contain. Matched terms appear as chips, with verbatim snippets showing where each match sits in your text.
2. **Asked for, no evidence yet:** posting terms that none of your case studies mention.
3. **Save as pack:** the top matches, reorderable and labelled (for example "Acme · Product designer"). A pack is presented full-screen (Present mode) or exported as PDF or Markdown.

What it is **not**: it is not AI, and it does not judge quality or write anything. The screen says exactly this: "Fit check counts words that appear in both the posting and your case studies. It doesn't judge quality, and it sends nothing anywhere."

**Positioning against the competitors found (§1):** they capture daily wins (Brag Book, Hype Doc, Bloomly, I Got Receipts!, Chronicle) or build a web page (eFolio, Behance). Portfolio Board is for the moment of use: which three projects to show *this* interviewer, and showing them well with no signal. **Store copy must describe what we do and must not claim what others lack.**

---

## 4. Architecture and data

- **Offline-first, on-device only. No backend.** The existing Supabase project `smvvjivvlprjhzhoizym` is **not used**, and no tables are needed. Reasons:
  - there is no account, so 5.1.1(v) account deletion does not apply;
  - there is no sharing to other users, so 1.2 UGC does not apply (`docs/APPLE_REQUIREMENTS.md`: the 1.2 and 5.1.1(v) rows are per-app);
  - it removes a production-data dependency.
  Cross-device sync is out of scope (§9). If it is ever proposed, it gets its own spec with RLS tables and a founder decision.
- **No network calls by the app's own code.** The only network traffic comes from Firebase (crash, performance, analytics), from AdMob (one banner), and from links the user taps (opened in the system browser via `url_launcher`).
- **Storage.** JSON documents under `getApplicationSupportDirectory()/portfolio/`, using `path_provider`, which becomes a direct dependency (it is already in the lock):
  - `cases.v1.json`: `{"format":"portfolio-board.cases","version":1,"cases":[CaseStudy…]}`
  - `lanes.v1.jsonl`: an append-only history of lane moves (`LaneChange`), one JSON per line, capped at 5,000 lines with the oldest dropped first. This is the same rule as `StageStore.maxHistory`, `stage_store.dart:25-27,84-86`.
  - `packs.v1.json`: `{"format":"portfolio-board.packs","version":1,"packs":[Pack…]}`
  - `profile.v1.json`: the optional name, headline, email and website used **only** in export headers.
  - `shared_preferences` holds small flags only: `pb.onboarded.v1`, `pb.lastBackupAt.v1` and `pb.pdfPaper.v1`.
- **Writes are atomic:** write `<file>.tmp`, flush, then rename.
- **A corrupt file is never overwritten.** On a parse failure the store renames the file to `<file>.corrupt-<epochms>`, loads empty, and the Board shows a persistent banner: "We couldn't read your saved portfolio. The file was kept. Export it from Settings › Backup." That is a deliberate change from today's "corrupt degrades to empty" (`stage_store.dart:38-40`). Degrading to empty would be fine for overrides, but here the next save would destroy the user's work.
- **Models** (`lib/models/`):
  - `CaseStudy`: `id` (a 128-bit hex from `Random.secure()`), `title` (1–80), `role` (≤80), `org` (≤80, optional), `startedOn` / `endedOn` (`YYYY-MM`, nullable; a null `endedOn` means "ongoing"), `context`, `actions`, `outcome` (Markdown, ≤20,000 chars each), `skills` (≤20 tags, each 1–40 chars, trimmed, case-insensitively unique), `evidence` (≤10 `{label ≤60, url}`, `https` only), `lane`, `createdAt`, `updatedAt`.
  - `CaseLane`: `draft`, `ready`, `featured`, `archived`.
  - `LaneChange`: `caseId`, `from`, `to`, `at`, `note?`. Same shape and JSON contract as `StageChange` (`models/stage.dart:83-126`).
  - `Pack`: `id`, `label` (1–80), `postingText` (≤20,000), `caseIds` (ordered, 1–12), `createdAt`, `note?` (≤500).
  - Limits: 1,000 case studies, 200 packs. Reaching a limit shows an inline message saying so. Nothing is silently dropped.
- **Backup.** Settings › Backup › Export shares `portfolio-board-backup-YYYY-MM-DD.json` (`{"format":"portfolio-board.backup","version":1,"cases":…,"lanes":…,"packs":…,"profile":…}`) through `share_plus`. Restore uses `file_picker`: it validates `format` and `version`, shows a summary ("12 case studies, 3 packs. Replace what's on this phone?"), and on confirm replaces everything atomically. A malformed file is rejected with a message, and nothing changes.
- **Analytics and crash hygiene (5.6 and privacy):**
  - Keep `AglCrash.init` and `AglInsights.init` (`main.dart:18,22`).
  - Add **no** custom analytics events. Call **no** `AglInsights.flag/setting/number` (these are Remote Config reads, which would be remote switches). Call **no** `setUserId`.
  - `AglCrash.log(...)` may take constant strings only. User text must never reach Firebase.
  - Enforced by a test (M11).

---

## 5. Reuse and delete (file:line at `063144d`)

### Reuse (adapt, keep the tests' intent)

| What | Where | Becomes |
|---|---|---|
| Markdown parser (headings, lists with checkboxes, tables, quotes, code, inline spans), with no package dependency | `lib/core/markdown/markdown_parser.dart:136` (`parseMarkdown`), `:271` (`parseInline`), `:1-15` (scope note) | Renders case-study sections and the editor's Preview. Keep `test/markdown_parser_test.dart` (23 tests) as is |
| Markdown renderer with search highlighting and link handling | `lib/widgets/markdown_view.dart:15-57` (`MarkdownView`, `highlight`, `onLink`), `:441-470` (`_RichSpans`, which disposes its recognizers) | Case-study reader, editor preview, Present mode |
| External-link test | `lib/services/doc_links.dart:5` (`isExternalLink`) | Validates evidence links. Delete `resolveDocLink` (`:21`), which is roadmap-relative |
| Search with verbatim snippets, occurrence counts and stable ranking | `lib/services/portfolio_query.dart:103-177` (`searchPortfolio`), `:247-257` (`_count`), `:259-281` (`_snippet`); the filter value type `:9-65` | `case_query.dart`: query plus facets lane / skill / year / strength. `_count` and `_snippet` move into `text_match.dart` and are shared with Fit check (with word-boundary matching added) |
| Lane store pattern: append-only log, cap, null on a no-op move, trimmed note | `lib/services/stage_store.dart:58-91` | The `lanes.v1.jsonl` writer. The rules stay: same-lane move → null; empty note → no note; the cap drops the oldest first |
| Move sheet: optional note, never pre-filled | `lib/features/project/stage_sheet.dart:9-13,14-60` | "Move to lane" sheet |
| Stage enum shape (id, label, blurb, colour, `fromId` fallback) | `lib/models/stage.dart:16-79` | `CaseLane`. An unknown id falls back to `draft` |
| Riverpod wiring: prefs override, injectable `now`, a joined board provider | `lib/core/providers.dart:16-34`, `:122-152` | `portfolioStoreProvider`, `nowProvider`, `boardProvider`, `searchResultsProvider`, `checkupProvider`, `fitCheckProvider` |
| Health computation: one pass, no logic in widgets, worst first, staleness, single-member flag | `lib/services/portfolio_health.dart:58-130`, `:72-80` (below-full ordering), `:82-95` (thinnest first), `:98-111` (untouched longest), `:146-149` (`singleProject`) | `portfolio_checkup.dart` (Checkup tab, M6) |
| "Measured rule, not verdict" | `lib/models/portfolio.dart:5-24` (`SpecDepth`), `:349-384` (`DepthRule.explanation`) | `CaseStrength` with its rule shown on screen (M3) |
| Widgets: stage chip, stat tile, distribution bar, card, section title, load failure | `lib/widgets/portfolio_widgets.dart:37`, `:189`, `:252`, `:294`, `:450`, `:499` | Restyled for M9; same semantics |
| Facet sheet and filter chips, labelled for screen readers | `lib/features/browse/browse_screen.dart:134-360` | Search tab facets |
| Reader with highlight-from-search | `lib/features/document/document_screen.dart:14-15,69` | Case-study reader opened from a search hit |
| UMP "Privacy choices" tile (still required while a banner exists) | `lib/features/settings/settings_screen.dart:107-152` | Kept as is |
| Shell banner placement rules (in layout flow, never over content) | `lib/app/router.dart:88-97` | The banner moves to the end of the Board scroll only (M10) |
| English-only declaration | `lib/app/app.dart:8-16` | Kept. Fit check's stopword list is English, and the UI says so |
| Tests whose intent carries over | `test/release_sanity_test.dart` (7, keep), `test/release_config_test.dart` (languages and permissions kept; the font test changes to Bitter and Sora), `test/i18n_test.dart` (3, keep), `test/accessibility_test.dart:114-141` ("no silent controls" sweep, re-pointed at the new screens), `test/foldable_layout_test.dart:44-60,188-220` (no overflow, folded sheets, re-pointed), `test/stage_tracking_test.dart` (its `StageStore` cases become lane-store cases), `test/portfolio_query_test.dart` (snippet and count cases kept, record cases replaced), `test/ads_placement_test.dart:26-61` (PrivacyChoicesTile, keep) | – |

### Delete

- `assets/roadmap/portfolio.json` (960 KB of company strategy) and the `assets/roadmap/` entry in `pubspec.yaml`.
- `tool/build_roadmap_asset.dart` (repo-root `tool/`). If deleting it breaks nothing outside `mobile/`, delete it; otherwise leave it and say so. Do **not** touch the repo-root `roadmap/`, `PORTFOLIO.md` or `mobile-rn/`; that is a founder question (§14).
- `test/roadmap_asset_test.dart` (25 tests), `test/doc_links_test.dart` (`resolveDocLink` cases only; keep `isExternalLink` cases), `test/portfolio_health_test.dart` (replaced by checkup tests). List each deleted test file in the commit message as "deleted because the feature was deleted", not as a fix to go green.
- `lib/models/portfolio.dart` (all roadmap types: `ProjectRecord`, `ProjectPriority`, `Tier1Row`, `GreenlightGate`, `GateCriterion`, `CategorySummary`, `AssetProvenance`, `PortfolioData`, `RoadmapDoc`), `lib/models/project_view.dart`, `lib/services/roadmap_repository.dart`.
- Screens and widgets: `features/portfolio/portfolio_screen.dart`, `features/project/project_screen.dart` (`_PriorityCard`, `_GateCard`, `_FactsCard`, LOIs, tiers), `features/health/health_screen.dart` (`_GatePanel` and tier/category panels), `_Provenance` in settings (`settings_screen.dart:29` "What is bundled in this build.", and the `_Provenance` class), `DepthBadge` and `TierChip` (`portfolio_widgets.dart:108,151`).
- Ads: the interstitial call `AglAds.onTransition()` (`router.dart:104`) and the shell-level `AglAdBanner` (`router.dart:95`). One banner is re-added in M10.
- Dependencies: `dio`, `cached_network_image`, `shimmer`, `connectivity_plus`, `flutter_secure_storage`, `google_fonts`, and `assets/google_fonts/` (Inter). Removing `cached_network_image` drops `sqflite` from the pods. That is fine, because v2 uses JSON files. Keep `path_provider` as a direct dependency.
- The `pubspec.yaml` `description:` text about the AGL Stage-1/Stage-2 portfolio, and the "# Desktop platforms" leftovers.

---

## 6. MUST

Each item ends with **Done when**: a check anyone can repeat. Everything must pass on a **fresh install** with no data, because there is never sample content.

### M1. Remove the company content and every roadmap concept
- Apply §5 Delete.
- **Done when:**
  - `grep -rn -i -E "roadmap|tier-?1|greenlight|LOI|stage-1|stage-2|PORTFOLIO\.md|American Group" mobile/lib mobile/test` → no match outside licence or attribution strings;
  - `ls mobile/assets/roadmap` → no such directory;
  - the release AAB and IPA contain no `portfolio.json`: `unzip -l <aab> | grep -c portfolio.json` → `0`, and the same on the `.app` inside the IPA.

### M2. Case studies: create, read, edit, autosave
- **New case study** (FAB on Board): title is required. The rest is optional.
- **Editor** fields:
  - title, role, org (optional), start and end month (or "Ongoing");
  - three Markdown sections with a Write/Preview toggle (Preview = `MarkdownView`):
    - **Context**: hint "What was the situation, and what were you asked to do?"
    - **What I did**: hint "Your actions, decisions and trade-offs. Use 'I', not 'we'."
    - **Outcome**: hint "What changed? Numbers if you have them: time saved, users, revenue, grades."
    Hints are placeholder text, never saved content.
  - **Skills**: chip input that autocompletes from the user's existing tags.
  - **Evidence links**: label plus URL. URLs are `https://` only, validated with `Uri.tryParse` + `isExternalLink`. Anything else gets an inline error.
- **Autosave:** debounced 1 s, and also on `AppLifecycleState.paused`. A small "Saved" status appears.
- **Delete:** confirmation with the title, then a 5-second Undo SnackBar.
- **Reader:**
  - shows sections in order and hides empty ones;
  - evidence links open in the system browser (`url_launcher`, external application);
  - shows the lane chip and a **History** list (lane moves with notes, newest first).
- **Done when** these pass:
  - unit tests: model JSON round-trip; every limit in §4 enforced with a message; a non-https URL is rejected; `startedOn` after `endedOn` is rejected;
  - store tests: atomic write (a leftover `.tmp` is ignored on load); a corrupt file is renamed to `.corrupt-<ms>` and never overwritten, and the banner is shown;
  - widget test: create → type → kill/restore the widget tree → the text is still there.

### M3. Board and lanes (home)
- **Board layout**, top to bottom:
  1. a lane distribution bar (`StageDistributionBar`), tappable per lane;
  2. **Featured**: a horizontal row of cards;
  3. **Ready**;
  4. **Draft**;
  5. **Archived**: one collapsed row ("4 archived"), expandable.
- **Each card shows:** title, role · org, date range, top 3 skills, and the **strength** "4 of 6 checks".
- **Move to lane:** the sheet with an optional note (reused from `stage_sheet.dart`). The move is recorded in `lanes.v1.jsonl`.
- **CaseStrength**: 6 measured checks, never shown as a percentage. The rule is visible through "How is this measured?":
  1. Context ≥ 40 words;
  2. What I did ≥ 60 words;
  3. Outcome ≥ 20 words;
  4. Outcome contains at least one digit. The rule text says: "checks for a number, not whether it is meaningful";
  5. ≥ 1 skill;
  6. ≥ 1 evidence link.
  The label is "Strong" (6), "Solid" (4–5) or "Sketch" (0–3).
- **Empty Board** (fresh install): "No case studies yet. Start with the project you'd most like to be asked about." with the button "Write a case study". Nothing else is shown, no sample cards.
- **Done when:**
  - unit tests: strength for boundary word counts (39/40, 59/60, 19/20), digit detection, the label bands; a lane move to the same lane → null; a note is trimmed; an empty note is stored as none; the history cap drops the oldest;
  - widget tests: the empty state; ordering Featured → Ready → Draft; Archived collapsed; the move sheet records a note.

### M4. Search
- **Search tab:**
  - a query field;
  - facets: lane, skill, year (from `startedOn`/`endedOn`) and strength label;
  - results ranked: title/role match first, then occurrences, then `updatedAt` (rule adapted from `portfolio_query.dart:162-175`);
  - each hit shows per-section matches ("Outcome · 3") with a verbatim snippet;
  - tapping opens the reader with the term highlighted.
- Archived case studies are included only when the Archived facet is on.
- **No results:** "Nothing matches 'X'." plus a "Clear filters" button when facets are active.
- **Done when:** unit tests cover ranking ties, facet combinations, snippet trimming at word boundaries, and pipes flattened (existing `_snippet` cases). A widget test covers a hit opening the reader with the highlight.

### M5. Signature: Fit check and packs
- New pure function `FitResult fitCheck(String posting, List<CaseStudy> cases, {FitOptions options})` in `lib/services/fit_check.dart`.
- **Inputs used:** non-archived case studies.
- **Algorithm:**
  1. **Normalise:** lowercase. Keep `+ # . /` inside tokens, so `c++`, `c#`, `node.js` and `ci/cd` survive. Collapse whitespace.
  2. **Posting terms:**
     - (a) every user skill tag that occurs in the posting as a whole word or phrase;
     - (b) unigrams and bigrams that are not in `assets/fitcheck/stopwords_en.txt`, are at least 2 characters long and are not pure numbers, and that occur ≥ 2 times **or** sit on a bulleted line (`-`, `*`, `•`, `1.`). Keep the top 25 by count, with ties broken by first occurrence.
     - The stopword list is **written by us in this repo** (common English function words plus posting boilerplate such as "experience", "ability", "team", "years", "role", "including", "strong", "work"). No third-party list, so there is no licence question.
  3. **Per case study:** a term matches if it occurs as a whole word in title, role, skills, context, actions or outcome. Score = 3 × matched skill tags + 1 × other matched terms. The weights are shown on screen.
  4. **Rank** by score, then lane (featured > ready > draft), then `updatedAt`. Case studies with score 0 go under "No overlap".
  5. **Gaps:** posting terms matched by no case study, in posting order.
- **Fit check tab screens:**
  - **Paste:** a multi-line field; Paste from clipboard; Clear.
  - **Results:** ranked cards with matched-term chips and up to 2 verbatim snippets each (reusing `_snippet`), then "Asked for, no evidence yet" (chips), and the honesty line from §3.
- **Guards:**
  - a posting under 30 words → "Paste the whole posting (at least 30 words) for a useful check."
  - zero non-archived case studies → "Write a case study first. Fit check compares the posting with your own work."
- **Save as pack:** the default selection is every case with score > 0 (max 6). The user can reorder by dragging, untick cases, add a label (required) and a note. The posting text is saved with the pack, so the check can be re-run later.
- **Packs list** (in the Fit check tab, under "Saved packs"): label, date and case count. Open → the pack detail with **Present**, **Export** and **Re-run check**.
- **Done when:**
  - exact-output unit tests on fixed inputs: skill-tag matching; bigram extraction; bullet-line inclusion; stopword exclusion; `c++`, `c#` and `node.js` kept; whole-word matching (`java` must not match `javascript`); ranking ties; the gap list in posting order; the 30-word guard;
  - a performance test: 1,000 case studies × a 3,000-word posting completes in < 500 ms on the test VM (measured with a `Stopwatch` in the test; report the figure);
  - widget tests: paste → results → save pack → the pack appears in the list after a widget-tree restart.

### M6. Checkup (reuses the health engine)
- **Checkup tab, computed in one pass** (`PortfolioCheckup.compute`):
  - lane spread;
  - **below Strong**, worst first, each with the checks it misses ("No evidence link", "Outcome has no number");
  - **skills coverage**: each skill with its count of Ready + Featured case studies, thinnest first. Skills with exactly one example are flagged "single example";
  - **untouched longest**: days since `updatedAt`, with `now` injected;
  - packs: count and the newest.
- Empty states for each panel. Example: "Every case study passes all 6 checks." is a real answer and is shown as one.
- **Done when:** unit tests on a fixed set (counts, orderings, the single-example flag, days with an injected `now`) pass, and widget tests show each empty state.

### M7. Present mode
- Entry points: a pack (in pack order) or the Featured lane (Board → "Present featured").
- **Layout:** a full-screen `PageView`, one case study per page. Large type (Bitter). Sections in order. Page indicator "2 of 5". Tap the edges or swipe to move.
- **Chrome and orientation:** no app chrome, **no ads**. Landscape is allowed **only** in Present mode (set preferred orientations on enter and restore portrait on exit; the app is portrait-only, `main.dart:38-41`).
- Evidence links open in the browser only after a confirmation sheet ("Open link in browser?"), so a stray tap in front of an interviewer does not leave the app.
- Works in flight mode.
- **Done when:** widget tests show pages in pack order; the indicator text; no `AglAdBanner` in the tree; orientations restored on pop (verified through a fake `SystemChrome` channel log).

### M8. Export
- **Profile** (Settings › Your details, all optional): name, headline, email, website. Used only in export headers. Stored in `profile.v1.json`.
- **Copy as Markdown** (Clipboard, no plugin) for one case study, a pack, or all Ready + Featured. Format:
  - `# <name or "Portfolio">`, then the headline line;
  - then per case study: `## <title>` / `*<role> · <org> · <MMM YYYY>–<MMM YYYY|present>*` / `### Context` … `### What I did` … `### Outcome` … / `**Skills:** a, b, c` / `**Evidence:**` list of `[label](url)`.
  - Empty sections are omitted, never printed as headings with nothing under them.
  - Markdown control characters in titles are escaped.
- **Share PDF** (`pdf` package to build it, `share_plus` to share it):
  - the same structure as the Markdown, set in the bundled Bitter and Sora;
  - Letter for an `en_US` locale, A4 otherwise, with an override in Settings;
  - page numbers;
  - links are clickable PDF annotations;
  - the file name is `<slug-of-label-or-portfolio>-YYYY-MM-DD.pdf`.
- **Done when:**
  - an exact-string unit test for the Markdown of a fixed pack (including escaping and omitted empty sections);
  - a PDF unit test: page count > 0, the fonts are embedded, the text extracted through `pdf`'s document parser contains each title, and link annotations are present for each evidence URL;
  - a widget test: Copy puts the text on the clipboard (mocked `SystemChannels.platform`);
  - Share is called with a `.pdf` `XFile` (fake `SharePlatform`).

### M9. Own identity: "index cards on a drafting board"
- **Colour (light):**
  - paper `#F7F4EC`, card `#FFFFFF`, rule `#DDD8CB`;
  - ink `#1D1D22`, secondary ink `#5A5867`;
  - primary / seed **cobalt ink `#2A3F9D`**;
  - accent **marker coral `#D9573B`** (Featured, primary actions in Present).
- **Colour (dark):** background `#15161C`, card `#1F2029`, ink `#ECEAF2`, primary `#9DAAF2`, coral `#F2A58F`.
- **Lane colours:** Draft graphite `#8C8A99`, Ready cobalt `#2A3F9D`, Featured coral `#D9573B`, Archived stone `#A39A86`. Each chip keeps its text label, so colour is never the only signal.
- **Collision check:** I grepped every Dart file under `/Users/spatchava/agl` (excluding build, `.dart_tool`, SDK and pub-cache) and every spec for all 14 hexes. All returned 0, except my first green choice, `#2E7D5B` (DriftDate, EventSpark, GadgetNest), which I dropped.
- **Type:**
  - **Bitter** (Sol Matas, OFL; `Bitter[wght].ttf`, `Bitter-Italic[wght].ttf`) for case-study text and headings;
  - **Sora** (Barnbrook/Moncada, OFL; `Sora[wght].ttf`) for UI chrome and numbers.
  - Verified on 2026-10-14: `raw.githubusercontent.com/google/fonts/main/ofl/{bitter,sora}/OFL.txt` → HTTP 200, and the METADATA filenames are as listed.
  - No app pubspec, Dart file or spec uses either. (The old spec's Spectral and Archivo are now taken: Spectral by `NewsBoard/mobile/pubspec.yaml`, Archivo by `Photriya/pubspec.yaml`.)
  - Bundle both under `assets/fonts/` with their `OFL.txt`, registered in `LicenseRegistry`. Remove Inter and `google_fonts`.
- **Shape:** cards are index cards: 2 px radius, a 4 px left rule in the lane colour, and a hairline `#DDD8CB` border. No 12/16 px pills. The reader uses a faint ruled-line background (1 px `#DDD8CB` at 28 px line pitch) behind section headings only.
- **Navigation:**
  - four tabs: **Board / Search / Fit check / Checkup**; Settings is a gear on the Board app bar;
  - iOS: `CupertinoTabBar` with `CupertinoIcons` (`square_stack_3d_up`, `search`, `scope`, `checkmark_seal`);
  - Android: `NavigationBar` with outlined Material symbols;
  - identical features on both, chosen by `defaultTargetPlatform`.
- **Icon:** a new 1024 px vector master, **not** from `generate_app_icons.py`: a white index card tilted 6°, three cobalt rules, and a coral corner tab, on cobalt `#2A3F9D`. Write it into the iOS `AppIcon.appiconset` (no alpha) and the Android adaptive icon. Remove the `"portfolio-board"` row at `agl-manifest/scripts/generate_app_icons.py:86`, so a regeneration cannot overwrite the icon.
- **Splash:** a new `LaunchScreen.storyboard` on `#F7F4EC` with the card mark (96 pt) centred. Android `launch_background.xml` uses the same colour and mark.
- **Onboarding** (once; `pb.onboarded.v1`):
  - one screen titled "Your work, written so it can be shown.";
  - three lines: "Write each project once as a case study." · "Paste a job posting to see which ones fit." · "Present or export them, offline. Nothing leaves your phone.";
  - buttons "Write my first case study" and "Not now";
  - no "Get started" and no carousel.
- **Done when:**
  - `grep -rhoiE "B45309|6B7280|16A34A|9F1239|E5E7EB|DC2626|1565C0|0D47A1|F8F9FA|1A1A2E" mobile/lib` → 0;
  - `grep -rn "GoogleFonts\|google_fonts\|Inter" mobile/lib mobile/pubspec.yaml` → 0;
  - `shasum LaunchScreen.storyboard` ≠ `3f6a9b27…`;
  - the `generate_app_icons.py` row is removed;
  - widget tests: onboarding shows once; `CupertinoTabBar` renders under `debugDefaultTargetPlatformOverride = iOS`; the theme exposes the hexes above (identity test).

### M10. Ads: one banner, fitted to the app
- Exactly **one** `AglAdBanner`, as the **last item of the Board scroll**, in layout flow. This matches the "fit per app" plan (`ad-units-plan.csv` rows 409/415 `keep`) and the EventSpark precedent of one Home banner (decision log 2026-10-14, #40).
- No banner on Search, Fit check, Checkup, the reader, the editor, Present, export previews, onboarding or Settings. **No interstitial**: delete `AglAds.onTransition()`.
- Keep `AglAds.configure/initialize` (`main.dart:26-30`) and the `PrivacyChoicesTile`.
- **Done when:** `test/ads_placement_test.dart` is rewritten. It asserts:
  - exactly one `AglAdBanner` when the Board tab is pumped with ≥ 1 case study and scrolled to the end;
  - zero on every other route, Present included;
  - `grep -rn "onTransition" mobile/lib` → 0.
  The three `PrivacyChoicesTile` tests (`:26-61`) stay. The rewrite is named in the commit message.

### M11. Privacy, permissions and honesty guards
- **Settings › What leaves this phone:** "Your case studies, packs, pasted postings and details stay on this phone. They leave only when you export or share them. The app sends anonymous crash reports, performance data and usage statistics to Google Firebase, and shows one Google AdMob banner on the Board." It must match §10 exactly.
- **Settings › Privacy policy:** a link to `https://www.americangroup.ai/policy/portfolio-board/` (the URL in `status.csv:851`). The page text is legal (Charter §6), so it is drafted for the founder (§14).
- **Settings › Reset everything:** a confirmation dialog stating the counts ("Delete 12 case studies and 3 packs from this phone?"). It deletes the files and flags.
- **No new permissions:**
  - iOS: no usage-description strings. `file_picker` with `FileType.custom(['json'])` uses the document picker, which needs none. The builder confirms this in the built `Info.plist` and reports it.
  - Android: `INTERNET` and `ACCESS_NETWORK_STATE` only. The merged-manifest check confirms no `READ_EXTERNAL_STORAGE` or `READ_MEDIA_*`.
- **Done when** a new `test/honesty_guard_test.dart` (static, reads sources) passes:
  - no `AglInsights.logEvent|flag|setting|number|setUserId` in `lib/`;
  - every `AglCrash.log(` argument is a string literal;
  - no `http://` or `https://` literal in `lib/` except the policy URL, the support URL and the licence attributions;
  - no string `demo`, `sample`, `lorem`, `example.com` or `John` in `lib/` or `assets/`.
  Also, `release_config_test.dart` permissions tests stay green.

### M12. Proven
- `flutter analyze` → "No issues found!". `flutter test` → all pass. The count is reported against the fresh `063144d` baseline, with deleted test files listed by name and reason (M1, M10).
- `integration_test/store_screenshots_test.dart` is rewritten for the new flow (§11 screenshots), or the commit says it was not.
- **Look at it** (memory rule: green tests missed a white screen):
  - a release build: `flutter build ios --release --no-codesign` and `flutter build appbundle --release`;
  - install and launch on an **iOS 27 iPhone 17 Pro Max simulator**, an **iPad 13-inch simulator** and an **Android emulator** (`scripts/sim_install.py portfolio-board`, pinned with `--android-serial`);
  - screenshot: onboarding, empty Board, editor (Write and Preview), Board with lanes, Search hit, Fit check results, pack, Present (portrait and landscape), Checkup, Settings, dark mode, and text scale 2.0 with no overflow;
  - look at each screenshot.
  This closes the 2.1(a) launch item only for simulators. **A physical device stays "not verified"** until a human runs it (Apple also asks for a screen recording on a physical device: `APPLE_REQUIREMENTS.md`, row "2.1 Screen recording").
- Re-run `python3 scripts/store_policy_audit.py portfolio-board`, `python3 scripts/apple_requirements.py` and `python3 scripts/testflight/privacy_scan.py` on the new IPA. Quote the counts.
- Commit path-limited: `git add mobile/lib mobile/test mobile/integration_test mobile/assets mobile/pubspec.yaml mobile/pubspec.lock mobile/ios/Podfile.lock mobile/ios/Runner/Info.plist mobile/ios/Runner/Base.lproj mobile/ios/Runner/Assets.xcassets mobile/ios/Runner/PrivacyInfo.xcprivacy mobile/android/app/src/main`. Never `fastlane/**`, never `project.pbxproj`, never `git add -A`. No `dart format`. Push to `main`.

---

## 7. Acceptance tests (end to end, fresh install, flight mode unless stated)

1. **AT-1 First run.** Launch → onboarding → "Not now" → empty Board with the single CTA. Relaunch → no onboarding. Nothing on any tab shows content the user did not type.
2. **AT-2 Write.** Create "Checkout redesign": role, dates, three sections (≥ 40/60/20 words, Outcome with "38%"), 3 skills, 1 https link. Background the app for 10 s, then kill and relaunch → everything is present and the strength reads "6 of 6 · Strong".
3. **AT-3 Validation.** The link `http://x.y` is refused with an inline error. 21 skills: the 21st is refused with a message. An end month before the start month is refused.
4. **AT-4 Lanes.** Move to Featured with the note "Best for product roles" → the Board shows it under Featured, and the reader's History shows the move with the note. Move to Featured again → no new history entry.
5. **AT-5 Search.** Search "checkout" → a hit with section counts and a snippet → tap → the reader opens with "checkout" highlighted.
6. **AT-6 Fit check.** Paste a ≥ 30-word posting containing one of the user's skill tags and a term no case study has → the case study ranks first with the tag chip, and the missing term is listed under "Asked for, no evidence yet". A 10-word posting shows the guard. With zero case studies, it shows the guard.
7. **AT-7 Pack and Present.** Save a pack "Acme · PM" → relaunch → open the pack → Present → page 1 of N in pack order, no ad, landscape works. Exit → portrait restored.
8. **AT-8 Export.** Copy Markdown → paste into Notes → structure as in M8. Share PDF → the share sheet shows a `.pdf`. On a device: open it → the fonts are visible and the link taps open. (The device part stays **not verified** unless a human does it.)
9. **AT-9 Backup round trip.** Export a backup → Reset everything → empty Board → Restore that file → the same counts and contents, history included. Restore a non-backup `.json` → rejected, nothing changed.
10. **AT-10 Corruption.** Replace `cases.v1.json` with `{` → launch → banner shown, `cases.v1.json.corrupt-*` exists, the app is usable. Creating a new case study does not delete the corrupt copy.
11. **AT-11 Ads.** Online, with test ad ids: exactly one banner, at the end of the Board scroll. None anywhere else. No interstitial after 20 tab switches.
12. **AT-12 Nothing leaves.** With a proxy, or by code inspection if no proxy is available (say which): no request carries case-study text. Firebase and AdMob hosts only.

---

## 8. SHOULD (in order, only after every MUST passes)

- **S1. Cover image per case study** from the photo library (PHPicker via `image_picker`; stored re-encoded at ≤ 1600 px with EXIF stripped). Shown in Present and the PDF. No editing, so it stays clear of Photriya. Adds a pod; check `project.pbxproj` first.
- **S2. Practice mode:** a pack's case studies with only titles shown and a 2-minute timer per story, so the user can rehearse telling them aloud. No recording (AGRecorder's job).
- **S3. Monthly nudge:** a local notification ("Anything worth a case study this month?"), opt-in, with `POST_NOTIFICATIONS` requested at opt-in only.
- **S4. Import a Markdown case study** from Files (`## Context / ## What I did / ## Outcome` headings mapped to fields).
- **S5. Pack history:** `sentOn` date and note, plus a list sorted by date. Not an application tracker: no statuses, no pipeline.

## 9. Out of scope

- Accounts, sign-in, cloud sync, Supabase tables, web portfolio pages, public links, sharing to other users. All of these would bring 5.1.1(v) and 1.2 duties and a production backend change.
- Any AI or LLM, text rewriting, or résumé generation.
- Job search, job listings, scraping postings, applying through the app.
- Translations. English only (`app.dart:16`). Fit check's stopwords are English.
- Editing `store/apps/*.json`, `store/privacy/*.json`, `docs/**` or `fastlane/**` (store-compliance applies §11 afterwards). No submission or Resolution Center reply (Charter §1; 5.6 freeze MA-043).
- The repo-root `roadmap/`, `PORTFOLIO.md`, `mobile-rn/` and `src/` (§14 Q3).

---

## 10. Privacy: data list

| Data | Where | Leaves the device? | Purpose | Store label |
|---|---|---|---|---|
| Case studies (text, skills, dates, evidence URLs), lane history, packs, pasted postings | app support files | **No**, except when the user exports or shares (user-initiated, to a destination they pick) | app function | not collected |
| Profile (name, headline, email, website) | app support file | Only inside an export the user shares | export header | not collected |
| Flags (onboarded, last backup, paper size) | shared_preferences | No | app function | not collected |
| Crash data | Firebase Crashlytics | Yes, anonymous | app functionality | CRASH_DATA, not linked |
| Performance data | Firebase Performance | Yes | app functionality | PERFORMANCE_DATA, not linked |
| Product interaction (automatic screen views; no custom events, M11) | Firebase Analytics | Yes | analytics | PRODUCT_INTERACTION, not linked |
| Device ID / advertising data | Google AdMob (one banner) | Yes | third-party advertising | DEVICE_ID and ADVERTISING_DATA, not linked |

- `PrivacyInfo.xcprivacy`:
  - keep CrashData, PerformanceData, OtherDiagnosticData, ProductInteraction and DeviceID as declared today;
  - add the `NSPrivacyAccessedAPICategoryFileTimestamp` reason only if the new IPA scan requires it (it is already present: `C617.1`);
  - re-derive from the built IPA with `privacy_scan.py`.
- No tracking and no ATT prompt (AdMob non-personalised is decided by UMP; this is unchanged from today).
- Play Data safety: the same as above. "Data is encrypted in transit" is yes for the Firebase and AdMob SDKs. "Users can request deletion" is **not applicable** (no account). Local data is deleted by Reset or by uninstalling.

---

## 11. Store

**Name** (30 chars max; none is a trademark search, iTunes only, 2026-10-14):
1. **"Portfolio Board: Case Studies"** (29). Recommended: it keeps the brand and removes the finance reading.
2. "Casefolio: Work Portfolio" (25). The iTunes search for "Casefolio" showed no app with that name.
3. Plain "Portfolio Board" (15), with the subtitle doing the work.

The home-screen name (`CFBundleDisplayName`, Android label) stays **"Portfolio Board"** in every case.

**Subtitle (30 max):** "Projects as interview stories" (29), or "Case studies for interviews" (27).

**Promotional text (≤170):** "Write each project once as a case study, paste a job posting to see which ones fit, then present them full-screen or share a PDF. Offline; your work stays on your phone." (169 characters, counted with `len()`.)

**Description (draft; it opens with the job, not the app name; no ALL-CAPS skeleton; no claims about competitors):**
> When someone asks "tell me about a project you're proud of", the answer shouldn't depend on what you remember that morning.
>
> Write each project once as a case study: the context, what you did, and what changed. Add skills and links to the work itself. Your case studies sit on a board by readiness (draft, ready and featured), and each one shows which of six simple checks it still misses, like an outcome with no number in it.
>
> Got a posting or a client brief? Paste it into Fit check. You see your case studies ranked by the words they share with the posting, where each match sits in your own text, and the terms the posting asks for that none of your work mentions yet. Fit check counts shared words; it doesn't judge or write anything for you.
>
> Save the best matches as a pack for that opportunity. Present it full-screen in the meeting, even with no signal, or share it as a PDF or Markdown.
>
> Everything you write stays on your phone unless you export it. No account. Back up to a file and restore it on a new phone.
>
> Portfolio Board shows one ad banner, at the bottom of your board. Crash reports and usage statistics are sent anonymously to Google Firebase.

**Keywords (≤100):** `case study,portfolio,interview,STAR,career,job,projects,achievements,self review,freelance,pdf` (94 characters).

**Category:** primary PRODUCTIVITY (unchanged, `store/apps/portfolio-board.json`), secondary BUSINESS.

**Age rating:**
- Expected **Apple 4+** and **IARC Everyone**: no objectionable content, no UGC shared with others, no unrestricted web view (links open in the system browser), no messaging, no gambling, no medical content.
- `status.csv:851` shows `18+` today, with no recorded reason. store-compliance re-answers the questionnaire for v2.
- Whether the AdMob banner needs an ad-content cap at the AdMob console to stay consistent with 4+ is **not verified**: `agl_ads` sets no `maxAdContentRating` (`grep` on `packages/agl_ads/lib` → only `testDeviceIds`, `ads.dart:86-87`). That is §14 Q5.

**Review notes (replace the shared skeleton):**
- What it is and for whom: "A private, offline work portfolio. Users write their projects as case studies, match them against a job posting they paste (word overlap computed on the device; no AI), and present or export them."
- No account and no login, so no demo account is needed.
- Try it in 60 seconds:
  1. Not now on onboarding;
  2. Write a case study (any text) and add a skill such as "SQL";
  3. Fit check → paste any job description containing "SQL" (at least 30 words) → see the ranking and the gap list;
  4. Save as pack → Present.
- External services: Firebase Crashlytics, Performance and Analytics; Google AdMob (one banner on the Board). The app reads no Remote Config value.
- Devices tested: state exactly what was run. Simulators only unless a human ran a physical device.
- Contact: a real person (founder), not "App Reviewer".

**Screenshots** (iPhone 6.9", iPad 13", Android phone and 10" tablet; 5 frames each; captured from the release-mode app by `integration_test/store_screenshots_test.dart`):
1. Board with Featured / Ready / Draft lanes and strength labels: "Your projects, by readiness".
2. Case-study reader (Bitter type, evidence links): "Context, what you did, what changed".
3. Fit check results with chips and the gap list: "Paste a posting. See what fits.".
4. Present mode, landscape on the iPad frame: "Show it full-screen, even offline".
5. Checkup (below Strong, skills coverage): "Find the weak spots before they ask".

**Content rule for screenshots (company rule: nothing fake).** The frames must show **real case studies of real work**. The integration test types them at capture time, and they are **never bundled** in the app. Proposed source: American Group's own shipped work, written from facts verifiable in the repos (for example, MileMaster's IRS-rate export or AeroSwift's OpenSky integration), with every number traceable to a file. Founder approval is needed on whose work is shown (§14 Q2). Without approval, no screenshots are produced. Placeholder text must not be used instead. The dirty `fastlane/` screenshots belong to someone else; do not overwrite them until that work lands.

**Play feature graphic:** the index-card mark on `#F7F4EC` with the name. It replaces the Flutter-logo graphic (old spec §6).

**Privacy label changes:** none in data types relative to today (§10). Ads remain, so DEVICE_ID and ADVERTISING_DATA stay. The label no longer belongs to "the 20-app identical group" only if store-compliance confirms the final set after `privacy_scan.py`. That is **not verified** now.

---

## 12. Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | **4.3(b), "opportunistic variant"**: brag and career apps exist (§1), and Apple judges our account as a whole | Ship the signature fully (M5 + M7), not as a claim. Own identity (M9). Review notes lead with Fit check. The copy describes our job without comparisons |
| R2 | The name reads as finance (iTunes "portfolio board" → Moneycontrol first) | Subtitle and name option 1. No money fields (§2 rules). Keywords avoid "stocks" and "invest" |
| R3 | A reviewer sees an empty app, because there is never sample content | The empty states guide; the review notes give a 60-second path; Fit check works with one case study |
| R4 | 2.1(a) launch crash history (iOS 27) | M12 simulator launches on iPhone and iPad. A physical-device recording needs a human |
| R5 | Data loss: on-device only, no sync | Atomic writes; corrupt files kept (AT-10); backup and restore (AT-9); iOS device backup and Android auto-backup cover app files (Android: no `allowBackup="false"`; iOS: Application Support is backed up unless excluded, which the builder must not do) |
| R6 | Pasted postings and case studies leak to telemetry | M11 static guard; no custom events; crash logs take constants only |
| R7 | The ad shows in front of an interviewer | Banner on the Board only; Present, reader and Fit check are ad-free (M10, AT-11) |
| R8 | Adding plugins disturbs the dirty `project.pbxproj` | CocoaPods only; `pbxproj` diff check before commit; commit `Podfile.lock` only |
| R9 | Fit check feels weak on short or odd postings | Guards; weights shown; "counts shared words" honesty line; the S4 import improves input. Never pad results |
| R10 | Screenshot content cannot be produced honestly without approval | §14 Q2 blocks screenshots, not the build |
| R11 | Account-level 5.6 freeze (MA-043) blocks review anyway | Build and verify now. Submission is a founder action later |
| R12 | Store rename: a name change ships with a new version, the bundle id stays | Founder picks the name (Q1). store-compliance applies it in App Store Connect and Play |

## 13. Not verified (by me, for this spec)

- Competitor behaviour beyond their store descriptions; whether any of them has a posting-match feature.
- Trademark status of any proposed name (I ran iTunes searches only).
- `flutter analyze` / `flutter test` at `063144d` (not run; the task said do not build).
- Whether `file_picker`'s iOS document picker adds any `Info.plist` requirement in 13.1.0 (M11 asks the builder to check the built plist).
- Apple's current age-rating questionnaire treatment of ad content (§11).
- The reason for `18+` in `status.csv:851`.

## 14. Open questions (founder)

1. **Q1. Store name:** "Portfolio Board: Case Studies" (recommended), "Casefolio: Work Portfolio", or keep "Portfolio Board"? The home-screen name stays "Portfolio Board" either way; the bundle id is permanent.
2. **Q2. Screenshot content:** may the store screenshots show real case studies of American Group's own shipped apps (facts traceable to the repos), or your own work history? Nothing fake may be used, so without an answer there are no screenshots.
3. **Q3. Repo-root strategy files:** v2 removes the bundled company strategy from the app. The private repo still holds `roadmap/`, `PORTFOLIO.md`, `mobile-rn/` and `src/` at its root. Keep them there, move them to an internal repo, or leave them as they are? (A move is not destructive, but it is your content.)
4. **Q4. Ads:** keep the one Board banner (spec default, per the "fit per app" plan rows 409/415), or ship v2 with no ads?
5. **Q5. Ad content rating:** if the banner stays, set AdMob's max ad content rating to G for this app so it is consistent with an Apple 4+ rating? This is an AdMob console setting (Charter §4 account action).
6. **Q6. Privacy policy text** (Charter §6): the policy at `americangroup.ai/policy/portfolio-board/` must be rewritten for an account-less, on-device portfolio with Firebase and one AdMob banner. The office drafts it; you approve it.
7. **Q7. Resubmission** stays yours, and it stays blocked while the 5.6 freeze (MA-043) holds.
