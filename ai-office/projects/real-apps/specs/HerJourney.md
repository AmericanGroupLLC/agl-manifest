# Spec: HerJourney, a private record of your reproductive life that shows what your own cycles are doing

- **Author:** product-manager (AI office), 2026-10-12
- **Repo:** /Users/spatchava/agl/HerJourney, branch `master`, base `2d5430619a2fdf06079ad1bcd2aa2db3f6f57ac2` (`git rev-parse HEAD`, read today)
- **Plan:** projects/real-apps/plan.md (acceptance criteria 1–7)
- **Store state:** Apple rejected 1.2.0 under 4.3 / 4.2.6 (`.dist/rejections.json` key `HerJourney`, message 1 is the shared 4.3/4.2.6 text). Message 2 adds **2.3.3**: "The 6.7' iPhone screenshots only display a splash screen." Google Play: PRODUCTION_DRAFT_STAGED.
- **Overlap ruling followed:** overlap.md G5. HerJourney keeps reproductive life stages (cycle, conception, pregnancy, menopause). MyHealth drops its cycle tracker (`MyHealth/lib/screens/profile/profile_screen.dart:456-457` `if (_p.sex == 'female') _cycleSection()`, MyHealth HEAD `b0cb774`). HerJourney must **not** duplicate MyHealth's general record of vitals, medicines and activity.
- **Uncommitted changes by other people in this repo (do not touch):** `fastlane/**` (metadata, screenshots) and `ios/Podfile.lock` (`git status --short`, read today). Every file this spec changes is clean today. Before editing `ios/Runner/Info.plist`, `ios/Runner/Runner.entitlements`, `ios/Runner/Base.lproj/LaunchScreen.storyboard` or `ios/Runner.xcodeproj/project.pbxproj`, run `git status` again. If any of them has someone else's edits by then, stop and report it. Do not work around it.

---

## 1. Problem

### What the app is today (read from `lib/`, 11,427 lines across 39 files)

The startup path is a splash, then a 5-step onboarding (`welcome_screen.dart`: name, age, journey, cycle details), then a hand-rolled 4-tab bar. `root_scaffold.dart:22-56` lists Home, Health, Vitals and Profile, plus an **AI** tab that appears only when `LLM_API_KEY` is defined at build time. `env/prod.json` has no `LLM_API_KEY` (read today), so release builds have no AI tab.

| Screen | What works | What is shallow, dead, off-job or wrong |
|---|---|---|
| Home `home/home_screen.dart` (1064 lines) | Cycle status card. A month calendar built from the user's own period date, cycle length and logs (`CycleCalendar`). Quick Log for period, symptoms, mood and intimacy, with history. | The greeting "Good morning/afternoon/evening" is generic. `_HealthMetricsStrip` shows heart rate and sleep, with "Not synced" (lines 679, 741, 771) when Apple Health is not connected. Those are vitals, which belong to MyHealth. `_QuickTip` and the phase cards give **unsourced** health claims, e.g. "Flaxseeds for estrogen balance", "Evening primrose oil", "Magnesium and B6 can reduce PMS symptoms significantly", "Estrogen is rising. Great time for new projects". |
| Health `health/health_screen.dart` + 4 views | You pick a journey. **Cycle** shows the calendar and log tiles. **Conceive** shows a fertile-window estimate (`estimateUpcomingOvulation`), an ovulation calculator, LH-test and intimacy logs. **Pregnancy** shows weeks and trimester from a due date, a due-date calculator and a symptom log. **Menopause** has a symptom log. | The journey switch is session-only. `AppState.instance` is in memory and separate from the saved `UserProfile.journeyPhase`. The "Coming Soon" pill code (lines 96-142) is dead because `Journey.comingSoon` returns `false` (`models/journey.dart:61`), but the template string is still compiled in. The Menopause view is a symptom log and nothing else. Its only richer feature is LLM guidance, which release builds never show. |
| Vitals `health/health_dashboard.dart` (562 lines) | Reads steps, heart rate, HRV, sleep, SpO2, temperature, weight and respiratory rate from Apple Health or Health Connect. | This is **a general vitals record**, which is MyHealth's job (G5). Also, `ios/Runner/Runner.entitlements` holds only `com.apple.developer.applesignin`, with **no `com.apple.developer.healthkit`** (read today). I expect HealthKit authorization to fail on a real iPhone, but I have not verified that on a device. |
| Profile `profile/profile_screen.dart` (1052 lines) | Journey chip, cycle and period length, last-period date, calculators, support email, Privacy choices. | **Account (Optional)**: Continue with Apple (line 310) and Continue with Google (line 321) sign in to Supabase. The screen itself says sync is "planned, not enabled yet" (lines 254-256), and line 134 says nothing uploads. So sign-in does nothing for the user. It is also the portfolio's shared sign-in family. Height, weight and BMI belong to MyHealth. |
| AI `assistant/`, `llm/ai_insights_screen.dart`, `assistant/chat_screen.dart`, `services/llm_service.dart` (~1,860 lines) | Nothing in release, because of the gate above. | Dead code that would send reproductive-health data to `api.openai.com` if a key were ever built in. It carries the 'AI-powered cycle insights' tell (`assistant_screen.dart:96`). |
| Scan `scan/scan_screen.dart`, `scan/report_analysis_screen.dart` (876 lines) | **Unreachable.** `grep -rn ScanScreen lib` shows no reference outside its own files. | It contains 'OCR is not enabled in this build' (line 105) and "the values below are a sample" (line 235), meaning **invented lab values**. It also adds camera and photo-library permissions to `Info.plist` (lines 73, 75) for a feature nobody can open. |
| History `history/log_history_screen.dart` | Entries listed by day, with delete. | Only the **last 90 days** are loaded (`app_provider.dart:174`, `log_history_screen.dart:29`). There is no search, no filter, no edit and no export. |
| Log sheet `widgets/log_sheet.dart` | Chips plus a note. | **No date field.** Every entry is stamped "now" (`quickLog`, `app_provider.dart:183`), so past periods cannot be entered. |

**The core gap in the job itself.** Predictions never learn from the user's history. `UserProfile.nextPeriodDate` is always `lastPeriodDate + cycleLength` (default 28, `user_profile.dart:83-87`), and the app never measures a single cycle from the logs. With the 90-day cap and no back-dating, it could not measure one anyway. A cycle tracker that cannot tell you your own cycle lengths is a calendar with a fixed offset.

**Things that are good and stay:** the period-start logic (`startsNewPeriod`, `latestPeriodStart`, and delete-restores-previous-start in `app_provider.dart`, with 20 tests in `test/period_tracking_test.dart`), calendar-day arithmetic that survives daylight saving, the honest "no period logged" prompts guarded by `test/no_invented_data_test.dart`, and the on-device SQLite store (`services/database_service.dart`).

### Why Apple called it a template (tells measured for this app)

- The Supabase sign-in family (`profile_screen.dart:310,321`, `services/auth_service.dart`, `lib/app_env.dart`, `config/app_config.dart` Supabase/Google/Apple ids) and the duplicated `services/error_reporter.dart`.
- The byte-identical `ios/Runner/Base.lproj/LaunchScreen.storyboard`: `shasum` gives `3f6a9b27d80dda327ce7df82d4887e3adbac50e4` (measured today), the same as 36 other apps.
- 'Coming Soon' (`health_screen.dart:142`), 'OCR is not enabled in this build' (`report_analysis_screen.dart:105`), 'AI-powered cycle insights' (`assistant_screen.dart:96`) and 'Get Started' (`welcome_screen.dart:207`).
- `GoogleFonts.interTextTheme` (`theme/app_theme.dart:25`), one of 13 Inter apps. The palette is the stock "pink app for women": rose `#E85E8A` and lavender `#8B6DC7` on `#FBF6F9` (`theme/app_colors.dart:11-34`), plus a pink-to-purple gradient button.
- The shared shell: a bottom bar with `AglAdBanner` directly above it (`root_scaffold.dart:76`, guarded by `showsAds`). The shared `privacy_choices_tile.dart` (0.52 similarity with RideZap).
- Icon (viewed `assets/icon/app_icon.png`): a pink six-petal flower on a dark plum gradient. It is generic, and it says nothing about cycles or stages.
- Store: '——' description headings. The review notes use the "2. DEVICES…" skeleton with "Intended audience: Cycle, pregnancy, menopause", which is the subtitle pasted in. They say both "No advertising SDK." and "Google AdMob (ads)…" in the same section 5, which contradict each other. The 6.7" screenshots were rejected under 2.3.3. The current `iphone69-01.png` (viewed today) is a mid-scroll list.
- The app overlaps MyHealth (vitals strip, Vitals tab, BMI) and BodyQuest (generic wellness tips).
- Home-screen name: `CFBundleDisplayName` = "Her Journey", while the store name is "HerJourney" (`PlistBuddy`, read today).

---

## 2. User

**A woman in her late 30s to early 50s who has tracked her period for years, notices that her cycles are changing, and wants to know whether the change is real and what to tell her clinician.** She will not put reproductive data on a server. She may also be trying to conceive later in life, or be pregnant, and wants the same private record to follow her from one stage to the next.

Secondary: anyone of any age who wants one on-device record across cycle, conception, pregnancy and menopause, with no account.

Not for: general health logging (vitals, medicines, activity, which is MyHealth), contraception (the app must never imply that), or learning anatomy (BodyQuest).

## 3. Product

### Core job
**Keep one private record of your periods and life-stage events on your phone, and see what that record says.** That covers your real cycle lengths, when the next period is likely (as a range, not one confident day), your fertile window, pregnancy weeks, and the time since your last period. You can hand all of it to a clinician as a report.

### Signature feature: **Cycle Record**, measured from your own logs, with menopause-transition markers and an appointment report

1. **Measured cycles.** Every completed cycle is computed from the logged period starts: its length (start to next start) and its bleeding days. The record shows the median, the shortest and longest of the last 6, and the spread. The cycle-length chart marks the 21–35-day band. Source: NHS, "ranging from every 21 days to every 35 days… between 2 and 7 days" (`curl -L https://www.nhs.uk/conditions/periods/` returned HTTP 200 today and I grepped the sentence).
2. **Range predictions.** Once 3 or more cycles are complete, the next period is shown as a window: last start plus the shortest of the last 6, to last start plus the longest, with the median as "most likely". The fertile window is derived the same way. With fewer than 3 cycles, the app uses the length the user set and says so ("from the 28 days you set").
3. **Menopause-transition markers (STRAW+10).** These are computed on-device from the bleeding pattern only, using the published STRAW+10 definitions (Harlow et al. 2012, `https://pmc.ncbi.nlm.nih.gov/articles/PMC3340903/`, HTTP 200 today). Sentences quoted from the page:
   - *Early transition:* "a persistent difference of 7 days or more in the length of consecutive cycles. Persistence is defined as recurrence within 10 cycles of the first variable length cycle."
   - *Late transition:* "amenorrhea of at least 60 days".
   - *Menopause:* the final period is confirmed after 12 months without one. The app shows "days since your last period" and the calendar date on which 12 months would be reached.

   Each marker is a card titled "What your logs show". It shows the cycles that triggered it, a "Why this matters" text, the source link, and the line "A pattern in your logs, not a diagnosis."
4. **Appointment report.** A PDF built on the device with the pure-Dart `pdf` package (pub.dev API today: latest 3.13.1, tags `license:apache-2.0`, platforms android and ios) and shared through the existing `share_plus`. You choose the range: 3, 6 or 12 months, or everything.
   - Contents: a cycle table, the median and range, bleeding days, symptom counts by kind, LH-test results, pregnancy dates if any, and the markers above.
   - Notes are **off by default** and switched on with a toggle.
   - CSV export of every entry is also available.

**Competitors.** Web search is disabled in this session (the WebSearch hook returned "Internet mode is not enabled"). I checked existence, rating and description text with Apple's keyless iTunes Search and Lookup API today (`itunes.apple.com/search`, `/lookup?id=…`). I have not installed any of these apps. Each gap below is based on the store description only.

| App (id, rating, count) | What the description says | Gap HerJourney fills |
|---|---|---|
| Flo Cycle & Period Tracker (1038369065, 4.74, 1,994,592) | Covers all stages. "Perimenopause Score to follow symptom changes", "Menopause Timeline to understand the perimenopause phases", "Cycle report summaries you can download". Has an Anonymous Mode, and Premium is a subscription. | The perimenopause tools are described as symptom scores and education. The description does not mention cycle-length markers computed from your bleeding history. The data is held by a company (an anonymous mode exists). HerJourney keeps everything on the device, needs no account, and computes the STRAW+10 bleeding-pattern markers. |
| Clue Period & Cycle Tracker (657189652, 4.76, 405,510) | "from first period to perimenopause". Perimenopause mode. GDPR, a subscription, 400+ articles. | The description says nothing about on-device-only storage or bleeding-pattern staging. Not verified beyond the description. |
| drip period & cycle tracker (1584564949, 4.0, 58) | "Everything stays on your device", graphs of cycles, "Not another cute, pink app." | It is on-device like HerJourney, but the description lists no pregnancy, menopause or life-stage support and no report. |
| Balance – Menopause & Hormones (1503345959, 4.73, 1,135) | Symptom and period tracking, "Generate a Health Report to take to your next healthcare appointment", community, Balance+ subscription. | It covers menopause only, with no cycle, conception or pregnancy stages. On-device storage is not stated. |

**Honest angle:** the big trackers cover every stage but keep your data with them and describe perimenopause as symptom scores. The private tracker (drip) does not follow you into pregnancy or menopause. HerJourney is the one record that stays on your phone through every stage, measures your actual cycles, and flags the published menopause-transition patterns in your own bleeding history, with a PDF to take to an appointment. All competitor gaps above rest on store descriptions only.

Buildable now by one developer: pure Dart statistics over data already in SQLite, `fl_chart` (already a dependency), the `pdf` package (pure Dart, no keys), `share_plus` (already a dependency). No network, no keys, no server.

---

## 4. Acceptance criteria

### MUST (what Apple has to see for a real, distinct app)

**M1. No sign-in, no AI, no dead code. Everything stays on the device.**
- Delete the sign-in feature:
  - Files: `services/auth_service.dart`, `services/secure_store.dart`, `lib/app_env.dart`.
  - Code: the `Supabase.initialize` and `AppEnv.validate` blocks in `main.dart:44-65`, the Account (Optional) section of Profile, and the Supabase, Google and Apple ids in `config/app_config.dart`.
  - Remove `com.apple.developer.applesignin` from `ios/Runner/Runner.entitlements`.
- Delete the AI and dead features:
  - AI: `screens/assistant/`, `screens/llm/`, `services/llm_service.dart`, the `chat_messages` table (a DB migration drops it), and every `AppConfig.hasLlmKey` branch.
  - Scan: `screens/scan/`, plus `NSCameraUsageDescription` and `NSPhotoLibraryUsageDescription` in `Info.plist`.
- Remove the `pubspec.yaml` dependencies that only those features used, after a grep proves no other use: `supabase_flutter`, `google_sign_in`, `sign_in_with_apple`, `crypto`, `flutter_secure_storage`, `http`, `image_picker`.
- Tests that cover only removed features (`account_deletion_test.dart`, `sync_claims_test.dart`, `app_env_test.dart`, and the LLM cases in `no_invented_data_test.dart`) are deleted **in the same commit as the feature**. The commit message lists each deleted test file. No test is deleted for any other reason.
- Proof: after the change, `grep -rniE "supabase|sign in with|continue with (apple|google)|openai|llm|in this build|coming soon|not enabled|sample" lib` returns nothing. Quote the output.
- TestFlight records 0 installs across all builds (`store/apps/HerJourney.json` differentiation §4, measured 2026-10-12), so no account holder loses anything. The founder confirms this in F1.

**M2. Off-job features removed (G5): no vitals record, no generic tips.**
- Delete the Vitals tab (`health_dashboard.dart`), Home's `_HealthMetricsStrip`, the height, weight and BMI fields and getters, and the `HealthMetrics` reads of steps, heart rate, HRV, sleep, SpO2, temperature, weight and respiratory rate.
- Delete `_QuickTip`, the nutrition tip sheets and the phase "advice" lines (`home_screen.dart` ~945-1000, 265-296). The phase *name* and day of cycle stay.
- Apple Health / Health Connect is reduced to **menstrual flow only** (S1). If S1 is not built in this pass, remove HealthKit and Health Connect entirely, along with their store claims.
- Test: no screen contains "Heart Rate", "Steps", "BMI", "Sleep" or "Not synced".

**M3. The record is complete: back-dating, full history, one saved stage.**
- The log sheet gains a date field. It defaults to today, accepts any past date and never a future one. A back-dated period entry runs through the existing `startsNewPeriod` logic in date order, so entering an old period never moves predictions backwards incorrectly.
- Onboarding (M6) offers "Add the periods you remember": up to 6 start dates. Each becomes a normal period log tagged `backfilled` in metadata, so the history and the PDF can show where it came from.
- Remove the 90-day cap. `_loadLogs` and History read all entries. Queries stay indexed by date. With 2,000 entries, History must open in under 1 second in a widget test using `sqflite_common_ffi`.
- The life stage is **one persisted value**. Delete the in-memory `AppState`, and the Health tab reads and writes `UserProfile.journeyPhase`. Every stage change is stored as a dated `stage_change` entry, so the record shows "Trying to conceive from 3 Mar 2026" and so on.

**M4. Signature: Cycle Record (the screens in §3).**
- **Pure Dart `CycleStats`** (`lib/record/cycle_stats.dart`, no Flutter imports, injectable `today`). From flow entries and stage changes it computes:
  - period starts and completed cycles (length, bleeding days)
  - the median and min–max of the last 6
  - the prediction window (rule in §3.2)
  - fertile window = predicted start − 14 days, both ends, then −5 days
  - **STRAW+10 markers:**
    - (a) early: two or more pairs of consecutive cycles whose lengths differ by 7 days or more, with the second occurrence within 10 cycles of the first;
    - (b) late: any gap of 60 days or more between period starts, or 60 or more days since the last start;
    - (c) 12 months: days since the last start, plus the date on which 365 days is reached.
  - Pregnancy and after-birth intervals (from stage changes) are **excluded** from cycle statistics.
- **Record screen:**
  - stat tiles: median cycle, range, bleeding days and cycles counted
  - an `fl_chart` bar chart of the last 12 cycle lengths with the 21–35-day band shaded, labelled "Typical range (NHS)", and a semantics summary for screen readers
  - the marker cards, shown when the stage is Menopause, or in any stage when marker (a) or (b) fires and the user's age range (M6) is "40 or over"
  - an "Appointment report" button
- **Prediction honesty.** Home, Calendar and Conceive all use `CycleStats`. With fewer than 3 completed cycles, every prediction carries "from the length you set". With 3 or more, every prediction shows a range.
- **PDF report** (`lib/record/report_pdf.dart`):
  - range chooser; notes toggle (off by default)
  - header "Prepared on this phone by HerJourney on {date}. Not a diagnosis."
  - a cycle table, symptom counts, LH results, stage changes and markers with their source URL
  - shared as `HerJourney-report-YYYY-MM-DD.pdf` through `Share.shareXFiles`
  - CSV export of every entry from Settings, with columns `date,type,tags,note,backfilled`
- **The report must be generated without the network** (test with the network unavailable).

**M5. Depth: search, filter, edit, delete-all, and empty, error and offline states.**
- **History:** search across tags and notes; filter chips by kind (Period, Symptoms, Mood, Intimacy, LH test, Pregnancy, Menopause, Stage); a date-range filter; and **edit** an entry (date, tags, note), which re-runs the period-start logic. No-match state: "No entries match 'xyz'".
- **Settings → "Erase everything on this phone":** a confirmation, then the database and preferences are wiped and the app returns to onboarding. This replaces account deletion, because there is no account.
- **Empty states with real next steps:**
  - Today with no periods: "Log your last period to start your record."
  - Record with fewer than 2 starts: "Two period starts make your first measured cycle."
  - The PDF with no entries in range: the button is disabled and reads "Nothing logged in this range".
- **Error state:** if the database fails to open, a full-screen message shows the error and a Retry button. A blank screen or an endless splash is not acceptable. Today `initialize()` stores `_error` but nothing displays it (`app_provider.dart:72`).
- **Offline:** every feature works in airplane mode. The only network users left are AdMob and Firebase, infrastructure that fails silently.

**M6. Own identity, distinct from MyHealth (primary `#338CEB`), BodyQuest (terracotta `#B8432F`, Nunito/Fredoka), DriftDate (aubergine `#5C2A4D`), the other specs written so far, and the stock "rose and lavender" women's-app look.**
- **Colour: "dusk and clay".**
  - seed/primary dusk indigo `#3B3561`
  - period clay `#C4583E`
  - fertile marigold `#D29A3A`
  - pregnancy moss `#5F7F52`
  - menopause heather `#7E6BA8`
  - paper background `#FAF6F0`
  - text `#26232F`
  - No pink-to-purple gradients. A dark variant uses `#1B1926` with the same accents.
  - Uniqueness check, run today: `grep -rlis` for each of `3B3561 C4583E FAF6F0 D29A3A 5F7F52 7E6BA8` over the 42 `*/lib` and `*/mobile/lib` folders under `~/agl` and over `specs/` found no match. The developer reruns this before committing.
- **Typography:** bundle **Source Serif 4** (`SourceSerif4[opsz,wght].ttf`) for headings and every number (cycle day, lengths, weeks), and **Karla** (`Karla[wght].ttf`) for UI text. Both are OFL. I confirmed with the GitHub API today that the folders `google/fonts/ofl/sourceserif4` and `ofl/karla` exist and contain those files and `OFL.txt`.
  - Declare both under `fonts:` in `pubspec.yaml` with their `OFL.txt`. Remove `google_fonts` if nothing else needs it. No runtime font fetch.
  - A grep for "source serif", "sourceserif" and "karla" over the same 42 `lib` folders, every `pubspec.yaml` and `specs/` found no match.
- **Home ("Today") is a stage dial, not a card list.** A `CustomPainter` ring changes with the stage:
  - **Cycle / Conceive:** one segment per day of the current cycle; bleeding days in clay; the fertile window in marigold; the prediction window as a soft band (the uncertainty is visible); a today marker. In the centre, "Day 17", and under it "next period likely 2–7 Nov".
  - **Pregnancy:** 40 week-segments in three trimester arcs. Centre: "Week 22 · 126 days to go".
  - **Menopause:** 12 month-segments since the last period. Centre: "214 days since your last period", plus the 12-month date.
  - Under the dial: one "Log" button that opens the kind picker, and today's entries.
  - Every ring has a full semantics label, e.g. "Cycle day 17. Next period likely between 2 and 7 November."
- **Shell:** 3 destinations: **Today**, **Calendar** and **Record**. History is reached from Record, Settings from a gear in the Today header.
  - iOS: `CupertinoTabBar`, CupertinoIcons or custom glyphs, and `CupertinoPageTransitionsBuilder`.
  - Android: a Material `NavigationBar`.
  - The hand-rolled bar (`root_scaffold.dart:79-170`) and the `FadeForwards` transitions go.
- **Ads placement:** the banner leaves the shell. Unless F2 says otherwise, the only banner is inline at the end of the History list. There is none on Today, Record, log sheets, the report or onboarding. Interstitials stay capped by `agl_ads`, fire only on Calendar↔Record moves, and never after a log is saved. Update `ads_placement_test.dart` to the new rule.
- **Onboarding (3 screens, all new copy):**
  1. "Where are you right now?" offers the four stages as illustrated rows. Pregnancy asks for the due date, Menopause for the date of the last period.
  2. "Add the periods you remember" (M3), skippable.
  3. "This stays on your phone." A plain privacy statement: no account, nothing uploaded, how to export and erase. It also asks for an **age range** (under 30 / 30–39 / 40 or over / prefer not to say), used only for M4's marker rule.
  - No name or birth date is asked. `isFirstLaunch` stops depending on `name` (`app_provider.dart:54`).
  - Remove "Welcome to HerJourney", "Get Started", "Your personal health companion", "Skip for now" and "Start My Journey".
- **Icon:** not a flower and not a glyph on a gradient. A paper `#FAF6F0` square holding an open ring drawn in dusk indigo, with one clay arc (a period) and one marigold dot (ovulation): the Today dial in miniature. Produce `assets/icon/app_icon.png` (1024 px, no alpha) and regenerate with `flutter_launcher_icons`. Set `adaptive_icon_background` to `#FAF6F0`.
- **Launch screen:** a new `LaunchScreen.storyboard` with background `#FAF6F0` (r 0.980, g 0.965, b 0.941) and a new `LaunchImage` (the ring mark only, no text). The `shasum` must differ from `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`. The Flutter `_SplashScreen` in `main.dart:139-180` matches it, or is removed if startup is fast enough.
- **Home-screen name:** set `CFBundleDisplayName` to `HerJourney` (today it is "Her Journey").
- **Settings copy is HerJourney's own:** "Your record" (export CSV, appointment report, erase everything), "Predictions" (cycle and period length you set, used until 3 cycles are measured), "Ads & privacy" (the existing `PrivacyChoicesTile` stays because it is legally required for consent, with this app's subtitle), "Language" (the existing shared screen may stay), and "About" (version, support email, privacy policy, terms).

**M7. Honesty.**
- Remove claims the app does not deliver: "Week-by-week guidance & tracking" (`welcome_screen.dart:387`), "Optimize fertility" (line 380) and "Help us predict your cycle accurately" (line 520).
- Remove `Journey.comingSoon` and the pill code (`health_screen.dart:96-142`).
- Every prediction carries the basis it was computed from (M4).
- The Conceive card keeps "Not a method of contraception."
- No value appears on screen unless it was computed from the user's entries.
- `test/no_invented_data_test.dart` is extended to the dial, Record and PDF (fresh profile → prompts only, no dates, no numbers).
- Medical source URLs used in the app (NHS periods, PMC3340903, and any others the developer adds) are curl-checked for HTTP 200 after redirects, and the output is quoted in the commit or the QA report.

**M8. Tests (plan criterion 6).**
- `flutter analyze` is clean and every test passes. Do not run `dart format`.
- New unit tests for `CycleStats`:
  - zero, one, two, three and twelve cycles
  - spotting-only entries ignored
  - back-dated entries inserted out of order
  - pregnancy intervals excluded
  - STRAW (a) fires on lengths 28, 36, 29, 38 and does not fire on 28, 36, 29, 30, 31, 30, 29, 28, 30, 29, 30, 37 (second jump outside 10 cycles)
  - STRAW (b) fires on a 61-day gap and not on 59
  - the 12-month date across a leap year
  - prediction window min/median/max
  - daylight-saving boundaries (use the existing `period_tracking_test.dart` style)
- Widget tests:
  - onboarding has no "Sign in" or "Get Started"; a back-dated log moves the dial
  - History search, filter and edit
  - "Erase everything" returns to onboarding with an empty DB
  - the Record empty state
  - the PDF bytes are non-empty and start with `%PDF`, and contain the cycle count, with the network unavailable
  - CSV columns
  - the iOS shell renders `CupertinoTabBar` under `debugDefaultTargetPlatformOverride = TargetPlatform.iOS`
- Keep and pass `accessibility_test.dart`, `foldable_layout_test.dart`, `i18n_test.dart`, `period_tracking_test.dart` and `release_sanity_test.dart`.
- Commit path-limited (`git add lib test pubspec.yaml pubspec.lock assets ios/Runner/Info.plist ios/Runner/Runner.entitlements ios/Runner/Base.lproj ios/Runner/Assets.xcassets android/app/src/main/res`). Never `git add -A`, because `fastlane/` and `ios/Podfile.lock` belong to someone else. Push to `master` after the tests pass.
- Build and launch on the iOS simulator and screenshot Today, Record and the PDF share sheet (memory: "Build it and look at it").

### SHOULD

- **S1. Apple Health / Health Connect, menstrual flow only.**
  - Import past `MENSTRUATION_FLOW` (up to 2 years) as `backfilled` period entries, so a new user's Record fills in on day one. Keep writing logged flow.
  - Requires `com.apple.developer.healthkit` in `Runner.entitlements` and the HealthKit capability on the App ID (F3). Shrink the `NSHealthShareUsageDescription` and `NSHealthUpdateUsageDescription` text to menstrual flow only. Verify on a physical iPhone; until then, report it as **not verified**.
- **S2. After-birth stage:** postpartum bleeding and return-of-cycle tracking, excluded from cycle stats until the first period after birth.
- **S3. Pregnancy week cards** with sourced text (NHS "week-by-week" pages, each URL curl-checked). They must not be written from memory.
- **S4. A local reminder** ("period likely starts in 2 days") using `flutter_local_notifications`, scheduled on-device, off by default.
- **S5. Symptom-by-phase view:** for each symptom, the share of entries falling in each cycle phase, computed from the user's own logs.

---

## 5. Data source

- **On-device only.** SQLite through `sqflite` (`services/database_service.dart`, schema v4 → v5: drop `chat_messages`, add an index on `date`, add the `backfilled` metadata convention and the `stage_change` log type) and `shared_preferences` for the profile.
- **Reference constants with verified sources** (curl today):
  - NHS periods page (HTTP 200): the 21–35-day range and 2–7 bleeding days.
  - STRAW+10, PMC3340903 (HTTP 200): the ≥7-day / within-10-cycles rule, ≥60 days, and 12 months.
- **No Supabase, no public API, no keys.** The PDF library is `pdf` 3.13.1 (Apache-2.0, per the pub.dev API today).
- **Infrastructure kept:** agl_ads (AdMob plus UMP consent), agl_observability (Crashlytics and Analytics; no log content is sent), agl_i18n.

## 6. Store impact (for store-compliance to apply. I did not edit any store or fastlane file)

**Name and subtitle**
- Name: "HerJourney: Cycle to Menopause" (30 characters).
- Subtitle: "Private cycle record & report" (29).
- Founder confirms (F4).
- Keywords: `cycle,period,perimenopause,menopause,ovulation,fertile,pregnancy,due date,private,offline,report,irregular`.

**Description (draft)**
It does not open with the app name, has no '——' or ALL-CAPS headings, and contains one ads sentence:
> Your periods, your pregnancy, your menopause — one record that never leaves your phone. Log a period (including ones from months ago) and HerJourney measures your actual cycles: how long they run, how much they vary, and when the next one is likely, shown as a range instead of a single guess. If your cycles start changing in your 40s, the Record screen shows whether your own logs match the patterns clinicians use to describe the menopause transition (STRAW+10): cycles that swing by 7 days or more, gaps of 60 days, and the date you would reach 12 months without a period. Make a PDF of any 3, 6 or 12 months to take to an appointment, or export every entry as CSV. Trying to conceive? See a fertile window built from your own cycle range and log LH tests. Pregnant? The home dial counts weeks and trimesters from your due date. There is no account and nothing you log is uploaded; erase everything from Settings at any time. HerJourney is free with ads from Google AdMob; nothing you log is shared with Google, and you can change ad consent in Settings. Not medical advice and not contraception.

**Promotional text:** "Measures your real cycles, flags menopause-transition patterns in your own logs, and makes a PDF for your clinician. No account."

**Screenshots (retake all; the 6.7" set was rejected under 2.3.3)**
Use iPhone 6.9"/6.7" and iPad 13", in this order:
1. The Today dial (cycle stage) with a prediction window.
2. The Record chart and stat tiles.
3. A marker card in the Menopause stage.
4. The PDF report preview.
5. The Pregnancy dial.
6. History search with filters.

Drive them through `integration_test/store_screenshots_test.dart`, which enters past periods **through the app's own UI** (the back-dated log sheet), so every number shown comes from the app's own computation. No login and no splash frames.

**Review notes**
Rewrite in prose, not the "2. DEVICES…" skeleton, and drop the contradictory "No advertising SDK." Content:
- what the app is, with the real audience from §2, not the subtitle
- "no account; to see the Record and markers in under a minute: onboarding → Menopause → add the periods you remember (e.g. six dates 30–70 days apart) → Record tab"
- AdMob and consent location (Settings → Ads & privacy)
- "everything is stored on the device; Settings → Erase everything"
- HealthKit only if S1 shipped and was verified
- devices tested: only what was actually run. Do not repeat the simulator-only promise. Apple asked for physical devices.
- Remove the ACCOUNT DELETION paragraph (no account exists any more). Change the review contact name away from "App Reviewer" (F5).

**Privacy label (`store/privacy/HerJourney.json`)**
- Remove EMAIL_ADDRESS, NAME and USER_ID (no sign-in).
- Re-evaluate HEALTH: under Apple's definition, data is "collected" only when it is transmitted off the device. HerJourney transmits none, so HEALTH should be removed. Store-compliance confirms.
- Keep DEVICE_ID and ADVERTISING_DATA (AdMob) and CRASH_DATA.
- Remove camera and photo usage strings from `Info.plist` (M1).

**Play:** the same copy changes. Make a new feature graphic in the paper/indigo palette with the dial, not the Flutter logo or a monogram. Data-safety form: no account, no health data collected.

## 7. Out of scope

- Any server sync, account, partner sharing or community.
- AI chat or generated advice.
- Lab-report scanning.
- Vitals, medicines, activity, weight or BMI (MyHealth).
- Contraception or any "safe days" feature.
- Paid features.
- Changing MyHealth: removing its cycle section is MyHealth's spec, and this app does not depend on it.
- Editing store JSON, fastlane metadata or docs.
- Submitting to Apple, replying to Apple or promoting on Play (Charter §1; the 5.6 freeze, MA-043).

## 8. Founder questions

- **F1.** Confirm removing Sign in with Apple/Google and Supabase from HerJourney. TestFlight shows 0 installs, so no user account is lost. Default if unanswered: remove it.
- **F2.** Should a reproductive-health app show ads at all? Default: one inline banner at the end of History only, with capped interstitials between Calendar and Record. The alternative is no ads in HerJourney.
- **F3.** Enable the HealthKit capability on the HerJourney App ID (Apple Developer account action) so S1 can ship. If not, Apple Health is removed from the app and from the listing.
- **F4.** Approve the new store name "HerJourney: Cycle to Menopause" and subtitle "Private cycle record & report".
- **F5.** Which real person or role is named as the App Review contact, instead of "App Reviewer"?

---

## Evidence log (commands run for this spec)

- `git -C HerJourney rev-parse HEAD` returned `2d5430619a2fdf06079ad1bcd2aa2db3f6f57ac2`; `git branch --show-current` returned `master`; `git status --short` showed only `fastlane/**` and `ios/Podfile.lock` modified or untracked.
- `grep -rn ScanScreen lib` found only self-references, so the scan screens are unreachable. `env/prod.json` has no `LLM_API_KEY`.
- `shasum ios/Runner/Base.lproj/LaunchScreen.storyboard` gave `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`. `PlistBuddy Print :CFBundleDisplayName` gave `Her Journey`. `Runner.entitlements` contains only `com.apple.developer.applesignin`.
- iTunes Search/Lookup (keyless) for Flo, Clue, drip and Balance: ids, ratings and description sentences as quoted in §3.
- `curl -L` returned HTTP 200 for `pmc.ncbi.nlm.nih.gov/articles/PMC3340903/` and `www.nhs.uk/conditions/periods/`, and the quoted sentences were extracted from the HTML. pub.dev API: `pdf` 3.13.1, `license:apache-2.0`.
- Viewed `assets/icon/app_icon.png` (pink flower on plum) and `fastlane/screenshots/en-US/iphone69-01.png`/`-02.png` (mid-scroll Health list; due-date calculator).
- Not verified: HealthKit behaviour on a physical device; the competitors' in-app behaviour (descriptions only).
