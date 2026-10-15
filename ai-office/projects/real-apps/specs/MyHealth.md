# Spec: MyHealth becomes a health record that writes your "since last visit" brief

- **Author:** product-manager (AI office), 2026-10-12
- **Repo:** /Users/spatchava/agl/MyHealth, branch `master`, base `b0cb77453f50f0d22bcdd76bb9c70c0ac4d52494`
- **Plan:** projects/real-apps/plan.md (acceptance criteria 1–7)
- **Store state:** Apple rejected 1.0.0 under 4.3 / 4.2.6. `.dist/rejections.json` key `MyHealth` holds 2 threads: the shared 4.3/4.2.6 text and the shared 2.1 "Information Needed" text. Google Play: PRODUCTION_DRAFT_STAGED.
- **Overlap ruling followed:** overlap.md G5. MyHealth is the personal health record: vitals, medicines, labs, doctors, activity, workouts, sleep and food diary. It drops the cycle tracker (HerJourney), demo food ordering and vendors (and stays out of GroceryMatch's job), and the anatomy screen (BodyQuest). MyCard's spec (line 118) relies on MyHealth's insurance screen storing nothing, so MyHealth drops that screen and does not become a card wallet.
- **Dirty files at base (someone else's, do not touch):** everything under `fastlane/` (11 modified, 13 untracked screenshots) and `ios/Runner.xcodeproj/project.pbxproj` (`git status --short`, run today).

---

## 1. Problem

### What the app is today (read from `lib/` at the base sha)

MyHealth is a port of a React Native app: **192 Dart files, 37,798 lines** (`find lib -name '*.dart' | xargs wc -l`), with **about 80 routes** in `router/app_router.dart`. You reach the 4-tab shell (Health · Diet · Workout · Explore) only after a Supabase sign-in wall, a 6-page onboarding and a consent gate. It opens on **Workout** (`app_router.dart:258`), and the first card there says *"Steps, calories and sleep aren't available yet. MyHealth doesn't read Apple Health or Health Connect in this version."* (`screens/tabs/workout_tab.dart:140`), above activity rings full of dashes.

| Area | What actually works (persisted unless stated) | What is shallow, dead, fake or off-job |
|---|---|---|
| **Medicines** `screens/medicine/*`, `MedicineStore` | Add (name, dose, times, weekdays), detail page with a 14-day adherence strip, "I took it now", archive. Persisted. | **No reminders.** The "Times" field does nothing because there is no notification plugin in `pubspec.yaml`. There is no start date, stop date or change history. `priceCents` is a leftover field. |
| **Vitals** `screens/vitals/*`, `VitalsStore` | Manual BP, glucose and weight with history. Other vitals keep only a "latest" override. | History is **capped at 100 readings per type** (`services/local_store.dart:273`), which loses data in a record app. The `VitalsSnapshot` model is shaped like HealthKit (ECG count, VO2 max, audio dB and more) with no source for most fields. Biological Age (`vitals/biological_age_screen.dart`) is an unsourced estimate, and it is enabled: `ClearancePending.biologicalAge = false`. |
| **Labs** `care/lab_reports_screen.dart` | Type 8 fixed fields and get "insights". | **Never stored** (its own header comment says "Never uploaded, never stored"). It compares values against hard-coded ranges marked *"Reference ranges are illustrative — a clinician must validate before release"* (`services/analysis/on_device_analysis.dart:72`). The camera "scan" reads nothing (no OCR). |
| **Doctors** `care/doctor_finder_screen.dart`, `services/npi_registry.dart` | Live CMS NPPES search by ZIP code. Verified today: HTTP 200. | The specialty box is free text. `taxonomy_description=Cardiology` returns **0** results (curl today, ZIP 10001), while `Cardio*` returns 5. "Save to favorites" is held only in screen state (`doctor_detail_screen.dart:133`) and is lost when you leave. There are no visits and no care team. |
| **Symptoms** `care/symptoms_log_screen.dart` | Body location, pain, duration, notes, persisted history | Fine. Keep it. |
| **Food diary** `diet/food_diary_screen.dart`, `nutrition/*`, `MealStore` | Log meals and daily macro totals. Barcode lookup by typed digits (Open Food Facts product API, HTTP 200 today). | **Food search is broken.** `nutrition_service.dart:51` calls `/api/v2/search?search_terms=`, and the v2 API ignores that parameter. For "oatmeal" curl returned `count: 4809285` (the whole database), and the first hit was a skyr. `cgi/search.pl?search_terms=oatmeal&search_simple=1&json=1` filters correctly (count 5461), but the GroceryMatch spec saw it answer 503 once, so it needs an error state. |
| **Activity / workouts** `activity/*`, `train/logger_screen.dart`, `workout/exercise_library_screen.dart` | Activity presets, set-by-set logger, exercise library. Persisted. | They are buried under a 25-route Train tree. Schedule keeps events in screen state only (`train/schedule_screen.dart` header). Stand-up "reminders" only change status text (`train/standup_screen.dart`). Send-to-Watch templates are "informational" (`train/templates_screen.dart`). The player is stubbed. Exercise detail shows **"Form video coming soon"** (`i18n/strings/train_strings.dart:74`, rendered at `train/exercise_detail_screen.dart:158`). |
| **Sleep** `sleep/*` | Wind-down breathing, a mood picker | No way to log sleep at all. The dashboard says "No sleep data… in this version" (`sleep_dashboard_screen.dart:31`). |
| **Off-job, demo or invented** | n/a | Cycle tracker (`profile/profile_screen.dart:456-542`, HerJourney's job). Vendor browse with "a generated menu", nearby delivery, and a checkout that is "Clearly labeled as a demo: NO payment is taken" with **invented prices** (`data/diary_data.dart:402` `unitPrice: 12.99`). Invented vendors ("Green Bowl Co.", `diary_data.dart:340`) on the Diet tab. Anatomy picker (BodyQuest). Bay Area trails and adventures. Run list (no GPS, so it can never fill). "Train together" built on seed data, marked "HONEST SAMPLE" (`social/shared_workout_screen.dart`). A badge grid where every badge is locked forever. Connected devices where nothing ever connects ("Not connected", "can't be connected in this version"). Tools hub whose manual log is session-only. Insurance card cost "insights" (MyCard's territory). Mental-health screening. Meal plan and diet suggestions from fixed data. |
| **Articles** `articles/*`, `services/articles_api.dart` | OpenFDA drug-label lookup (HTTP 200 today) | Live topics call MyHealthfinder **v3**, which is gone. `health.gov/myhealthfinder/api/v3/topicsearch.json` returned **HTTP 410** "version 3 has been removed" (curl today), so the screen always falls back to bundled links without saying so. |
| **Account** `auth/*`, `services/auth_service.dart` | Email/password, Apple, Google, guest | **No feature uses the account.** `Supabase.instance` appears only in `auth_service.dart` (lines 41, 166, 302, 396: sign-in, sign-up and the `delete_user` RPC). All data is in `shared_preferences`. `main.dart:50` still says the auth layer "falls back to a local demo session for the provisioned test accounts". The QA credentials themselves are gone from `lib/` (grep for `qaEmail` finds nothing). |
| **Onboarding** `onboarding/onboarding_screen.dart` | n/a | It asks for **"Approximate time of birth"** and birth city (`onboarding_strings.dart:23`), which a health app has no use for. Its permission rows (Apple Health "Read & write", Notifications, Location, Calendar, Motion; `data/onboarding_data.dart:49`) **request nothing**: a tap only runs `_granted.add(p.key)` (`onboarding_screen.dart:387`). The copy says "your AI-powered health companion… plus optional clinical integration" and "Care+" (`onboarding_strings.dart:5,29`). The app has no AI and no clinical integration. |
| **False or unfinished claims** | n/a | The profile badge says *"All health data is encrypted on your device and in transit"* (`profile_strings.dart:88`), but records are plain JSON in `SharedPreferences`. The in-app privacy page renders *"Draft placeholder — not legal advice. Replace with a counsel-reviewed policy before release."* and *"privacy@myhealth.app (placeholder)"* (`legal_strings.dart:18,36`; rendered at `legal/privacy_screen.dart:28`). |
| **Remote and switch logic (5.6 risk)** | n/a | A per-device A/B experiment `login_cta` (`state/experiment_provider.dart:30`). `ClearancePending` flags that grey out entry points (`theme/feature_flags.dart`). Neither is fetched remotely, but both are "switches" this account cannot afford. |

### Why Apple called it a template

Measured tells for this app:
- **Sign-in:** the Supabase sign-in family (`login_screen.dart`, `auth_service.dart`, `supabase_config.dart`, `app_env.dart`, plus the shared `error_reporter.dart`). The store record sets the shared demo login `qa@americangroup.ai` with `demo_account_required: true` (`store/apps/MyHealth.json`).
- **Shell:** a Material `BottomNavigationBar` with `AglAdBanner` directly above it (`screens/home/root_tabs.dart:35-36`), plus an interstitial on every tab switch (`root_tabs.dart:43`).
- **Launch screen:** the byte-identical storyboard. `shasum ios/Runner/Base.lproj/LaunchScreen.storyboard` gives `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, measured today.
- **Icon:** the glyph-on-gradient formula. I viewed `Icon-App-1024x1024@1x.png`: a white heart with a cross and an ECG line on a cyan-to-violet diagonal gradient.
- **Colour:** iOS system greys plus Tailwind hexes: `EF4444`, `F97316`, `6366F1`, `22C55E`, `A855F7`, `06B6D4`, `EAB308` (`theme/app_theme.dart:23-74`). Primary is `#338CEB`. No font is declared, so the system face renders.
- **Home-screen name:** `Myhealth` (`ios/Runner/Info.plist:20`), plus the mechanical "My" prefix.
- **Privacy label:** `store/privacy/MyHealth.json` is **byte-identical to yourtube's** (both shasum `09a253cb2b4dc6fcfce1f32fa2f49f9b1c398d5e`).
- **Screenshots:** the working-tree `fastlane/screenshots/en-US/iphone69-01.png` (someone else's uncommitted file, which I viewed) is **"Hike & Explore / Bay Area trails"**. The committed version at HEAD is the consent screen. Neither shows a health record.
- **Description:** "——" headings. It is built around what the app does *not* do ("does not read Apple Health… in this version"). The review notes use the numbered skeleton with "Intended audience: Activity, diet, sleep, vitals", which is the subtitle pasted in.

The product problem behind the tells: a 37,798-line port of a much bigger native app, with every RN screen kept and most of them hollow. Apple sees a generic "fitness tracker" whose main tab says it can't track, next to hikes, food ordering and a cycle tracker.

## 2. User

**An adult who manages ongoing care: two or more regular medicines, a condition that is checked at visits (blood pressure, blood sugar, cholesterol, thyroid), and more than one clinician.** Typical cases are a 45–70-year-old with hypertension or type 2 diabetes, or someone tracking a parent's medicines. Their real moment of need is **the 10 minutes before an appointment**: "What changed since I last saw Dr Patel? When did I stop the lisinopril? What were my readings? What did I want to ask?" Today they scroll through four apps and a paper folder.

Not for: athletes optimising training (MyHealth keeps a simple workout log and no training plans), reproductive health (HerJourney), learning anatomy (BodyQuest), grocery shopping (GroceryMatch), or storing insurance and ID cards (MyCard).

## 3. Product

### Core job
**Keep your own health record on your phone:** medicines with their history, readings, lab results, symptoms, sleep, activity, workouts and food, all on one searchable timeline, plus the clinicians who look after you.

### Signature feature: the "Since last visit" brief
Pick a clinician from your care team. MyHealth builds a one-page brief of **what changed since your last visit with that person**:
- medicines started, stopped or changed in dose, with dates
- dose adherence from your own logs
- readings with first, last, min, max and average
- lab results with the range printed on your report and the previous value
- the symptoms you logged
- a sleep and activity summary
- **FDA recall reports for the ingredients you take**
- your list of questions

You choose which sections to include, preview it, and share it as a PDF, or print it, or copy it as text. Nothing goes to a server. After the visit, "Log this visit" starts the next window.

**Competitors.** Existence, rating and description were checked today with Apple's keyless iTunes Lookup API (`itunes.apple.com/lookup?id=…`). Web search and WebFetch are disabled in this session ("Internet mode is not enabled"), and I have not installed any of these apps. Every gap below rests on the **store description only**.

| App (id, rating, count) | What its description says | Gap MyHealth fills |
|---|---|---|
| Guava: Health Tracker (1622255863, 4.80, 933) | "DOCTOR VISIT PREP — Create custom summaries of your medical history including symptoms, meds, and conditions"; connects to patient portals; "Guava uses AI to digitize" uploads | Visit prep **exists here**, so it is not our gap by itself. The description does not mention a **change-since-last-visit** view per clinician, recall checks, or working without portal connections and uploads. |
| Medisafe (573916946, 4.71, 101,460) | Reminders; "REPORT SHARING: … send it to the doctor or nurse as a visual informative PDF"; drug interaction warnings | A medication-centred report. The description mentions no labs, symptoms, care team or recall reports. |
| MyChart (382952264, 4.60, 726,206) | "To access MyChart, you must create an account with your healthcare organization"; After Visit Summary | It is tied to one health system's portal. It shows the clinic's record, not what the patient tracked between visits. |
| CareClinic (1455648231, 4.24, 2,310) | PHR sections (appointments, care teams, labs); "Data encryption on your device and server" | It is broad and server-backed. The description has no per-visit change brief and no recall check. |
| Bearable (1482581097, 4.77, 6,468) | Symptom correlations; "give your doctor a clear record" | Symptom- and mood-centred. No labs, medicine history or care team in the description. |

**Honest angle:** others either summarise your whole history (Guava, Medisafe) or show the clinic's own record (MyChart). MyHealth answers the narrower question patients actually walk in with, *"what changed since I last saw **this** doctor"*. It does that with no account, no portal and no upload, and it flags public FDA recall reports for what you take.

**Data for the signature, verified with curl today:**
- RxNorm `rxnav.nlm.nih.gov/REST/approximateTerm.json?term=lipitor%2020mg` returned HTTP 200 → "atorvastatin 20 MG [Lipitor]".
- `/REST/rxcui/617312/related.json?tty=IN+BN` returned HTTP 200 → ingredient "atorvastatin", brand "Lipitor".
- openFDA recalls `api.fda.gov/drug/enforcement.json?search=openfda.generic_name:"metformin"+AND+report_date:[20250101+TO+20261012]` returned HTTP 200 with `total 2` (Class II, 2025-04-02, "Ongoing"). A query with no recalls returns **HTTP 404 `NOT_FOUND` "No matches found!"**, which the code must treat as "none", not as an error.
- NPPES lookup by NPI `?version=2.1&number=1003000126` returned HTTP 200 with 1 result.
- **Not buildable:** RxNav's drug-interaction API `REST/interaction/list.json` returned **HTTP 404** today. Do not build interaction checks.

Buildable now by one developer: Dart only, using `pdf` (pure Dart) for the PDF, `share_plus` (already a dependency), and `flutter_local_notifications` for reminders. No keys.

---

## 4. Acceptance criteria

### MUST (what Apple has to see for a real, distinct app)

**M1. Cut to the core: remove the off-job, demo and hollow screens.**
Delete these screens, their routes, data files, strings and providers:
- **Overlap and demo:** the cycle section; `vendor_browse`, `nearby_delivery`, `order_checkout`, `nearby_food_search`, `meal_plan`, `diet_suggestions`, `food_scan`, and the Diet tab vendor strip; `train/anatomy_screen.dart` and `widgets/muscle_silhouette.dart`; hike; run.
- **Hollow:** `social/shared_workout`; badges; connected devices and the "Connected sources" rows; the tools hub; biological age; mental-health screening; the insurance card; prescription scan; nearby care; annual reports (the brief replaces it); state of mind; the sleep dashboard; the workout rings, metric detail, goals, RPE and wellness insights; the home dashboard; Explore; articles and the dead MyHealthfinder v3 call; `water_tracker`; binder; More.
- **Train tree:** everything except the set logger and the exercise library (remove the templates, programs, suggestions, player, schedule, stand-up, warm-up, cool-down, yoga, meditation, guided stretch, stretching, strength block, recovery day and progress report).
- **Plumbing:** `ExperimentProvider`, `theme/feature_flags.dart` (`ClearancePending`), `services/mock_data.dart`, `services/weather.dart`, `state/location_provider.dart` and `widgets/location_picker.dart` if nothing else uses them, and `widgets/futuristic_background.dart`.
- The OpenFDA drug-label lookup **moves** to the medicine detail page as "Label (OpenFDA)" for that medicine.

Targets:
- Measured: `lib/` is **at most 15,000 lines** and the route table has **at most 30 routes** (report both numbers).
- After deletion, no file under `lib/` matches `vendor|checkout|hike|anatomy|cycle|biological|shared_workout|badges|connected_devices|experiment`. Report the grep.
- Tests that only cover removed features are deleted **in the same commit as the feature**, and each one is listed in the commit message. At base those are parts of `app_env_test`, `auth_service_test`, `account_deletion_test`, `mock_data_test`, the `Experiment` cases in `providers_test`, and the hike, insurance and cycle cases (grep today). No test is deleted for any other reason.

**M2. No account. Open straight into MyHealth's own onboarding.**
- Remove `screens/auth/*`, `services/auth_service.dart`, `services/supabase_config.dart`, `lib/app_env.dart`, `state/auth_provider.dart`, `models/auth_user.dart`, `AppEnv.validate` and `Supabase.initialize` (`main.dart:43-67`) and the stale demo-session comment. Remove the dependencies `supabase_flutter`, `google_sign_in`, `sign_in_with_apple` and `crypto`, after a grep proves nothing else uses them.
- Remove `com.apple.developer.applesignin` from `ios/Runner/Runner.entitlements`. That file is clean at base. Do **not** touch `project.pbxproj`.
- Settings has no sign out and no delete account, because there is no account. **"Erase everything on this phone"** stays: it is the existing `eraseAllData()`, with a typed confirmation.
- On a fresh install the router goes to onboarding, then the record, never `/auth/*`.
- *Default if founder question F1 is unanswered: build it. No data is server-side. I did not verify the server-side user count.*

**M3. The record works end to end, and everything persists.** One local store per record type with create, edit, delete and a full history:
- **No caps:** remove the 100-reading cap. If the developer can do it safely, move records out of `SharedPreferences` into a single `sqflite` database or a JSON file in the app documents directory, with a one-time migration of existing `@myhealth/*` keys. **Either way, the existing records of a current install must survive the upgrade** (a migration test proves it).
- **Medicines:**
  - On add, search-as-you-type against RxNorm `approximateTerm` and store `rxcui`, ingredient and brand. Free text still works offline and is marked "not matched".
  - Store `startedOn` and `stoppedOn`. "Stop taking" replaces archive.
  - Every dose or schedule edit appends a **change event** (date, old, new).
  - **Reminders actually fire** at the scheduled times, using `flutter_local_notifications`. The system notification permission is requested the first time the user saves a medicine with a time, never during onboarding. Notification text is "Time for {medicine}" with **no dose and no condition** on the lock screen. Reminders are cancelled on stop or erase. Android needs `POST_NOTIFICATIONS` and exact-alarm handling.
  - Remove the "Times" UI if reminders cannot be delivered. A visible control that does nothing is not acceptable.
- **Readings:**
  - Types: blood pressure + pulse, weight, glucose (tagged fasting, before meal, after meal or random), temperature, SpO2.
  - Each entry has an editable date and time, a unit setting (kg/lb, mg/dL/mmol/L, °C/°F) and a note.
  - Trend chart for 30, 90 or 365 days.
  - **No app-invented "normal" verdicts.**
- **Labs (new store):**
  - A result has: test name (offline free text, with optional LOINC search from `clinicaltables.nlm.nih.gov/api/loinc_items/v3/search`, HTTP 200 today), value, unit, **the reference low/high printed on your report**, collected date, lab name and note.
  - H or L is flagged **only against the range the user typed**. Delete `analyzeLab` and its hard-coded ranges.
  - Per-test history and trend.
  - "What is this test?" opens MedlinePlus via MedlinePlus Connect by LOINC. Verified today: `connect.medlineplus.gov/service?…v.c=4548-4&knowledgeResponseType=application/json` returned HTTP 200 → "Hemoglobin A1C (HbA1c) Test", medlineplus.gov/lab-tests/….
- **Care team and visits:**
  - Search NPPES by ZIP code plus a **specialty picker** of real NPPES taxonomy terms, sent as a wildcard (`Cardio*`, `Family Medicine`). Or add a clinician by hand (outside the US, or not listed).
  - Saving puts them in the care team and persists it. This replaces the screen-state favourite.
  - Log visits per clinician (date, reason, notes, next appointment date).
- **Symptoms:** keep the existing log.
- **Sleep (new, manual):** bedtime, wake time and quality 1–5, giving a duration trend.
- **Activity and workouts:** keep the activity presets and the set logger.
- **Food diary:**
  - Keep manual entry and barcode digits.
  - **Fix search** to `cgi/search.pl?search_terms=…&search_simple=1&json=1`, with a `User-Agent` and a 10-second timeout. A test with a recorded response proves that "oatmeal" results contain "oat".
  - Daily totals.
- **Proof:** a widget test per record type that adds an entry, restarts the store, finds the entry, edits it and deletes it.

**M4. Signature: the "Since last visit" brief.**
- **Window:** from the last logged visit with the chosen clinician (or a date the user picks if there is none) to today.
- **Sections**, each with an include toggle; the choices persist per clinician:
  1. **Header:** "Prepared by {name} on {date}". Name and date of birth are optional, set in Settings → "Name on briefs", and asked for only when the first brief is made.
  2. **Medicines:** current list with ingredient (RxNorm), dose and schedule. "Changes since {date}" lists started, stopped and dose changes with dates, taken from change events. Adherence is doses logged ÷ doses scheduled, shown only when a schedule exists.
  3. **Readings:** per type with at least 1 reading in the window: count, first, last, min, max and average, with a small sparkline in the PDF.
  4. **Labs:** each result in the window with the report's range, the H/L flag and the previous value of the same test.
  5. **Symptoms:** the logged entries, most recent 15 shown, then "and N more".
  6. **Sleep and activity:** average sleep duration, workout sessions and total minutes.
  7. **FDA recall reports:** for each current medicine with an ingredient, query openFDA `drug/enforcement` for that ingredient with `report_date` in the window (minimum 12 months).
     - Show report date, classification, status and a shortened product description, followed by the line "Recalls apply to specific products and lots. Check the label or ask your pharmacist."
     - HTTP 404 `NOT_FOUND` → "No FDA recall reports for {ingredients} between {d1} and {d2} (openFDA, checked {time})".
     - Offline or HTTP error → "Recall check not run: {reason}". Never a blank section and never a stored copy.
  8. **My questions:** persisted per clinician. Each can be checked off after the visit.
- **Outputs:** an on-screen preview; **Share PDF** (the `pdf` package, Spline Sans fonts embedded, A4 or Letter from the device locale) through the share sheet; and **Copy as text**.
- **"Log this visit"** records today's visit, which starts the next window, and archives the answered questions.
- **Pure logic:** the brief builder is a pure Dart function `buildBrief(record, clinician, window, clock)` with an injectable clock and recall client, so it is unit-testable without Flutter.

**M5. Depth: timeline, search, export, and real empty, error and offline states.**
- **Timeline tab:** every record entry newest-first.
  - Filter chips: Medicines, Readings, Labs, Symptoms, Sleep, Activity, Food, Visits.
  - Date-range filter.
  - A search box over medicine names, test names, notes and clinician names, with a no-match state: "Nothing in your record matches 'xyz'".
- **Export:** keep the full JSON export in Settings, and add **Import from a MyHealth export**, which restores into an empty record and refuses files with a different `app` or a newer `schema`. CSV per record type is a SHOULD (S3).
- **Empty states written for this app.** A fresh install shows "Add your first medicine" and "Add a clinician to make a brief". Do not show dashes in empty tiles.
- **Network states:** each network lookup (RxNorm, NPPES, LOINC, MedlinePlus, Open Food Facts, openFDA) has a timeout, a "You're offline. You can still type it in." path, and an error message naming the service. **No silent fallback to bundled data**: the MyHealthfinder fallback pattern must not come back.
- **Offline:** the whole record and the brief, minus the recall section, work offline.

**M6. Own identity, distinct from BodyQuest (terracotta `#B8432F` on paper, Nunito/Fredoka), HerJourney (dusk indigo `#3B3561`, Source Serif 4/Karla), every other real-apps spec so far, and the portfolio's blue/teal/neon look.**
- **Concept: a well-kept clinic chart.** Clean chart-white pages, hairline rules, and numbers set like a printed lab report.
- **Colour:**
  - seed/primary mulberry `#8A2E7E`
  - secondary cerulean ink `#0A5F8A` (links, the selected tab on Android)
  - surface chart-white `#F6F4F1`, cards `#FFFFFF`, text ink `#1F1B24`
  - out-of-range flag: a bold "H" or "L" letter in `#9A5B00`, never colour alone
  - dark variant: background `#17131A`, primary lifted to `#C98BBE`
  - Delete the Tailwind and system-colour tables in `theme/app_theme.dart`.
  - Uniqueness: `grep -rlis -e 8A2E7E -e 0A5F8A -e F6F4F1 -e 1F1B24` over the 42 `*/lib` and `*/mobile/lib` folders under `~/agl` and the 24 specs written so far found **no match** (run today).
- **Typography:**
  - Bundle **Spline Sans** (`SplineSans[wght].ttf`) for UI and body.
  - Bundle **Spline Sans Mono** (`SplineSansMono[wght].ttf`) for **every reading, dose, lab value and date in the record and the brief**.
  - Both are OFL. The GitHub API today lists `ofl/splinesans` and `ofl/splinesansmono` in google/fonts with `OFL.txt`, and the raw TTFs answered HTTP 200 (146,896 B and 118,744 B).
  - Declare both under `fonts:` with their licences. No runtime font fetch.
  - These are variable fonts, so **check in a screenshot that bold actually renders bold**. If it does not, cut static instances with fontTools `varLib.instancer`.
  - A grep for "spline" across the same app folders, every `pubspec.yaml` and the specs found **no match**. Public Sans, Newsreader and Atkinson Hyperlegible are already claimed by MyFinance, daily-pulse, and AGrammarly/Kinnav.
- **Shape language:**
  - corners 6 (not the portfolio's 12)
  - 1 px rules between rows, like a lab report
  - ranges drawn as a thin horizontal band with the value marked
  - **no gradients, no glass, no glow**
- **Home ("Chart", the first tab):**
  1. The next-appointment card: "Dr {name} · {date}" with **"Brief: 4 changes since {last visit}"** and a Prepare button. If no visit is logged it reads "Add a clinician to make a brief".
  2. "Due now" medicine doses with Take buttons.
  3. The latest reading of each type in mono, with a 30-day sparkline.
  4. One "+ Add to record" button that opens a sheet of entry types.
- **Shell:** 3 tabs: **Chart**, **Timeline**, **Care team** (clinicians, visits, briefs, questions). Settings is a gear in the Chart header.
  - iOS: `CupertinoTabBar` with CupertinoIcons, Cupertino page transitions and Cupertino date/time pickers.
  - Android: Material `NavigationBar`.
  - The 4-tab `BottomNavigationBar` goes.
- **Ads (pending F2):** no banner above the tab bar, and **no interstitial** (remove `AglAds.onTransition()`). If ads stay, there is one inline banner at the end of the Timeline list only, never on the brief, entry forms or Care team. AdMob consent ("Privacy choices") stays in Settings.
- **Onboarding: 3 screens, MyHealth's own.**
  1. "Your health record, on this phone. Nothing is uploaded." This screen includes the not-medical-advice line, the Terms/Privacy links and the opt-in analytics and crash toggles, replacing the separate consent page.
  2. "Add a medicine you take", or skip.
  3. "Add a clinician" (NPPES search), or skip.
  No name, birth date, birth time, city, goals, conditions or fake permission rows.
- **Icon:** not a glyph on a gradient, and not a heart or ECG.
  - A chart-white rounded square holding a folded clinic-chart page in mulberry with three mono-style rule lines, one of them ending in a small cerulean tick.
  - Produce a 1024 px PNG with no alpha for iOS, plus the Android adaptive foreground and background, then regenerate.
  - The current `assets/logo/myhealth_icon*` files are replaced.
- **Splash:** replace the shared storyboard with chart-white `#F6F4F1` and the chart mark.
  - Change only `ios/Runner/Base.lproj/LaunchScreen.storyboard` and the `LaunchImage.imageset` assets. No pbxproj edit.
  - **Proof:** `shasum` of the storyboard is no longer `3f6a9b27d8…`.
- **Home-screen name:** `CFBundleDisplayName` and the Android `android:label` become the approved name. If F3 is unanswered, use **`MyHealth`** with correct casing, not `Myhealth`. Keep the name in one Dart constant so a rename touches one place.

**M7. Honest and 5.6-safe.**
- **Remove these strings from code and rendering:**
  - every "in this version", "aren't available yet", "Not connected", "coming soon", "Form video coming soon" (drop the video box)
  - "AI-powered", "clinical integration", "Care+"
  - "HONEST SAMPLE" seed content
  - the **false encryption badge** (`profile_strings.dart:88`)
  - **the in-app draft privacy text**: `legal_strings.dart:18`, `:36` and the 9 sections
  - The in-app "Privacy policy" and "Terms" links open the hosted policy `https://www.americangroup.ai/policy/myhealth/` (the `privacy_url` in the store record).
  - **Do not write new legal text.** That is Charter §6, founder question F4.
- **Replacement data-safety line:** "Your record is stored only on this phone, inside MyHealth's app storage, and is never uploaded. Lookups (medicine names, ZIP code, test names, food barcodes) are sent to the public services named on screen. Use your phone's passcode to protect it." Optional Face ID/Touch ID lock is S2.
- **No switches:** no demo login, no A/B or remote switches (`ExperimentProvider` is gone; grep `AglInsights` to show Remote Config gates nothing), no reviewer, region or date detection, and no hidden gestures.
- **No invented content:** no invented prices, vendors, ratings, users or "normal range" verdicts. Every number on screen comes from the user's entries or a named live source.
- **Disclaimer:** "MyHealth is a record-keeping tool, not medical advice. Don't change a medicine because of anything in this app" stays visible in onboarding, Settings, and the footer of every brief.

**M8. Proven.**
- `/Users/spatchava/agl/.flutter-sdk/bin/flutter analyze` returns **0 issues**.
- `flutter test` passes in full.
- **New tests:**
  - **brief builder:** window from the last visit; a medicine started, stopped and dose-changed inside versus outside the window; adherence only with a schedule; reading stats; the lab H/L flag uses only the report's range; symptom truncation; recall states (results, 404 → none, timeout → "not run") using a fake client
  - **migration:** old `@myhealth/medicines` and `vitals/bp` keys survive the upgrade
  - **record CRUD** for every type
  - **reminder** scheduling and cancel, with the plugin mocked
  - **NPPES:** the specialty picker sends a wildcard; NPI parse
  - **Open Food Facts:** search uses `cgi/search.pl`
  - **import/export** round trip; import refuses a foreign file
  - **onboarding:** fresh install → 3 screens → Chart with no sign-in
  - **absence:** no "Sign in with Apple", "Continue as guest", "in this version", "coming soon", "Not connected", "Bay Area", "Checkout", "Cycle" or "AI-powered" in rendered screens or in `lib/`
- **Look at it:** build for the iOS simulator, launch it, and screenshot Chart (with real entries the developer made), the brief preview, the PDF (opened), Timeline and Care team. Do not ship without looking at it.
- **Commit:** path-limited (never `git add -A`). Never touch `fastlane/` or `ios/Runner.xcodeproj/project.pbxproj`. Push to `master`.

### SHOULD

- **S1. Appointment reminder:** a local notification the evening before a logged next appointment: "Your brief for Dr {name} is ready".
- **S2. Optional app lock** with Face ID/Touch ID or the device passcode (`local_auth`; needs `NSFaceIDUsageDescription` in `Info.plist`, which is clean at base).
- **S3. CSV export** per record type (readings, labs, medicines with change events) through the share sheet.
- **S4. Apple Health / Health Connect import** of weight, blood pressure, glucose, heart rate, steps and sleep. **Only after F5:** HealthKit needs the capability on the App ID and in the provisioning profile (an account action, Charter §4) and an entitlements change. Until then, no copy anywhere mentions Apple Health.
- **S5. Medicine label link:** RxNorm ingredient → MedlinePlus Connect drug information (keyless) on the medicine page, alongside the OpenFDA label.
- **S6.** Replace `services/error_reporter.dart` (an exact duplicate in 13 apps) and `services/monitoring.dart` with direct `AglCrash` calls, if simple.

## 5. Data source

- **On-device:** every record entry, care team, visits, questions and briefs. Nothing is uploaded. After M2, MyHealth no longer talks to Supabase `smvvjivvlprjhzhoizym` at all, and no tables are needed.
- **Keyless public APIs, each curl-verified on 2026-10-12:**
  - NPPES `npiregistry.cms.hhs.gov/api/` (200)
  - RxNorm `rxnav.nlm.nih.gov/REST/approximateTerm.json` and `/rxcui/{id}/related.json` (200)
  - openFDA `api.fda.gov/drug/enforcement.json` (200, and 404 `NOT_FOUND` for none) and `/drug/label.json` (200)
  - MedlinePlus Connect `connect.medlineplus.gov/service` (200)
  - NLM Clinical Tables LOINC `clinicaltables.nlm.nih.gov/api/loinc_items/v3/search` (200)
  - Open Food Facts `world.openfoodfacts.org/cgi/search.pl` (200) and `/api/v2/product/{code}.json` (200)
  - Add `.nih.gov`, `.fda.gov`, `.hhs.gov` and `.medlineplus.gov` to `scripts/verify_api_hosts.py` coverage. Today only `.openfoodfacts.org` of these is listed (`verify_api_hosts.py:52`).
- **Removed sources:** MyHealthfinder v3 (HTTP 410), Open-Meteo (it served only the hike screen), Supabase auth.
- **Nothing invented:** no sample entries, ranges, prices, vendors or users. A fresh install shows an empty record.

## 6. Store impact (proposed; store-compliance applies it, and this spec does not edit store files)

**Listing (`store/apps/MyHealth.json`):**
- **Name** (30 max): depends on F3. Default `MyHealth: Visit-Ready Record` (28). Alternative if the founder drops "My": `Chartkeeper: Since Last Visit` (29). An iTunes search for "Chartkeeper" today returned no app with that name, but I have **not** verified App Store Connect name availability (a 409 risk).
- **Subtitle** (30 max): `Meds, labs, readings, doctors` (29). It replaces "Activity, diet, sleep, vitals".
- **Primary category:** MEDICAL (currently HEALTH_AND_FITNESS). Secondary: HEALTH_AND_FITNESS. It is a record and visit-prep tool, not a fitness tracker. On Play, use Medical.
- **Description:** open with the job, not the app name. No "——" headings, no list of things it can't do, no hikes. Draft:
  > Before your next appointment, MyHealth writes a one-page brief of what changed since you last saw that doctor: medicines you started, stopped or changed, your blood pressure, glucose and weight readings, new lab results against the range on your report, the symptoms you noted, and your questions. Share it as a PDF or print it.
  >
  > Keep your record as you go: medicines with reminders and a full history, readings with trends, lab results, symptoms, sleep, workouts and a food diary. Find and save your clinicians from the official U.S. provider registry (NPPES), and log each visit.
  >
  > The brief also checks public FDA recall reports for the ingredients you take, and tells you when there are none.
  >
  > No account. Your record stays on this phone and is never uploaded. Medicine names, test names, ZIP codes and barcodes you look up are sent to the public services named in the app (NLM RxNorm and MedlinePlus, openFDA, CMS NPPES, Open Food Facts).
  >
  > MyHealth is a record-keeping tool, not medical advice. Don't change a medicine because of anything in this app.
  - Keep one plain sentence about AdMob only if F2 keeps ads.
- **Keywords:** `health record,medication list,pill reminder,blood pressure log,lab results,doctor visit,appointment,PHR,symptoms,recall,glucose,caregiver`. Drop "fitness, workout, hiking".
- **Promotional text:** "Walk into every appointment knowing what changed: medicines, readings, labs and symptoms since your last visit, on one page."
- **Release notes:** say honestly that this is a rebuild. Removed: sign-in, hikes, food ordering, cycle tracker. Added: brief, labs, care team, reminders, timeline.

**Screenshots: retake all of them** (iPhone 6.9" ×5, iPad 13" ×5, Play phone and tablet). Use the real app after the developer has entered a few weeks of genuine test entries on a test device. No invented names: the clinician must be a real NPPES result, and test data should be clearly the tester's own.
1. Chart home with next appointment and "Brief: 4 changes since…"
2. The brief preview (medicine changes and readings)
3. The PDF in the share sheet
4. Lab result history with report range and H/L
5. Timeline with filters, or Care team

No sign-in screen, no hikes, no consent page as the first shot. `fastlane/screenshots/` and `fastlane/metadata/` have someone else's uncommitted changes at base, so store-compliance must coordinate before overwriting. **Feature graphic:** a new one in the chart style.

**Review notes:**
- Drop the "2. DEVICES…" skeleton and the simulator boilerplate. State physical-device testing **only if it was actually done**, naming the device.
- Say plainly:
  - no account and no demo login (set `demo_account_required: false`, remove `qa@americangroup.ai`)
  - what to try: add a medicine (type "lisinopril"), add a blood-pressure reading, search a clinician by ZIP (e.g. 10001, Family Medicine), log a visit dated last month, change the dose, then open Care team → Prepare brief → Share PDF
  - the audience as written in §2
- Remove the Supabase, Google Sign-In, Sign in with Apple, MyHealthfinder and Open-Meteo services, and the "Account deletion" paragraph. List the APIs in §5. Notifications are local only.

**Privacy label** (replaces the label shared with yourtube):
- Drop EMAIL_ADDRESS, NAME and USER_ID (no account after M2).
- **Health and fitness data is not "collected"**, because it never leaves the device. Apple's definition (fetched today with curl from developer.apple.com/app-store/app-privacy-details/): *"'Collect' refers to transmitting data off the device in a way that allows you and/or your third-party partners to access it for a period longer than what is necessary to service the transmitted request in real time"* and *"Data that is processed only on device is not 'collected' and does not need to be disclosed."*
- Lookups send medicine names, test names, ZIP code and barcodes to public government and Open Food Facts APIs in real time. **Whether those count as collection is for store-compliance to decide.** I cannot verify how those services retain request logs.
- Crash, Performance and Product Interaction data stay as they are (opt-in Firebase, not linked).
- DEVICE_ID and ADVERTISING_DATA stay only if F2 keeps ads.
- Review notes and the description must say the record is not uploaded, matching the label.

**Differentiation answers** in the JSON (§2, §3): use §2 and §3 of this spec, with the competitor table labelled as based on store descriptions.

## 7. Out of scope

- Cycle, fertility, pregnancy, menopause (HerJourney). Anatomy or health games (BodyQuest). Grocery lists, restaurant or food ordering (GroceryMatch). Insurance or ID card storage (MyCard).
- Training plans, GPS runs, hikes, Watch apps, SharePlay, social features, badges.
- Patient-portal / FHIR connections, OCR of lab reports, AI summaries, drug-interaction checks (the RxNav API is gone), cloud sync, multi-user family profiles.
- Writing privacy or terms text (Charter §6). Editing `store/apps/*.json`, fastlane metadata or `docs/`. Replying to or resubmitting to Apple (Charter §1, 5.6 freeze MA-043).
- Translating the new screens into the other 11 locales. English first. The shared `agl_i18n` labels still apply, and the review notes must keep saying translation is partial.

## 8. Founder questions

- **F1. Remove accounts?** Supabase is used only for sign-in, sign-up and `delete_user`, and no record data is server-side. Default if unanswered: remove (M2). I did not check how many MyHealth users exist in Supabase auth. That needs a production read, which is a Charter §2 decision.
- **F2. Keep ads in a medical-record app?** Recommended: remove ads from MyHealth, or keep one inline banner at the end of Timeline and no interstitial. Removing ads affects revenue (Charter §3). Default if unanswered: inline Timeline banner only, interstitial removed.
- **F3. App name.** Keep "MyHealth" (fixing the casing) or rename, e.g. "Chartkeeper". "My" is one of the portfolio's mechanical prefixes. Name availability in App Store Connect is not verified.
- **F4. Privacy policy text.** The hosted policy at `americangroup.ai/policy/myhealth/` must describe the new model: no account, local-only record, the listed public lookups and local notifications. Legal text is Charter §6. The in-app draft placeholder is removed by M7 either way.
- **F5. Enable HealthKit / Health Connect?** It needs the HealthKit capability on the App ID and in provisioning profiles (Charter §4). That unlocks S4. Without it, MyHealth stays manual-entry, and no copy mentions Apple Health.
- **F6. Category change to MEDICAL** (from HEALTH_AND_FITNESS). Recommended. Store-compliance applies it if approved.
