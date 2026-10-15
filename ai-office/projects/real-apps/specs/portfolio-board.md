# Spec: portfolio-board — the team's offline docket for AGL's 33 project specs (internal tool, not a public product)

Author: product-manager (AI office), 2026-10-12
Project: real-apps (`../plan.md`, criteria 1–7)
Repo: `/Users/spatchava/agl/portfolio-board` (app in `mobile/`)
Base: `main` @ `87d5ae0b4196b1ab2ed8692cf28d7b019f7e07ac`. Source: `git -C /Users/spatchava/agl/portfolio-board rev-parse HEAD` and `git branch --show-current`, run 2026-10-12.
Baseline, run 2026-10-12 in `mobile/` against that base with `/Users/spatchava/agl/.flutter-sdk/bin/flutter`:
- `flutter analyze` → "No issues found! (ran in 12.7s)"
- `flutter test` → "+244: All tests passed!"

**Other people's uncommitted work is in this repo. Do not touch it.** `git status --short` (2026-10-12) shows:
- `mobile/fastlane/**`: both description files, `review_information/notes.txt`, every phone/tablet/iPad screenshot, and 4 new untracked `05.png` screenshots;
- `mobile/ios/Runner.xcodeproj/project.pbxproj`. Its diff is 6 lines: the provisioning profile changes from `c09f3297-…` to `7689ddf8-…`.

None of the MUST items below need any of those files. **Trap:** adding a native plugin (for example `share_plus`) can make Flutter/CocoaPods rewrite `project.pbxproj` and `Podfile.lock`. Every MUST below can be built with **pure Flutter/Dart only** (`Clipboard`, `shared_preferences`, which is already a dependency). If a plugin gets added anyway, run `git diff mobile/ios/Runner.xcodeproj/project.pbxproj` first. If the other person's edit is still there, do not commit that file; report it instead.

---

## 0. Decision gate. Read this first

**Recommendation: retire portfolio-board from the public stores and distribute it internally.** This is decision **D4** in `ai-office/reports/approvals/2026-10-12-real-apps-consolidation.md:30` and `projects/real-apps/overlap.md:44` (G12). It is a Charter §8 decision, so the founder makes it. I checked GitHub issue #25 ("Approve: consolidate/retire 6 overlapping apps — D1–D6") on 2026-10-12: state OPEN, 0 comments. **D4 is not answered.**

**Build rule.** No real-apps build effort goes into this app until D4 is answered (overlap guidance). After that:
- **D4 = yes (retire, internal):** build the MUST list in §3. It is small, because the app's code is already among the most honest in the portfolio. It is aimed at the people who actually use this tool, not at App Store Review.
- **D4 = no (stay public):** do **not** build §3 as written. The app needs a new public job, and I could not find one that stands up to 4.3(b) (see §1, "Why a public pivot is not proposed"). The product-manager writes a new spec once the founder names the public user it is for. That spec starts from the candidate in §7.

Why retirement is the honest answer (evidence):
1. **The listing itself says the app has no public user.** `store/apps/portfolio-board.json` `differentiation_overrides.2`: "It contains no content other than this one company's portfolio and is not a general project-management tool for other users' projects."
2. **Apple told us the same thing.** The 2.1 message (`.dist/rejections.json` "portfolio-board", 2026-09-27T01:11Z) ends: "Guideline 3.2 - Other Business Models: If your app is intended to be used by specific businesses, organizations or employees then use one of the other distribution options available to you through the Apple Developer Program Account."
3. **A proper channel exists.** I fetched `https://developer.apple.com/support/unlisted-app-distribution/` (HTTP 200) on 2026-10-12. It says: "Apps for partner sales tools, employee resources, or research studies are examples of good candidates for unlisted distribution." It also says a request needs the app "submitted to App Review" with a review note saying it is meant for unlisted distribution. That is a review submission, so it is founder-only (Charter §1) and blocked by the 5.6 freeze (MA-043). TestFlight internal testing and Play internal testing need no review.
4. **The original block was this exact question.** `_was_blocked_resolved.original` in the store JSON reads "Should probably not be published at all … publishes internal roadmap data". It was cleared only by the blanket 2026-09-24 instruction that all 43 apps go to both stores, not by any judgement about this app.

---

## 1. Problem

**Apple's state** (`/Users/spatchava/agl/.dist/rejections.json` → "portfolio-board", 4 messages):
- 2026-09-27T01:11Z **2.1 Information Needed** (the account-wide template, including the 3.2 note quoted above).
- 2026-09-29T16:47Z **our reply**, the portfolio template. "WHO IT IS FOR" was the subtitle pasted in ("Offline spec and stage board"). "EXTERNAL SERVICES USED" said "None. The app works entirely on the device and calls no external service." **That was false for the next binary.** Commit `c9f5d0f` added AdMob, and the current notes (`store/apps/portfolio-board.json` `review_information.notes` §5) list AdMob and Firebase.
- 2026-09-29T19:01Z **2.1(a) crashed on launch**, iPhone 17 Pro Max, iOS 27.0.
- 2026-10-05T21:26Z **4.3(a)/(b) + 4.2.6**, the same text as the other 25 apps. `docs/store-holds.json:102` records `"guideline": "4.2.6"`.

Google Play: PRODUCTION_DRAFT_STAGED (task context; I did not query Play myself).

**What works today.** I read all of `lib/` (23 files, 5,795 lines) on 2026-10-12. Nothing is a placeholder.
- **Data:** `assets/roadmap/portfolio.json` is bundled: schema 1, 33 records (28 products + 5 shared-infra), 200 documents (198 project docs + 2 portfolio docs), about 800 KB of markdown. It loads through `services/roadmap_repository.dart`, and a schema mismatch fails loudly (`:45-50`).
- **Portfolio tab** (`features/portfolio/portfolio_screen.dart`): a stage distribution bar, stage chips that open Browse pre-filtered (`:103-107`), categories in ExpansionTiles, the 2 portfolio documents, and provenance.
- **Project screen** (`features/project/project_screen.dart`): a Tracking tab with tagline, TAM/pricing facts, the 10-axis priority score, the greenlight gate with LOIs and pipeline, a document index and stage history. It also has one tab per document, rendered by a hand-written markdown parser and renderer (`core/markdown/markdown_parser.dart`, `widgets/markdown_view.dart`). Relative links switch tabs (`:98-112`).
- **Move stage** (`features/project/stage_sheet.dart`): a bottom sheet with an optional note. Moves persist in `shared_preferences` as an append-only log capped at 500 (`services/stage_store.dart`).
- **Browse** (`features/browse/browse_screen.dart`, `services/portfolio_query.dart`): full-text search over all 200 documents with per-document match counts and verbatim snippets. Results open the document with the term highlighted. Facets: category, stage, tier, spec depth, kind.
- **Health** (`features/health/health_screen.dart`, `services/portfolio_health.dart`): stage spread, Tier-1 gate rollup, measured spec depth, category coverage, and "untouched longest".
- **Settings:** provenance, the full change log, reset with confirmation, and the UMP Privacy choices tile.
- **States:** load failure with retry (`LoadFailure`), "No record named …", "No document … in the pack", and empty change log copy all exist.

**What is wrong:**
- **No public user.** See §0. Every screen speaks the vocabulary of one company's internal process: Stage-1/Stage-2, Tier-1 greenlight gates, LOIs, `roadmap/README.md`, `PORTFOLIO.md § 1`. A member of the public who installs it gets another company's investment pipeline.
- **It publishes company strategy.** The bundle holds pricing bands, GTM plans and competitor analysis for 28 prospective products. A regex count finds 1,485 dollar-figure tokens (for example `$50K`, `$250K`, `$1,499`). I found **no** confidentiality marking: the 5 hits for "confidential" are all domain content, such as legal-confidential data in `ai-legal-contract-review`. Whether this may be public is a founder question (see founder questions).
- **Decisions cannot leave the phone.** Stage moves and notes are "never written back" (`settings_screen.dart:41-42`). There is no export or copy, so a reviewer's decisions die on the device. That is the one real gap in the app's own job.
- **Ads in an internal tool.** `AglAdBanner` sits above the tab bar (`lib/app/router.dart:95`), with an interstitial on tab switches (`:104`). For the actual audience (the company's own staff), ads earn nothing real and invite self-generated ad traffic.
- **Template tells in this app (portfolio diagnosis; items marked "re-checked" I verified today):**
  - The icon is from the generator: `agl-manifest/scripts/generate_app_icons.py:76` `"portfolio-board": ("dashboard", "#37474F", "#78909C")` (re-checked).
  - The splash is the shared one: `ios/Runner/Base.lproj/LaunchScreen.storyboard` shasum `3f6a9b27d80dda327ce7df82d4887e3adbac50e4` (re-checked; same hash as 37 apps). Android `launch_background.xml` is `@android:color/white` (re-checked).
  - The theme is a clone: `core/theme/app_theme.dart` scores 0.83 Jaccard with RideZap's, and the diff is essentially primary `1565C0` vs `1B5E20` (diagnosis, not re-measured).
  - Inter everywhere (`app_theme.dart:52,57`; bundled in `assets/google_fonts/`). 13 apps use Inter.
  - Tailwind/Material default hexes in `lib/` (re-counted today): `B45309`×6, `6B7280`×4, `16A34A`×3, `9F1239`×2, `E5E7EB`, `DC2626`, plus Material `1565C0`×3 and `0D47A1`.
  - The shared shell: Material 3 `NavigationBar` with `AglAdBanner` above it, hidden on settings (`router.dart:83-133`). Stock Material icons on iOS.
  - 'What is bundled in this build.' (`features/settings/settings_screen.dart:29`, re-checked).
  - The Play feature graphic shows the Flutter logo (diagnosis, not re-checked).
  - 42% of description sentences are negations (diagnosis).
  - The review notes are the shared skeleton: "2. DEVICES …", simulators only, "Intended audience: Offline spec and stage board".
  - Privacy label: in the 20-app identical group (diagnosis).

**Why a public pivot is not proposed.** I looked for a public job that reuses this engine (offline markdown reading, full-text search, multi-axis scoring, stage moves with notes). The closest is "a portfolio board for a solo maker's own ideas". Apple's keyless iTunes API (`itunes.apple.com/search` and `/lookup`, run 2026-10-12) shows that category is already full of that exact feature set:
- **Idea Score** (id6565167217): "assign grades based on factors like budget, income potential, and passion … prioritize and choose the best projects". Weighted idea scoring.
- **Idea Log: Track your ideas** (id6475268939): "Watch as your ideas transition through stages". Stage tracking.
- **Pulse - Project Tracker** (id6761269528): "Health levels change based on your activity … fades when neglected". This is our "untouched longest".
- **Kill My Idea: Startup Test** (id6759175306): a go/no-go stress test, the same idea as our greenlight gate.
- **Trello** (id461504587, 7,009 ratings) and **Notion** (id1232780281, 90,369 ratings) do boards and docs generally.

A pivot into that space would be, in Apple's words, "an opportunistic variant of an existing category" (4.3(b)), from an account Apple is already judging as a whole. I am not willing to claim a gap I cannot show.

## 2. User and core job (D4 = yes)

**User:** the American Group LLC people who decide which of the 33 specs move forward: the founder and anyone the founder adds to the internal TestFlight / Play internal group. They read specs away from a laptop (on a train, between meetings, offline) and make stage calls.

**Core job:** read any of the 200 spec documents offline, find any claim across all of them in seconds, and **record a stage decision with its reason, then get that decision back into the repository.**

**Signature feature: "Decision docket export."** The app already captures stage moves and notes. It will turn them, together with the reviewer's shortlist, into a ready-to-commit Markdown review. Each entry carries the date, project, from→to, note, priority rank and score, and gate status. The review can be copied in one tap and pasted into a PR against `PORTFOLIO.md`. Generic tools (Notion, Trello) cannot produce this, because they do not know this corpus's stages, 10-axis scores or gate criteria. Fully on-device; no network.

## 3. Acceptance criteria. MUST (only after D4 = yes)

Each item lists what to change and the check that proves it. Every item must pass on a fresh install.

**M1. Launch proof (criterion 1, the 2.1(a) crash).**
- At HEAD, `ios/Runner/Info.plist:255-271` already carries `UIApplicationSceneManifest` with `FlutterSceneDelegate`, and `docs/REJECTION_ANALYSIS.md:14` reports "iOS 27 launch crash (no UIScene lifecycle): **0** apps still affected". Nobody has shown that this binary launches.
- Acceptance: a release-mode build (`flutter build ios --release --no-codesign` and `flutter build appbundle --release`) succeeds. The app is launched on an iOS 27 iPhone 17 Pro Max simulator and on an Android emulator, and a screenshot of the first screen is saved and looked at (memory rule: a white screen passes analyze/tests). Physical-device launch is **not verified** unless a human runs it. Say so in the report.

**M2. Signature: Decision docket export (criteria 2, 3).**
- New `lib/services/docket_export.dart`: a pure function `String buildDocket(PortfolioBoard board, List<StageChange> history, Set<String> shortlist, {DateTime? since})` that returns Markdown:
  - a header with the export date and pack provenance (`roadmapGeneratedOn`, pack built);
  - "Decisions": one line per move since `since` (default: all), newest first, as `YYYY-MM-DD · <slug> · <from> → <to> · rank N/28, score S/100 · gate met: X` plus the note quoted underneath. Shared-infra records have no rank; say "shared infra" and never invent one.
  - "Shortlist": each starred record with its effective stage and rank;
  - "Board now": counts per effective stage.
- UI: an "Export decisions" action in Settings → Change log. It opens a full-screen preview (rendered with the existing `MarkdownView`), offers a "since" choice (all / last 7 days / since last export, with the last-export time persisted in `shared_preferences`), and has **Copy Markdown** (`Clipboard.setData`, then a SnackBar "Copied N decisions").
- Empty state: with no moves and no shortlist, the action stays visible and the preview says "Nothing to export yet: move a project's stage or star it, then come back." Never an empty document.
- Tests: a unit test feeds `buildDocket` fixed changes (fixed `at`) and compares the exact output string, including a shared-infra record and a note with Markdown characters, which must be escaped. A widget test shows that tapping Copy puts the text on the clipboard (mock `SystemChannels.platform`).

**M3. Shortlist (criterion 3 depth: persistence plus filter).**
- A star toggle in the Project app bar and on `ProjectCard`. It persists under the `shared_preferences` key `portfolio.shortlist.v1`. Browse gets a "Shortlisted" facet. Settings reset clears the shortlist too, and the reset dialog text says so.
- Empty state on the shortlist facet: "No starred projects. Tap ☆ on a project to keep it here."
- Tests: store round-trip; corrupt JSON gives an empty shortlist without crashing (same pattern as `StageStore.overrides()`); the facet filters correctly; reset clears it.

**M4. Remove ads from the internal build (criteria 4, 5). Needs founder confirmation, see founder questions.**
- Delete `AglAdBanner` (`router.dart:95`), `AglAds.onTransition` (`:104`), and `AglAds.configure/initialize` (`main.dart:26-30`). Remove `agl_ads` from `pubspec.yaml`, plus `GADApplicationIdentifier`/`SKAdNetworkItems` from `ios/Runner/Info.plist` and the AdMob app-id meta-data from `AndroidManifest.xml`.
- `PrivacyChoicesTile` then has nothing to govern and goes too. It is UMP for ads only (`settings_screen.dart:107-152`).
- `test/ads_placement_test.dart` asserts the old behaviour. **Replace** it with a test that asserts no `AglAdBanner` in any shell route, and record the replacement in the commit message. That is a behaviour change, not a test deleted to go green.
- Firebase Crashlytics/Analytics (`agl_observability`) stay. The app reads no Remote Config key: `grep -rn -i remote lib` → only the comment at `main.dart:20`. Keep it that way (5.6).

**M5. Remove this app's template tells: copy (criteria 4, 5).**
- `settings_screen.dart:29` "What is bundled in this build." → "The roadmap snapshot inside the app."
- Acceptance: `grep -rn -i -E "this build|coming soon|not connected|unavailable" mobile/lib --include=*.dart` → only code comments (today: `app.dart:8`, `doc_links.dart:13`, `markdown_view.dart:52,468` are comments). No user-visible string contains them.
- Home-screen name: `CFBundleDisplayName` is already "Portfolio Board" (re-checked). No change.

**M6. Own identity: colour, type, icon, splash (criterion 4).** "Manila docket": spec folders on a desk, not a dashboard.
- **Colour:** `ColorScheme.fromSeed(seedColor: Color(0xFF5B6B2E))` ("archive olive"). Pin `primary` to `#5B6B2E`. Light surfaces: paper `#F3ECDD` (manila), card `#FBF7EE`, rule `#D8CDB4`, ink `#1F2124`, secondary ink `#5E5A50`. Dark theme: background `#1B1C18`, card `#25261F`, ink `#ECE6D6`, primary `#B5C27A`.
- **Stage colours** (replacing every Tailwind hex in `stage.dart` and `app_theme.dart`): Stage-1 spec `#8A8270` (pencil), Stage-2 discovery `#2F6E8E` (ink blue), Greenlit `#5B6B2E` (olive), Parked `#B07A1E` (ochre), Dropped `#8E3B2E` (oxblood). Each stage chip also keeps its text label, so colour is never the only signal.
- No sibling spec in `specs/` uses `#5B6B2E` or a manila paper ground. I checked the seeds in the 24 existing specs: vermilion, petrol, harbour blue, beetroot, dusk indigo, PCB green and others.
- **Typography:** **Spectral** (Production Type, OFL) for document bodies and headings in `MarkdownView`. **Archivo** (OFL) for UI chrome, labels, numbers and tab labels. Both are bundled as asset fonts under `assets/fonts/` with their `OFL.txt`, and Inter plus `google_fonts` are removed. Sources verified 2026-10-12: `raw.githubusercontent.com/google/fonts/main/ofl/spectral/OFL.txt` → 200, `…/ofl/archivo/OFL.txt` → 200. The repo lists `Spectral-Regular/Medium/SemiBold/Bold/Italic.ttf` and `Archivo[wdth,wght].ttf`. No sibling spec uses Spectral or Archivo (grep of `specs/*.md`). Register both licences in `LicenseRegistry`, as `configureFonts()` does today.
- **Shape:** document cards get 4 px corners with a folder-tab notch: a 28×6 px tab in the stage colour on the card's top-left. That replaces the 16 px pill cards (`app_theme.dart:63`) and the 12 px radii.
- **Icon:** a new 1024 px master that is not from `generate_app_icons.py`. A manila folder silhouette, tab at top-left, on olive `#5B6B2E`, with three ruled lines, drawn as vector art; no Material glyph. Write it into `ios/Runner/Assets.xcassets/AppIcon.appiconset` (all sizes, no alpha) and Android mipmaps/adaptive icon. Remove the `"portfolio-board"` row from the DESIGN table in `agl-manifest/scripts/generate_app_icons.py`, so a regeneration cannot overwrite it. That script is not under `docs/` or `store/`.
- **Splash:** a new `LaunchScreen.storyboard` with background `#F3ECDD` and the folder mark at 96 pt centred, plus the word "Docket" in Archivo below it rendered into the image. The Android `launch_background.xml` uses the same colour. Acceptance: `shasum ios/Runner/Base.lproj/LaunchScreen.storyboard` ≠ `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, and `grep -c 'red="1" green="1" blue="1"'` on it → 0.
- Acceptance: `grep -rhoiE "B45309|6B7280|16A34A|9F1239|E5E7EB|DC2626|1565C0|0D47A1|F8F9FA|1A1A2E" mobile/lib` → 0. `grep -rn "GoogleFonts\|google_fonts" mobile/lib mobile/pubspec.yaml` → 0.

**M7. Own home layout and first run (criterion 4).**
- **Home = "Docket"**, replacing the category-first overview. Top to bottom:
  1. the reviewer's **Shortlist** (horizontal folder cards; empty state from M3);
  2. **Recent decisions**, the last 3 moves with notes, plus "Export" (M2);
  3. **Ranked**: the 28 products in `priority.rank` order, separated by tier bands T1–T4, each row showing rank, score/100 and the stage tab colour;
  4. **Shared infrastructure**, the 5 specs.

  Categories move to a segmented control at the top of Ranked ("By rank | By category"), reusing `_CategoryTile`.
- **Tabs:** three, Docket / Search / Health. Settings becomes a gear in the Docket app bar. On iOS, use `CupertinoTabBar` with `CupertinoIcons` (`folder`, `search`, `chart_bar`). On Android keep `NavigationBar`. Choose by `defaultTargetPlatform`. That is platform adaptation, not a hidden switch: identical features on both.
- **First run** (once; flag `docket.onboarded.v1`): one screen, "AGL portfolio docket. 33 project specs, offline. Star what matters, move a stage with a reason, export your decisions as Markdown for a PR. Stage moves stay on this phone until you export them." One button: "Open the docket". No "Get started", no "Welcome back".
- Tests: a widget test of the first run showing once and not on the second launch; Docket renders ranks 1..28 in order with tier bands; the iOS path renders `CupertinoTabBar` (`debugDefaultTargetPlatformOverride`).

**M8. Proven (criterion 6).**
- `flutter analyze` → "No issues found!". `flutter test` → all pass, with a count of at least 244 plus the new tests. No test deleted or skipped except the `ads_placement_test.dart` replacement named in M4.
- Commit path-limited (`git add mobile/lib mobile/test mobile/assets mobile/pubspec.yaml mobile/pubspec.lock mobile/ios/Runner/Info.plist mobile/ios/Runner/Base.lproj mobile/ios/Runner/Assets.xcassets mobile/android/app/src/main`). Never `git add -A`, never the dirty `fastlane/` or `project.pbxproj`. Push to `main`.
- Run `dart run tool/build_roadmap_asset.dart --check` (from the repo root layout the README describes, if `../roadmap/` exists) to show the bundle still matches its source. If `roadmap/` is not present, write "not run".
- Do not run `dart format`.

## 4. SHOULD (only after D4 = yes, if time allows)

- **S1. Compare two records** side by side on the 10 priority axes (a bar per axis, the difference highlighted), launched from the shortlist.
- **S2. Search history:** the last 10 queries persisted and shown under the empty search field, clearable.
- **S3. Health "decided vs untouched":** count projects with at least one local move vs none, linked to Browse.
- **S4. Web build** (`flutter build web`) for a team member without a test device. Hosting it is a founder/website decision. It must not go under the public `americangroup.ai` root without approval, because the content is company strategy.
- **S5. Share sheet** (`share_plus`) next to Copy in M2, only if `project.pbxproj`/`Podfile.lock` are clean when it is added (see the trap above).

## 5. Data source

- **On-device only.** The bundled `assets/roadmap/portfolio.json` (generated by `tool/build_roadmap_asset.dart` from the repo's `roadmap/`, `PORTFOLIO.md` and `PRIORITIZATION.md`; its byte-identity is guarded by `test/roadmap_asset_test.dart`), plus `shared_preferences` for stage overrides, history, shortlist, onboarding flag and last-export time.
- No Supabase, no public API, no account, no demo login, no remote switch, no reviewer/region/date detection.
- Nothing is invented. Shared-infra records carry no rank. Unmeasurable gates stay "not measurable" (existing rule). Export output contains only recorded moves and stored facts.

## 6. Store impact

**If D4 = yes (recommended).** All of these are founder actions (Charter §1/§8), prepared by store-compliance, not done by the office:
- **Apple:** do not resubmit for public release. The app was never released, so there is nothing to "Remove from sale". Distribute via **TestFlight internal testing** (no review). If the founder wants a link-only App Store install for partners, use **Unlisted App Distribution**. It requires a review submission with the review note: "This app is intended for unlisted distribution to American Group LLC staff and partners who evaluate our project portfolio. It is not intended for the public App Store." Blocked while the 5.6 hold is in force (MA-043).
- **Google Play:** discard the staged production release (PRODUCTION_DRAFT_STAGED) and ship to the **Internal testing** track only.
- **Listing copy** (`store/apps/portfolio-board.json`; I did not edit it, another workstream owns it): no public copy is needed. If a description is kept for the internal/unlisted listing, use: name "AGL Portfolio Docket"; subtitle "Internal: our 33 project specs"; first line "For American Group LLC staff and partners: read our 33 project specs offline, star and move projects with a reason, and export your decisions as Markdown." Drop the "What it does not do" paragraph (most of the 42% negations). Drop the ads paragraph if M4 lands.
- **Review notes, if an unlisted submission is ever made:**
  - Replace the shared skeleton. State plainly that it is an internal tool.
  - List external services accurately: Firebase Crashlytics/Performance/Analytics. No AdMob after M4. Remote Config initialised by `agl_observability`, but the app reads no key.
  - Say the device actually tested. Do not claim physical-device testing unless a human did it.
  - Replace "App Reviewer" contact with a real person (founder).
- **Screenshots:** retake after M6/M7 (Docket home, a document in Spectral, Search with highlights, the Export preview). The dirty `fastlane/` screenshots belong to someone else. Do not overwrite them until that workstream lands.
- **Privacy label:** after M4 it no longer belongs in the 20-app identical group. Remove "Device ID — third-party advertising"; keep crash data, performance data and product interaction (Firebase), not linked to identity. Same change to `PrivacyInfo.xcprivacy` (drop the AdMob-related entries).
- **Play feature graphic:** replace the Flutter-logo graphic with the manila folder mark on `#F3ECDD`, for whatever internal listing remains.

**If D4 = no:** none of the above. The founder names the public user and the product-manager writes a new spec (§7).

## 7. Out of scope

- Any public-store pivot. The strongest candidate, recorded only so a D4 = no spec does not start from zero: "bring your own Markdown spec folder". Import a folder or zip from Files, read it offline with tables, search with match counts, and roll up the `- [ ]` checkboxes in each project into a gate view. Risk: Obsidian, 1Writer and the idea apps in §1 already cover most of it. Competitor coverage for this candidate is **not verified**; I did not search for it.
- Editing specs on device, sync, accounts, Supabase.
- Adding projects; the record set comes from `roadmap/` via the build tool.
- Translations (the app declares English only, `app.dart:16`).
- Store submission, Resolution Center replies, Play publishing, removing the store record (founder, Charter §1/§8).
- `store/apps/*.json`, `fastlane/`, `docs/`: owned by another workstream.

## Founder questions

1. **D4:** retire portfolio-board from the public stores and keep it internal (TestFlight internal / Play internal testing)? Recommended: yes. Issue #25 is still unanswered.
2. If yes: remove AdMob from the internal build (M4)? It removes an ad unit that today serves no public audience. Recommended: yes.
3. Is the bundled content (pricing bands, GTM plans and competitor analysis for 28 prospective products) cleared to be public in any form? This covers unlisted links and a web build (S4). If not, distribution stays TestFlight-internal / Play-internal only.
4. Rename to "AGL Portfolio Docket" for the internal build? The bundle id `com.americangroupllc.portfolioboard` stays either way, because bundle ids are permanent.
