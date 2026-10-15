# Spec: Uscis-Case — a family's immigration case file that knows its filing windows

Author: product-manager (AI office), 2026-10-12
Project: real-apps (`../plan.md`, criteria 1–7)
Repo: `/Users/spatchava/agl/Uscis-Case`. The Flutter app is at the repo root (`lib/`, `test/`, `pubspec.yaml`). The repo also carries the old web/RN/Electron product (`client/`, `server/`, `mobile/`, `shared/`, …); none of that ships in the store binary and this spec does not touch it, except to port one pure function (M3).
Base: `main` @ `c4b30ab73729967f75d97930183c2b3a6f87a2e3` (`git rev-parse HEAD`, `git branch --show-current`, run 2026-10-12).
Baseline (run 2026-10-12 against that base):
- `flutter analyze` → "No issues found! (ran in 26.5s)"
- `flutter test` → "+249 -1: Some tests failed." The one failure is `test/release_config_test.dart: backend host the dead list includes the manifest NXDOMAIN hosts`. It fails on `expect(nx, isNotEmpty)` (`release_config_test.dart:49`), because `../agl-manifest/docs/api-hosts.json` currently lists no NXDOMAIN hosts. This is an environment-dependent test about the `API_BASE_URL` backend switch. M1 deletes that switch, and the test goes with it (M9).

**Other people's uncommitted work is in this repo. Do not touch it.** `git status --short` shows 28 modified files under `fastlane/**` (descriptions, notes.txt, every Play and App Store screenshot), plus `ios/Podfile.lock` (`COCOAPODS: 1.16.2` → `1.17.0`) and `ios/Runner.xcodeproj/project.pbxproj` (16 lines). This spec changes none of those files by hand.

**Podfile.lock trap.** Removing `google_sign_in` / `sign_in_with_apple` (M1), or adding any plugin with a pod (`share_plus`, `flutter_local_notifications`), makes CocoaPods rewrite `ios/Podfile.lock`. Before committing, run `git diff ios/Podfile.lock`. If the other owner's `COCOAPODS: 1.17.0` edit is still uncommitted, **do not commit `Podfile.lock`**. Report it instead, and use the Clipboard fallbacks named below. No MUST item here needs a new pod.

---

## 1. Problem

**Apple's state.** Apple rejected the app under **4.3(a)/4.3(b)/4.2.6** on 2026-10-05T21:25:47Z (`/Users/spatchava/agl/.dist/rejections.json` → "Uscis-Case", message 0, the portfolio-wide text with md5 f5127d27). Earlier, on 2026-09-29T18:32Z (message 1), it rejected:
- **2.1(a)**: "it crashed on launch" on an iPhone 17 Pro Max with iOS 27.0;
- **2.3.3**: screenshots;
- **2.3.6**: the age rating must say Advertising = Yes.

Google Play: LIVE_PRODUCTION.

**Why Apple sees a copy of what is already there (4.3(b)).** The App Store's USCIS case-tracker category is crowded, and its leaders do the one thing this app cannot. I checked with the iTunes Search API on 2026-10-12 (`itunes.apple.com/search?term=uscis+case+status`). I read descriptions only and did not run these apps.
- **"Case Tracker for USCIS & NVC"** (Immivision, id921827126, **318,391 ratings**) claims: live status for every receipt prefix, NVC tracking, a "search a range of cases" neighbour lookup, background status-change alerts, the Visa Bulletin, immigration news and a Civics Quiz.
- **"Lawfully Case Tracker"** (id1435063223, **173,509 ratings**) claims: live USCIS status, a case-history timeline, push alerts, a personalised visa bulletin, NVC/DOL/immigration-court (EOIR) tracking, and a "Case Analysis Pro" upsell.
- Further live-status trackers in the same results: MigraConnect (194,082 ratings), Case Status Inc. (45,208), and "Case Tracker for USCIS Status" (21,692).

Our app offers the **same menu**: receipts, status, NVC, visa bulletin, news, civics, AI. But it **cannot fetch a status** (see §3): the user copies statuses by hand. As a case-status tracker it is strictly weaker than free apps with hundreds of thousands of ratings. A new skin alone will not fix that, so the product has to change.

**What in the binary reads as hidden or as a template (evidence read 2026-10-12):**
- **A build-time switch decides which features exist (5.6 pattern, the reason 16 sibling apps were rejected).** `lib/services/app_config.dart:41` reads `String.fromEnvironment('API_BASE_URL')` with an empty default. `ApiService.isLive` (`lib/services/api_service.dart:43`) then hides or reshapes screens:
  - `resources_screen.dart:41-63`: **AI chat** and **Impact Advisor** cards appear only when `live`.
  - `:88-115`: Processing Times and Visa Bulletin open a native screen only when `live`; otherwise they open a browser link.
  - `settings_screen.dart:40-46`: the status-alerts setting.
  - `nvc_tracker_screen.dart:131-135`: the NVC lookup.
  - `case_detail_screen.dart:531`: Refresh.
  - `case_history_screen.dart:61`: Refresh all.

  The shipped IPA still contains the unreachable screens' text: `strings Payload/Runner.app/Frameworks/App.framework/App` from `/Users/spatchava/agl/.dist/Uscis-Case.ipa` (built 2026-10-08) → "AI-powered analysis" 1 hit, "Chat with the USCIS immigration AI assistant" 1, "LIVE LOOKUP UNAVAILABLE" 1.
- **A second switch hides a whole sign-in flow.** `app_config.dart:62` has `static const bool authDisabled = true;`. `main.dart:249` reads `(AppConfig.authDisabled || authenticated) ? HomeShell() : LoginScreen()`, so `LoginScreen` (the portfolio's "Sign in with Apple / Continue with Google / Continue as guest" wall, `login_screen.dart:259,271,282`) is compiled in but unreachable. `pubspec.yaml` still ships `google_sign_in`, `sign_in_with_apple` and `crypto` for it.
- **Dead screen.** The Alerts tab can never receive an alert without a backend. Its empty state says "This version does not check USCIS automatically…" (`alerts_screen.dart:62`).
- **Shared shell.** `home_shell.dart:79` has a stock `BottomNavigationBar` with 5 tabs (Home, My Cases, Alerts, Resources, Profile), and `BannerAdSlot` sits directly above it (`:76`). `ad_service.dart:59,102` preloads an interstitial that nothing ever shows (`grep -rn "Interstitial" lib` → only `ad_service.dart`).
- **Template copy.**
  - "Get Started" (`onboarding_screen.dart:199`);
  - "Welcome back" (`i18n/app_strings.dart:252`);
  - "AI-powered analysis…" (`impact_advisor_screen.dart:68`);
  - a sample/demo vocabulary still in the string table: `app_strings.dart:136,138` "Sample data — this is a demonstration case…", "Live lookup unavailable — sample only";
  - `services/sample_data.dart` (192 lines), which on inspection holds **no invented data**: only the static FAQ, NVC guide, quick links and a timeline helper for the backend path. The file name is the only problem.
- **Duplicate infrastructure.** `lib/app_env.dart` is byte-identical to 4 other apps (diagnosis). `supabase_config.dart` is the 15-app scaffold. `auth_service.dart` has 0.52 Jaccard with Kinnav.
- **Skin.**
  - The palette is the US flag (`brandNavy #002868`, `brandRed #BF0A30`, `app_theme.dart:12-13`) on Tailwind blue/gray (`primary #1D4ED8`, `gray50…gray900 #F9FAFB…#111827`, `app_theme.dart:16-46`, 8 Tailwind greys), with `ColorScheme.fromSeed(brandNavy)` (`:112`). The flag colours also make a non-government app look official.
  - No typeface is declared.
  - Corners are 4/8/12/16 plus pills.
  - The icon is a white document with a green check on a diagonal navy gradient (`ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png`, viewed).
  - The splash `LaunchScreen.storyboard` shasum is `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, the same file as 37 of 43 apps.
- **Three names.**
  - App Store: "USCIS Case Lookup" (`store/apps/Uscis-Case.json` copy.en.name; `_name_note` says it "no longer describes this build").
  - Home screen: `CFBundleDisplayName` "Case Tracker for USCIS".
  - Bundle: `CFBundleName` "Case Tracker".
  - Android: `title_activity_main` "USCIS Case".

  The store name also uses a government agency's name.

**What is real and worth keeping:**
- **The receipt tracker and status log.** `CasesProvider`, `TrackedCase` with labels and an append-only `StatusEntry` history marked `user`/`uscis`, `StorageService` persistence, receipt validation (`ApiService.receiptRegex`), copy-and-open-USCIS (`widgets/case_status_tools.dart`) with the 12 common status wordings, and the history export text (`case_history_screen.dart:25-44`).
- **The civics trainer.** It holds the official 2025 test (128 questions, M-1778 (09/25), with source URL in `civics_data_2025.dart:1-12`) and the 2008 test (100), the 65/20 filter, the 20/12 and 10/6 rules, and per-version progress and best score.
- **The Federal Register client** (`ApiService.getNews`), which is keyless and verified in §3.
- **Accessibility work.** Receipt numbers are spelled out for screen readers, plus foldable layout handling and RTL.
- **Startup.** The guarded storage start in `main.dart` and the UMP "Privacy choices" row.
- **The N-400 date engine.** The old web product already has one: `shared/n400.ts:90-123` computes "earliest filing = (LPR date + N years) − 90 days" and cites 8 CFR 334.2(b). M3 ports it to Dart.

## 2. User and core job

**User:** a family in the US going through USCIS paperwork across several years and several people. For example: a green-card holder with a conditional card and a spouse's EAD, who is counting toward citizenship; or a sponsor with an I-130 for a parent and an I-765 renewal of their own. They hold paper notices (I-797), cards with expiry dates and a passport full of trips. Their real anxiety is less "has the status changed today?", which the big trackers already answer, and more:

> "When can I file — and when is it too late? Which of our cards expires next and when does its renewal window open? Do my trips abroad push back my citizenship date? How long has each of our cases been sitting in each stage?"

**Core job: keep the family's case file, and never miss a window.** The user adds each receipt with its form type and receipt date, and each card or document with its expiry date. As they check the official USCIS site, they record statuses, which the existing status log already handles. The app turns those dates into a single **Docket**: every filing window opening, every expiry, and every deadline the user copied from a notice, for every person, in date order, offline.

**Signature feature: "Windows" — filing windows computed from your own documents, plus the Citizenship clock.**
- **Rule-backed windows.** For each document type the app computes the window from a rule **quoted verbatim from uscis.gov** (§3), shows the quote and the link under the date, and counts down:
  - I-751 joint filing: the 90 days before the conditional card expires.
  - EAD renewal (I-765): opens 180 days before expiry, with USCIS's "at least 90 days before" shown too.
  - Green card renewal (I-90): opens 6 months before a 10-year card expires.
  - N-400: 90 calendar days before the 5-year or 3-year (married to a US citizen) anniversary.
- **Citizenship clock.** The user enters the date on their green card and their basis (5-year, or 3-year married to a US citizen), then logs trips abroad. The app shows:
  - the earliest N-400 filing date;
  - physical-presence days against the requirement (913 for the 5-year path, per the Policy Manual quote in §3), counting departure and return days as days present, as USCIS states;
  - every trip of more than 6 months but less than 1 year flagged as one that can break continuous residence, and every trip of 1 year or more flagged as one that breaks it;
  - a **"Plan a trip"** what-if that shows how a proposed trip would move the date or the flags before the user books it.
- **Deadlines from notices.** For things no rule computes (an RFE response due date, a biometrics or interview appointment), the user types the date printed on the notice, and it appears in the Docket labelled "from your notice". The app never computes an RFE deadline itself.

**Competitor check (iTunes Search/Lookup API, 2026-10-12; descriptions only, apps not run; WebSearch is disabled here: "Internet mode is not enabled"):**
- **Immivision** and **Lawfully** (above): live status, visa bulletin, news, alerts. **Neither description mentions filing windows, card expiry or renewal windows, or trip and physical-presence counting.**
- **"Green Card Trips – USA Tracker"** (Fabulous Apps, id6749515843, **9 ratings**, updated 2026-08-28) claims trip logging, the 913/548-day physical-presence count, continuous-residence alerts and a "Travel Simulator". **It already does the Citizenship clock. Our clock is not novel by itself, and the spec does not claim it is.**
- **Civics apps** ("US Citizenship Test 2026 Plus", id1103037173, 104,319 ratings; "Citizen Now", id1492938869, 65,595 ratings, with an AI speaking simulator, audio, ZIP-localised answers and CarPlay) are far ahead on civics. Civics stays a supporting feature here, not the pitch.
- **So the claimed gap is narrow, stated plainly:** one on-device file for a **family's** cases and cards that computes **every** renewal and filing window (I-751, I-765, I-90, N-400) with the rule quoted from uscis.gov under each date, combined with the trip-adjusted Citizenship clock and the user's own status log. No sign-in, no lookup, no data leaving the phone except the public Federal Register query in M5. Whether reviewers find this distinct enough is **not verified**; see founder question Q1.

## 3. Data sources (verified 2026-10-12)

**Used by this spec:**

| Data | Source | Proof (2026-10-12) |
|---|---|---|
| Receipts, statuses, cards, notice deadlines, trips, civics progress, cached Federal Register results | On-device, through the existing `StorageService` (`shared_preferences`) | — |
| Window rules (constants in code, each with its quote and URL) | uscis.gov pages fetched with curl. The quotes below are copied from the fetched HTML | `https://www.uscis.gov/i-751` HTTP 200: "You must file your Form I-751 during the 90-day period immediately before your conditional residence expires." / `https://www.uscis.gov/i-765` 200: "We generally recommend you file a Form I-765 to request a renewal Employment Authorization Document (EAD) up to 180 days before your current EAD expires." and "To renew your Employment Authorization Document, file Form I-765 at least 90 days before the expiration." / `https://www.uscis.gov/green-card/after-we-grant-your-green-card/replace-your-green-card` 200: "you must replace your Green Card if: Your Green Card is either expired or will expire within the next six months" / `https://www.uscis.gov/n-400` 200: "You may file Form N-400, Application for Naturalization, 90 calendar days before you complete your continuous residence requirement if your eligibility for naturalization is based upon being a: Permanent resident for at least 5 years; or Permanent resident for at least 3 years if you are married to a US citizen." |
| Citizenship-clock rules | USCIS Policy Manual (curl, HTTP 200) | `uscis.gov/policy-manual/volume-12-part-d-chapter-4`: "Applicants for naturalization under INA 316(a) are required to demonstrate physical presence in the United States for at least 30 months (at least 913 days) before filing", and "USCIS will count the day that an applicant departs from the United States and the day he or she returns as days of physical presence". Also "at least half the time for which his or her continuous residence is required". `…/volume-12-part-d-chapter-3`: continuity "can be broken" when "The applicant is absent from the United States for more than 6 months but less than 1 year; or The applicant is absent from the United States for 1 year or more." |
| Official notices and rules per form (M5) | Federal Register API, keyless: `https://www.federalregister.gov/api/v1/documents.json?conditions[agencies][]=u-s-citizenship-and-immigration-services&conditions[term]="Form I-765"&order=newest&per_page=20&fields[]=title&fields[]=publication_date&fields[]=type&fields[]=document_number&fields[]=html_url&fields[]=abstract&fields[]=effective_on&fields[]=comments_close_on` (curl needs `-g` for the brackets) | HTTP 200. Term counts: "Form I-485" 56, "Form I-130" 30, "Form N-400" 61, "Form I-765" 186. Newest I-765 item: 2026-09-14 Notice 2026-18681. The `RULE`/`PRORULE` type filter works (I-765 → 5 results, with `effective_on` and `comments_close_on`). Host `www.federalregister.gov` is "ok" in `docs/api-hosts.json` |

**Not usable (checked, so nobody builds on them):**
- **Live case status.** `https://egov.uscis.gov/csol-api/case-statuses/<receipt>` returns HTTP 403 with "Attention Required! | Cloudflare". USCIS's official Case Status API (developer.uscis.gov, which answers 200) needs registered credentials we do not have. Scraping behind a bot wall is out.
- **Processing times data.** `https://egov.uscis.gov/processing-times/api/forms` returns HTTP 403 (Cloudflare). So processing times are **user-recorded** (M2), not fetched.
- **Visa Bulletin data.** `travel.state.gov/.../visa-bulletin.html` returned HTTP 403 (Cloudflare) to curl from this machine, with and without a phone user agent. The page may open in Safari on a phone (**not verified**). The bulletin is therefore a link plus **user-recorded** cutoffs (M2). A server-side bulletin feed is founder question Q3.
- **3-year physical presence (548 days).** I could not fetch a page stating "548" (the fetch of Policy Manual vol. 12 part G was refused by the office's guard). 548 is derived from the verified "half the time" rule (3 × 365 / 2 = 547.5 → 548, the same arithmetic as 5 × 365.25 / 2 ≈ 913). The app must label it "half of 3 years (548 days)" and cite the half-time sentence, not a page that says 548. See §7.

No API keys, no paid feed, no Supabase reads or writes for features, no backend of ours.

## 4. Acceptance criteria

### MUST (what Apple has to see to judge this a real, distinct app)

**M1. One build, nothing hidden, no dead screens (5.6 and plan criterion 1).**

Delete:
- `AppConfig.apiBaseUrl`, `defaultApiBaseUrl`, `resolvedApiBaseUrl`, `authDisabled`, `seedSampleData` (keep `kPrivacyPolicyUrl`);
- `ApiService.isLive`, `checkStatus`, `getProcessingTimes`, `getVisaBulletin`, `askAi`, `getImpactAnalysis`, `checkNvcStatus`, `_postTrpc`, `_unwrapTrpc` (`ApiService` keeps only the Federal Register client and becomes `FederalRegisterClient`);
- the screens `ai_chat_screen.dart`, `impact_advisor_screen.dart`, `processing_times_screen.dart`, `visa_bulletin_screen.dart`, `alerts_screen.dart`, `login_screen.dart`, `profile_screen.dart` (merged into Settings, M7), `home_shell.dart` and `resources_screen.dart` (replaced by M7's home);
- the NVC live-lookup branch of `nvc_tracker_screen.dart`. The static NVC guide stays as a page linked from an approved I-130/I-140 case and from Sources;
- `CasesProvider.liveLookupAvailable`, `checkStatus`, `trackFromResult`, `refreshAll`, `RefreshResult`;
- `NotificationsProvider` and `AppNotification`, if nothing else uses them after Alerts goes;
- `CaseStatusResult.isSample`, `SampleDataBanner`, and the `sample.*` strings;
- `services/sample_data.dart`: move `kFaqEntries`, `kQuickLinks` and the NVC guide to `lib/content/reference.dart`, and delete `SampleData.synthesizeTimeline`;
- `AuthProvider` sign-in methods, `auth_service.dart` sign-in code, and the deps `google_sign_in`, `sign_in_with_apple`, `crypto` (Podfile.lock trap in the header). **Keep** Supabase init and the legacy-account delete path only as founder question Q2 decides. Until then, keep the existing "Delete Account" row, shown only when a persisted session exists;
- `lib/app_env.dart` and its `AppEnv.validate` call (its only use is validating `SUPABASE_URL`), with `test/app_env_test.dart` removed together with it;
- the unused interstitial preload in `ad_service.dart` (`preloadInterstitial`, `_cachedInterstitial`).

Acceptance:
- (a) `grep -rn "fromEnvironment" lib` → only the AdMob unit ids in `services/ads_config.dart:58-64` and `SupabaseConfig` (if Q2 keeps it). Note both in the commit message.
- (b) `grep -rniE "isLive|liveLookup|authDisabled|API_BASE_URL|in this build|this version does not|unavailable right now|sample|demo|placeholder|coming soon|simulator|AI-powered|AI assistant|Impact Advisor|Welcome back|Get Started" lib` → 0 hits. A remaining legitimate hit, such as `_StorageUnavailableApp`, needs a one-line justification in the commit.
- (c) Release iOS build: `strings build/ios/iphoneos/Runner.app/Frameworks/App.framework/App | grep -ciE "AI-powered|immigration AI assistant|LIVE LOOKUP UNAVAILABLE|Sign in with Apple|Continue as guest|tools.processingTimes|advisor.chat"` → 0. This checks the binary Apple inspects.
- (d) Every feature is reachable from the first screen on a fresh install, with no account, in every locale.

**M2. Core job: the case file — receipts, status log, processing time and priority date.**
- **Case fields.** Extend `TrackedCase` with JSON-backward-compatible fields: existing saved cases must load. Old keys are read as before, and new fields default to null.
  - `formType`: a picker of common forms (I-130, I-140, I-485, I-765, I-131, I-751, I-90, N-400, I-129F, I-821D, I-601A) or free text;
  - `person`: free text, e.g. "Mom";
  - `receiptDate`: the date on the I-797;
  - optional `priorityDate`, `category` (F1–F4, EB1–EB5, free text) and `chargeability` (country, free text).
- **Status log.** Keep it as is: `recordStatus`, common wordings, notes, delete entry, "Check on USCIS", which copies the receipt and opens egov.uscis.gov. Add **"days in each stage"**: the gap between consecutive recorded statuses, and "<N> days since receipt" from `receiptDate`. Use calendar days, computed in local time.
- **Posted processing time (user-recorded).** On a case, "Add the time USCIS posts for this form" takes:
  - the figure the user reads on egov.uscis.gov/processing-times, in months, plus the office or service-centre name as text;
  - an optional "receipt date for case inquiries" date as shown there;
  - the date they looked (defaults to today).

  The case then shows a bar: "Month 9 of 14.5 — posted by USCIS for <office>, as you recorded on <date>". If the user's `receiptDate` is on or before the inquiry date they recorded, the case shows "By the date you copied from USCIS, this case is outside the posted time — you can ask USCIS about it", with a link to the official page. The wording must say the figure is the user's copy of the USCIS figure. **The app never invents or estimates a processing time.**
- **Priority date (user-recorded bulletin).** On a case with `priorityDate`, "Record this month's cutoff" takes the bulletin month and the Final Action date (or "C" for current) that the user reads in the Visa Bulletin ("Open the Visa Bulletin" link). The case shows "Current" or "Your date is <N> months behind the cutoff you recorded for <month>", plus a list of recorded cutoffs and the month-to-month movement **computed only from the user's entries**. With no entries: "Record a cutoff from the Visa Bulletin to see where your date stands."
- **Acceptance.**
  - Unit tests: old-format JSON (fixture copied from today's `TrackedCase.toJson` shape) loads; new fields round-trip; days-in-stage over 3 entries; the inquiry comparison on, before and after the date; behind/current computation, including "C".
  - A widget test: add receipt `IOE0123456789` with form I-765 and person "Ana" → record "Case Was Received" dated 30 days ago → relaunch (fresh providers over the same mock prefs) → the case shows "30 days since receipt" and its status.

**M3. Signature: Windows + Citizenship clock.**
- **Documents.** "Add a card or document" with a type and a date. Each type maps to one rule constant, and each constant has `quote`, `sourceUrl` and `checkedOn: 2026-10-12`. Types:
  - **10-year green card** → I-90 window opens 6 months before expiry;
  - **Conditional green card** (2-year) → I-751 joint window = the 90 days before expiry, with "file before expiry" urgency in the last 30 days and "past the window" after expiry ("See USCIS — late filing needs an explanation", linking `uscis.gov/i-751`). The app gives no legal advice beyond the quoted rule;
  - **EAD** → I-765 renewal opens 180 days before expiry, with "USCIS asks for at least 90 days" marked;
  - **Passport, visa, I-94 or other** → expiry reminder only, no rule (labelled "expiry you entered");
  - **Notice deadline** (RFE due, biometrics, interview, oath) → the date the user typed, labelled "from your notice".
- **Window engine.** `lib/domain/windows.dart` is pure Dart with no Flutter imports. Input: documents, cases and the clock. Output: a sorted list of `WindowEvent {person, title, opensOn, closesOn?, dueOn?, kind, ruleQuote?, sourceUrl?}`. Use calendar arithmetic (`DateTime(y, m - 6, d)` style with month-end clamping, so 31 Aug minus 6 months is 28 or 29 Feb). Never use 30-day months.
- **Citizenship clock** (`lib/domain/citizenship_clock.dart`, a port of `shared/n400.ts:90-123` plus trips).
  - Inputs: the "resident since" date on the card, the basis (5-year, or 3-year married to a US citizen), and trips `{departed, returned, note}`.
  - Outputs:
    - the anniversary date, and the earliest filing date (anniversary minus 90 calendar days);
    - days abroad, counting **only the full days between departure and return**, since both of those days count as present (Policy Manual quote, §3);
    - days present against 913 or 548 in the window ending today, and against the earliest filing date;
    - each trip's flag: none, ">6 months and <1 year: may break continuous residence", or "≥1 year: breaks continuous residence". Take "6 months" as calendar months from the departure date, and show the rule quote.
  - When a ≥1-year trip exists, the clock must say plainly that the date shown assumes no break and that a break restarts the period, and link the Policy Manual chapter. It must **not** compute a "new" date as if it were legal advice. Same for the ">6 months" case: the flag says it *may* break continuity, with the quote.
  - **Plan a trip.** Enter planned dates and see the before/after of the earliest filing date's physical-presence count and any new flag. Nothing is saved unless the user taps "Add trip".
- **Docket view** (the home screen, M7): the next 12 months of `WindowEvent`s for every person, grouped "Now open", "Next 90 days", "Later". Each row shows a countdown in Fira Mono. Tapping a row shows the date maths ("Card expires 14 Mar 2027 → window opens 15 Dec 2026") and the quoted rule with its link.
- **Acceptance.** Unit tests, all with fixed dates (inject a clock; no `DateTime.now()` inside the domain code):
  - I-751: expiry 2027-03-14 → window 2026-12-14…2027-03-14. The off-by-one convention ("90-day period immediately before") is decided in code and documented in the test.
  - EAD 2027-01-31 → opens 2026-08-04 (180 days); the 90-day marker is 2026-11-02.
  - I-90: 2027-08-31 → 2027-02-28 (month-end clamp).
  - N-400: resident since 2022-01-15, 5-year → anniversary 2027-01-15, earliest 2026-10-17. The 3-year spouse path gives the same with 3 years.
  - Feb 29 resident date in a non-leap anniversary year (convention documented).
  - Physical presence: a trip departing 2025-06-01 and returning 2025-06-10 → 8 days abroad.
  - Flags at 182, 183, 364 and 365 days, with the thresholds documented.
  - Plan-a-trip does not persist.
  - A widget test: add a conditional card expiring in 60 days → Docket shows it under "Now open" with the I-751 quote.

**M4. Official updates for your forms only (replaces the generic news feed).**
- On each case with a `formType`, show "Federal Register: Form <X>": the 20 newest USCIS documents matching `"Form <X>"` (§3 query). Each item shows type chip (Rule, Proposed rule, Notice), date, title, abstract (2 lines), "effective <date>" and "comments close <date>" when present, and "Open on federalregister.gov".
- A "Hide paperwork notices" toggle (default on) hides titles starting "Agency Information Collection Activities". The setting persists.
- Sources (M7) keeps one combined list: USCIS, ICE and CBP, newest first, the existing `newsFeedUrl`. There is no general news, no non-government source and no "News" tab. This keeps the app clear of daily-pulse.
- Results are cached per form with the fetch time. Offline shows the cache with "Saved <date> · offline". No cache and no network → "Needs a connection to federalregister.gov." with Retry. 8 s timeout. An HTTP error → "The Federal Register didn't answer. Try again."
- **Acceptance.** A parser test against a **real recorded** response, saved under `test/fixtures/fr_form_i765.json` from the §3 query on the build day. Also: the paperwork filter test, the offline-cache test, and a widget test for the error state.

**M5. Depth: persistence, search, export, empty/error/offline states.**
- **Persistence.** Everything in M2–M4 survives relaunch, through `StorageService` with new keys for documents, trips, cutoffs and cached Federal Register results. "Delete everything on this phone" in Settings clears all of them; existing `clearAll` plus the new keys.
- **Search and filter.** On Cases: a text search over receipt, label, person, form and status; filter chips by person and form; sort by receipt date, last status date or name. On Docket: a person filter.
- **Export.**
  - "Copy case file" puts plain text on the Clipboard: every case with its status history and days-in-stage, every document with its window dates and rule citation, the Citizenship clock summary with its trip list, generation date, and "Not affiliated with USCIS. Not legal advice." It extends the existing `_exportText`.
  - "Copy trip list" exports trips as `departed – returned (N days abroad) note`, one per line, in the order the N-400's travel section asks for (newest first). This is the user's own list, so no claim is made about the form's exact layout.
  - `share_plus` only after the Podfile.lock check; Clipboard meets the criterion.
- **Empty states, specific to this app.**
  - Docket: "Add a receipt or a card's expiry date, and the windows that matter appear here."
  - Clock: "Enter the 'Resident since' date from the front of your green card."
  - Trips: "No trips yet — add each trip abroad since you became a resident."
  - A case's processing time: "Add the time USCIS posts for <form>."
- **Errors.** No blank screens and no endless spinners. Storage failure keeps `_StorageUnavailableApp`.
- **Acceptance.** Tests for search and filter, the export text (golden string), and "delete everything" clearing every new key.

**M6. The 2.1(a) launch crash: prove a clean launch of the release build.**
- The crash log Apple attached is not in the repo or `.dist` (searched 2026-10-12). Its cause is **not verified**.
- Required: `flutter build ios --release --no-codesign` succeeds. The release build installs and launches on the newest available iOS simulator (iOS 26 or 27, whichever is installed), and the developer screenshots the first screen and the Docket with data. Do the same with **Firebase config absent and network off**, since the crash path most worth testing is startup without network.
- Startup order stays guarded (`AglCrash.init` → storage in try/catch → `runApp`). Supabase init, if kept, must not be awaited before `runApp` without a timeout. Add a 5 s timeout, or move it after `runApp`.
- `integration_test/`: one test that boots `main()` with mocked prefs and finds the Docket.
- **A physical-device run is a human step and is not verified by the office** (note it in the review notes honestly).

**M7. Own identity: home layout, onboarding, colour, type, shape, icon, splash, name.**
- **Home: "Docket", no tab bar.**
  - One home screen, top to bottom: a **date strip** (today's date and the next event's countdown, large, in Fira Mono); the Docket groups (M3); a **People** row of chips (filter); then two compact cards: **Cases** (count, the most recent status change, opens the Cases list) and **Citizenship** (earliest filing date, physical-presence progress and civics progress; opens the clock and, from there, the civics trainer).
  - A single "Add" button opens a sheet: Receipt / Card or document / Notice deadline / Trip abroad.
  - Settings and Sources open from app-bar icons. Everything else is a pushed page.
  - Delete `home_shell.dart`. Acceptance: `grep -rn "BottomNavigationBar\|NavigationBar(" lib` → 0.
- **Ads.** `BannerAdSlot` stays out of any shell: exactly **one** placement, at the end of a case's detail page below the status log. None on Docket, onboarding, civics quiz, clock or Settings. Acceptance: `grep -rn "BannerAdSlot()" lib` → 1 hit. Any interstitial is founder question Q4.
- **Onboarding: "What's on your desk?"** Shown once, re-openable from Settings, and it replaces the three generic pages:
  - Card 1: three chips the user taps to say what applies (a pending USCIS case / a green card or EAD with an expiry / working toward citizenship).
  - Card 2: the matching first form opens: the add-receipt sheet, the add-card sheet, or the "Resident since" date.

  One line on card 1 says what the app is: "Your family's case file — statuses you record, and the filing windows they open." Plus "Not affiliated with USCIS or any government agency." No "Get Started", no "Welcome". The final button reads "Add it" or "Skip for now".
  - Acceptance: shown once, Skip works, and each chip opens its sheet.
- **Palette: "Ink and highlighter"** (a marked-up paper file; deliberately **not** flag navy and red, so it does not look official). `ThemeMode.system`, with a hand-built `ColorScheme`, not `fromSeed`.
  - Light: surface `#F1F0F6`, cards `#FFFFFF`, text `#1B1A2E`, **primary ink indigo `#2D2A6E`** (on-primary white), highlighter `#F6D743` (used only as a fill behind "Now open" windows, with ink text on it), deadline `#9C2F1F` (past or last-30-days), muted `#5D5B73`, divider `#D9D7E4`.
  - Dark: surface `#14131F`, cards `#1F1D2E`, text `#ECEBF3`, primary `#A9A4F0`, highlighter `#E9C93A` (dark text on it), deadline `#F08A75`, muted `#A3A1B8`.
  - None of these hexes appears in another spec in `specs/` (grep of all `#xxxxxx` in `specs/*.md`, 2026-10-12).
  - Acceptance: `grep -rhoiE "002868|BF0A30|1D4ED8|1E40AF|DBEAFE|1E3A8A|16A34A|DCFCE7|D97706|FEF3C7|DC2626|FEE2E2|0891B2|CFFAFE|F9FAFB|F3F4F6|E5E7EB|D1D5DB|9CA3AF|6B7280|4B5563|374151|1F2937|111827|7C3AED|059669|4F46E5|9D174D|FCE7F3" lib` → 0. A test asserts contrast ≥ 4.5:1 for text/surface, on-primary/primary, ink/highlighter and deadline/card, in both modes, using `computeLuminance`.
- **Typography.**
  - **Fira Sans** (Regular, Medium, SemiBold, Bold) for UI and headings. **Fira Mono** (Regular, Medium) for receipt numbers (shown `IOE 012 345 6789`-style, 3-3-3-4), every date, countdown and day count.
  - Use `FontFeature.tabularFigures()` on numbers.
  - Bundle the TTFs under `assets/fonts/` with both `OFL.txt` files and declare them in `pubspec.yaml`. No runtime font fetch. Non-Latin locales (zh, hi, ar, ko) fall back to the platform font, which is expected.
  - Sources resolve: curl `github.com/google/fonts/raw/main/ofl/firasans/FiraSans-Regular.ttf` 200 (456,996 B), `-Medium` 200 (457,248 B), `-SemiBold` 200 (489,028 B), `-Bold` 200 (489,720 B), `ofl/firasans/OFL.txt` 200 (4,370 B), `ofl/firamono/FiraMono-Regular.ttf` 200 (174,596 B), `-Medium` 200 (173,428 B), `ofl/firamono/OFL.txt` 200 (4,371 B).
  - No other spec in `specs/` names Fira (grep, 2026-10-12).
- **Shape.**
  - Cards are "file folders": 4 px corners, a 1 px divider border, no shadow, and a 6 px ink tab on the left edge of each Docket row, coloured by kind (ink = window, deadline red = due or past, muted = expiry only).
  - Buttons have 4 px corners. Chips are 4 px, not pills. Countdowns sit on a highlighter fill when a window is open.
  - Acceptance: `grep -rn "AppRadius.full\|circular(9999)\|circular(16)\|circular(12)" lib` → 0.
- **Icon.**
  - Hand-built art, flat with no gradient: an ink-indigo `#2D2A6E` square holding a white manila-folder silhouette with a highlighter-yellow `#F6D743` stripe across a calendar-date row. No checkmark, no document-with-lines, no Material glyph.
  - Regenerate every `AppIcon.appiconset` size and the Android mipmaps and adaptive icon. `Uscis-Case` is not in `scripts/generate_app_icons.py` (grep → 0 hits), so nothing will overwrite it.
- **Splash.**
  - A new `LaunchScreen.storyboard` with background `#2D2A6E` and the white folder mark. Android `launch_background.xml` uses the same.
  - Acceptance: shasum ≠ `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`.
- **Names.**
  - One `kAppName` constant drives `MaterialApp.title`, `CFBundleDisplayName`, `CFBundleName`, the Android `app_name` resValue (`android/app/build.gradle*:91`) and `title_activity_main`.
  - Until the founder picks a name (Q1), use **"Case Tracker for USCIS"**, which matches Play's `title` and the current home-screen name. The pubspec description becomes "A family's immigration case file with filing windows."
  - Acceptance: a test reads `ios/Runner/Info.plist` and `android/app/src/main/res/values/strings.xml` and asserts both equal `kAppName`.

**M8. Honest, app-specific copy; template furniture trimmed.**
- **Remove:** "Get Started", "Welcome back", "What You Can Do", "My USCIS Updates" (the app fetches no updates), the hero pills, the 4-tile feature grid, "Quick Links" on home (they move to Sources), the AI and Impact Advisor copy, the `sample.*`/`auth.*` strings, the "Case Tracker for USCIS (Flutter) v1.0.2" footer (`profile_screen.dart:219`), and both `debugPrint('LAUNCHING PRIVACY POLICY URL…')` calls.
- **Settings becomes one page**, merging Profile:
  - **Your file**: "Delete everything on this phone" (cases, documents, trips, cutoffs, cached results, civics progress), and "Copy case file".
  - **Federal Register**: the hide-paperwork toggle.
  - **Language**: `AglLanguageScreen` may stay (shared infrastructure).
  - **Privacy choices**: the UMP row stays (legal).
  - **Privacy policy, Support.**
  - **Delete account**: only when a legacy session exists (Q2).
  - **Version**: read from the build.
  - **Sources**: the existing `GovernmentSourcesScreen`, plus the rule quotes from §3 with their URLs and "checked on" date.
- **Keep the non-affiliation statement**: "Not affiliated with USCIS or any government agency. Not legal advice." It stays on the Docket footer, onboarding card 1, Sources and the export (legal; Google Play government-apps policy). Keep `legal.affiliation` identical in every locale, as `compliance_test.dart` asserts today.
- **Strings.** New user-facing strings go through `AppStrings` with all 9 languages, so `i18n_completeness_test` stays green and is not weakened. The verbatim uscis.gov rule quotes are English-only *quotations* and join the test's `englishOnly` set with a comment saying why, the same treatment the legal strings get today. Translations written by the developer are flagged in the commit and the review notes as **not reviewed by a native speaker**.

**M9. Proven.**
- `flutter analyze` is clean and `flutter test` passes, with no failures, including the currently failing one removed with the code it tests (below).
- **New tests cover:** the M2 model migration and computations; the M3 window engine and Citizenship clock (every case listed in M3); the M4 parser on a real fixture, the paperwork filter and the cache; M5 search, filter, export and delete-everything; M6 integration boot; M7 onboarding once, no tab bar, one `BannerAdSlot`, palette contrast, fonts declared and on disk, storyboard shasum, `kAppName` equal in plist and strings.xml; and an extended `release_sanity_test` (or `no_invented_data_test`) that greps `lib/` for the M1(b) strings.
- **Tests that go, only together with the code they test:**
  - the `backend host` group in `test/release_config_test.dart` (3 tests, including today's failing one);
  - the backend parts of `test/api_service_test.dart` (status, processing times, bulletin, AI, NVC; keep and adapt the news parser tests);
  - `test/app_env_test.dart`;
  - the login and auth parts of any test that pumps `LoginScreen` or uses `AppConfig.authDisabled`;
  - the alert, profile and tab-shell parts of `widget_test.dart`, `foldable_layout_test.dart`, `accessibility_test.dart` and `case_tracking_flow_test.dart`.

  `foldable_layout_test`, `accessibility_test` and `case_tracking_flow_test` must be **rewritten** for the Docket, Cases and case pages, not dropped. The commit message lists every removed test by name. No other test is deleted or skipped.
- **Look at it.** Launch on the iOS simulator. Add two people's receipts, a conditional card expiring in 60 days, an EAD, a resident-since date and two trips, plus one planned trip. Take screenshots of: Docket, a Window detail with its quote, Citizenship clock, Plan a trip, a case with status log, processing-time bar and Federal Register list, and onboarding card 1. No white screen, no overflow at 200% text, RTL (Arabic) checked on Docket.
- Commit path-limited (never `fastlane/`, `Podfile.lock` or `project.pbxproj` while they carry others' edits) and push to `main`.

### SHOULD (if time allows, in this order)

- **S1. Local reminders** for window openings and notice deadlines (`flutter_local_notifications`): on-device scheduling only, no push server. This needs the Podfile.lock check, and it can hold off until the lock is clean.
- **S2. "Your local answers" for civics.** The 2025 test asks location-dependent questions (state senators, representative, governor, state capital). The user types their own answers once, with links to senate.gov and house.gov finders, and the quiz shows them. No data source is invented.
- **S3. iOS-native feel.** On iOS, `CupertinoIcons`, Cupertino page transitions, a large-title `CupertinoSliverNavigationBar` on Docket and a `CupertinoDatePicker` for dates. Material stays on Android.
- **S4. Share sheet** (`share_plus`) for the case file and the trip list, after the Podfile.lock check.
- **S5. Calendar file.** Export Docket events as an `.ics` file through S4.

## 5. Store impact (proposed; store-compliance applies it later. Nothing was written to `store/` or `fastlane/`)

**Name.** Founder decision, Q1. The current App Store name "USCIS Case Lookup" is false (no lookup) and leads with an agency name. Candidates, with availability **not checked**: "Filing Window: Immigration Dates", "Case File: Green Card & N-400", "Docket — Immigration Case File". Keeping "USCIS" out of the name lowers the government-impersonation risk. "for USCIS" can stay in the subtitle or keywords as a descriptor. Play `title` can stay "Case Tracker for USCIS" or follow the new name. The bundle id is permanent either way.

**Category.** Keep `UTILITIES` primary (Immivision and Lawfully are Utilities per the iTunes API). Secondary: `PRODUCTIVITY`.

**Subtitle (≤30):** `Filing windows & case file` (26)

**Play short description (≤80):** `Your family's USCIS receipts, status log, card expiries and filing windows.` (75)

**Promotional text (≤170):** `Add your receipts and card expiry dates and see every window that opens: I-751, EAD renewal, green card renewal and your N-400 date, adjusted for trips abroad.` (159)

**Description (draft).** It drops the "—— Heading ——" skeleton and the opening "<AppName> keeps…" line, and it does not reuse the house ads paragraph:
> Immigration paperwork runs on dates: when a card expires, when a renewal window opens, when you can apply for citizenship, how long a case has sat in each stage. This app keeps those dates for everyone in your family, on your phone, and turns them into one docket.
>
> Add a receipt number with its form and receipt date, and record each status you see on the official USCIS Case Status page — the app opens it with your receipt number copied. You get a dated history with the days spent in each stage. Copy the processing time USCIS posts for your form and see where your case stands against it; record the Visa Bulletin cutoff for your category and see how far your priority date is.
>
> Add a card's expiry and the app shows the window that opens for it, with the USCIS rule quoted under the date: the 90 days before a conditional green card expires (I-751), up to 180 days before an EAD expires (I-765), six months before a 10-year green card expires (I-90). Enter the date you became a resident and your trips abroad, and the citizenship clock shows the earliest day you can file the N-400, your days of physical presence, and any trip long enough to put continuous residence at risk. Plan a trip before you book it and see what it changes.
>
> For each form you're tracking, see the newest USCIS notices and rules from the Federal Register. Practise the official civics questions for the 2025 test (128) and the 2008 test (100).
>
> No sign-in. Your cases, dates and trips stay on your phone. The app does not fetch case statuses from USCIS.
>
> Not affiliated with USCIS, the Department of State or any government agency, and not legal advice. Check anything that matters against the official source.
>
> Free with ads from Google AdMob, shown on case pages. Where the law requires it you choose about ad personalisation first, and can change it in Settings.

**Keywords (100 chars, the limit):** `green card,n400,i751,ead renewal,i90,citizenship date,physical presence,receipt,priority date,civics`

**Screenshots to retake.** All live from the build, with entries the capturer types at capture time. These are the user's own kind of data, not seeded fixtures, and no frame is Settings or onboarding-only. Fixes 2.3.3, and the iPhone 1/3/4 near-duplicates. Sizes: iPhone 6.9", iPad 13", Play phone and tablet.
1. Docket with "Now open" (I-751) and "Next 90 days" rows across two people.
2. Window detail: date maths plus the quoted uscis.gov rule.
3. Citizenship clock with trips and one flagged trip.
4. Plan a trip, before and after.
5. A case: status log with days-in-stage, and the processing-time bar.
6. Optional: Federal Register list for Form I-765.

The current fastlane screenshots carry someone else's uncommitted edits. Coordinate with their owner; do not overwrite them from this workstream.

**Play feature graphic.** Rebuild it from the new folder icon and a Fira Sans wordmark on `#2D2A6E`.

**Review notes** (rewrite for this app only; drop the "2. DEVICES…" skeleton and the simulator / "a build that cannot start never ships" paragraph):
- **What changed:** "Earlier builds contained an AI assistant, a risk advisor, a live status lookup and a sign-in screen that only appeared when a build-time backend address was set. Those screens, the switch and the sign-in code have been deleted. Every feature is reachable from the first screen, without an account, identically in every region."
- **Path:** "First screen → tap what applies → add receipt IOE0123456789 (any 3 letters + 10 digits), form I-765 → open it, 'Record status'. Then 'Add' → 'Card or document' → Conditional green card, expiry 60 days from today → the Docket shows the I-751 window with the USCIS rule. 'Citizenship' → enter a resident-since date and a trip." A receipt number typed by the reviewer is not a demo login.
- **External services:** Federal Register API (public notices by form number), Google AdMob, Firebase Crashlytics and Analytics, and links to uscis.gov, egov.uscis.gov, travel.state.gov and ceac.state.gov. Supabase only if Q2 keeps legacy deletion. "The app does not contact USCIS; statuses are recorded by the user."
- **Audience,** in place of the pasted subtitle: "Families in the US managing several USCIS filings over years — green-card holders with conditional cards or EADs to renew, people counting toward naturalization who travel abroad, and sponsors tracking a relative's petition — who need the dates and filing windows in one place."
- **Test devices:** state only what was actually used. The physical-device run is a human step, **not verified** by the office (M6).
- **Translation:** new screens are translated by the developer, not yet reviewed by native speakers. Legal and rule quotations are English.

**Age rating (2.3.6).** Set "Advertising: Yes" in App Store Connect (Apple asked). That is a store-compliance or founder action in ASC; it is not in this repo.

**Privacy label.** `store/privacy/Uscis-Case.json` today declares EMAIL_ADDRESS, NAME and USER_ID "linked to you" (from `_derived_from.account: true`). If Q2 removes sign-in and legacy accounts, drop those three. If legacy deletion stays, they arguably stay until those accounts are gone. Device ID, advertising, crash, product-interaction and performance data stay. The Federal Register query sends only a form number, which is public data, to a government API.

**differentiation (store json):**
- §1: rewrite to the new screens.
- §2: the audience above.
- §3: replace the TODO with §2's competitor paragraph, naming Immivision and Lawfully (live status, which we do not do) and Green Card Trips (trip counting, which we also do), and stating the gap as the family file plus rule-quoted windows. Keep the "descriptions only" caveat.
- §6: "Not CalcMaster or any date calculator in the portfolio; no other app on the account handles immigration."
- §4 (beta) and §9 remain founder items.

**`_name_note`.** Resolve it with Q1.

## 6. Out of scope

- **Fetching case status, NVC/CEAC status, processing times or Visa Bulletin data.** No keyless source answered (§3), and scraping bot-protected pages is out. Neighbour or receipt-range lookups, for the same reason.
- **Any AI chat or "risk analysis".** There is no backend, and an LLM giving immigration advice is a legal-advice risk the office cannot take (Charter §6). Removed, not deferred.
- **Accounts, sync, Supabase feature tables, push notifications, background fetch.**
- **General news or non-government sources** (daily-pulse territory).
- **Legal advice:** computing deadlines that the rule quotes do not state, judging whether a trip "broke" residence, or late-filing advice.
- **Immigration-court (EOIR), DOL/PERM tracking.**
- **The web, RN, Electron and extension code in this repo.**
- **A home-screen widget.**

## 7. Not verified

- **The cause of the 2026-09-29 launch crash** on iPhone 17 Pro Max / iOS 27.0. The crash log is not on disk. M6 tests a clean release launch on the simulator only.
- **Whether travel.state.gov, egov.uscis.gov/processing-times and the Case Status page open in Safari on a phone.** All three returned Cloudflare 403 to curl from this machine (behind a proxy; `HTTPS_PROXY` is set). The developer must open each from the simulator and screenshot it. If one fails, the link stays (it is the official page) and the copy must not promise more.
- **USCIS's exact wording for the processing-times "case inquiry" date.** Its page returned 403. M2's label must be checked against the live page in the simulator.
- **The 548-day figure** is derived from the half-time rule; no page saying "548" was fetched (§3).
- **The I-751 window's day-count convention** (whether the 90-day period includes the expiry day), and **the Feb 29 anniversary convention.** USCIS's early-filing calculator page (`uscis.gov/forms/uscis-early-filing-calculator`) returned 403. Document the conventions in tests and say "about" nowhere; show exact dates.
- **Competitor behaviour beyond App Store descriptions.** WebSearch is disabled ("Internet mode is not enabled").
- **Store-name availability** for any Q1 candidate.
- **Whether legacy Supabase accounts exist for this app.** The `delete_user` RPC is not applied in production (MA-044, per the office's notes), so "Delete Account" may fail today for anyone who has such an account.
- **Physical-device behaviour,** and whether Apple accepts a resubmission.
- **Process note (my own action).** While checking hosts I ran `python3 scripts/verify_api_hosts.py --print` in `agl-manifest`. That script **rewrites `docs/api-hosts.json`**, a file under `docs/` that this workstream must not edit. `git status` now shows ` M docs/api-hosts.json` (4 insertions, 13 deletions: `api.aviationapi.com` and `www.flightschoolcandidates.gov` NODATA entries removed and `www.fts.tsa.dhs.gov` added, all from the PilotEnRoute code). I did not revert it, because I cannot tell whether the file already held another workstream's uncommitted run, and reverting could destroy it. The docs owner should decide whether to keep or `git checkout` it.

## 8. Founder questions (Charter decisions; the office does not take them)

- **Q1. Keep and rename, or retire?** The USCIS case-tracker category has free apps with 318k and 173k ratings that fetch statuses, which this app cannot do. This spec bets on a different job: a family's case file with rule-quoted filing windows plus the trip-adjusted Citizenship clock. The clock alone already exists in "Green Card Trips". If the founder judges this not distinct enough under 4.3(b), the alternative is **retiring the iOS app** (Charter §8). It is LIVE on Play. If kept, pick a store name (§5 candidates, availability not checked) and whether "USCIS" stays in the name.
- **Q2. Legacy accounts.** Are there any real accounts from the earlier sign-in version? If none: remove Supabase, `supabase_config.dart` and the Delete Account row entirely, and drop EMAIL/NAME/USER_ID from the privacy label. If some exist: keep the legacy delete path, and MA-044 (`delete_user`) must be applied in production for it to work (Charter §2).
- **Q3. A real Visa Bulletin feed.** Showing the bulletin in-app without user entry needs a server job that fetches the State Department page monthly into a Supabase table, which means a migration and a production deploy (Charter §2). Approve building it, or keep the user-recorded cutoffs in M2?
- **Q4. Ads.** One banner on case pages only, and the unused interstitial preload removed. Add an interstitial anywhere? Money decision (Charter §3).
- **Q5. Resubmission.** Replying to Apple and resubmitting stay frozen under the 5.6 hold (MA-043, Charter §1). The 2.3.6 age-rating change in App Store Connect also needs whoever holds ASC access.
- **Q6. Beta testing statement.** differentiation §4 needs a true account of TestFlight testing, which only the founder can give.
