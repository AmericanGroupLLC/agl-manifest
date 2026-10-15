# Spec: iMeasure becomes a slope-and-fall level for people fitting things

- Author: product-manager (AI office), 2026-10-12
- Repo: `/Users/spatchava/agl/iMeasure`, branch `main`, base_sha `b9f7ece5e06d51f84f3c37891f605cf23425ee00`. Both come from `git rev-parse HEAD` and `git branch --show-current`, run today.
- Apple: rejected under **4.3 / 4.2.6** on 2026-10-05T21:26Z. Earlier, on the same thread, **2.1(a) crashed on launch** (iPhone 17 Pro Max, iOS 27.0) and **2.3.6** (age rating must say "Advertising: Yes") were raised. Source: `/Users/spatchava/agl/.dist/rejections.json` key `iMeasure`, 4 messages. Google Play: LIVE_PRODUCTION.
- Plan: `projects/real-apps/plan.md` (seven acceptance criteria). Overlap: `projects/real-apps/overlap.md:36` (G4, converter = CalcMaster) and `:37` (G5, pedometer next to MyHealth).
- Baseline, measured today at HEAD: `flutter analyze` gave "No issues found! (ran in 41.1s)". `flutter test` gave "+392: All tests passed!".

**Other people have uncommitted work in this repo. Leave it alone.** `git status --short` shows 26 entries: 25 under `fastlane/` (descriptions, notes.txt, every screenshot) and `ios/Runner.xcodeproj/project.pbxproj`. **None of the files this spec asks the developer to change has uncommitted edits right now.** Those files are `lib/**`, `test/**`, `integration_test/**`, `pubspec.yaml`, `assets/**`, `ios/Runner/Info.plist`, `ios/Runner/Base.lproj/LaunchScreen.storyboard`, `ios/Runner/Assets.xcassets/**` and `android/app/src/main/res/**`. Do **not** touch `project.pbxproj`. Bundled fonts go through `pubspec.yaml`, and new images go into existing asset catalogs, so neither needs a pbxproj edit. Fastlane and store JSON belong to store-compliance (section 5).

---

## 1. Problem

### What the app is today (I read all of `lib/`: 41 files, 16,714 lines, 4,108 of them in the string table `lib/services/i18n.dart`)

| Area | State | Evidence |
|---|---|---|
| Shell | 5 custom tabs: Home, Measure, Level, Compass, Records. Settings is pushed from a gear icon. `BannerAdSlot` sits in the shell Column directly above the tab bar. That is the portfolio's "banner above the bottom bar" pattern, done without `AglAdBanner`. | `lib/screens/home_shell.dart:59-134` |
| Home | A dashboard: a stat strip ("Ready/Offline", "11 tools", saved count, units), 3 recent readings, then a grid of **11 instrument tiles**. This is the generic tile-grid scaffold. | `lib/screens/home_screen.dart:51-125, 157-253` |
| Measure | Two modes. **Screen**: tap two points on a grid, and the length comes from screen DPI. This does the same job as Screen Ruler. **Camera**: freeze a frame, mark a bank card / A4 / Letter reference, then mark the object, and the length is scaled from the reference (`referenceScaledCm`). The camera mode is real and the most original thing in the app, **but the photo is thrown away**: only the number is saved. | `lib/screens/measure_screen.dart:22-51, 200-219` |
| Tolerance copy | Measure shows "±1–5 cm" uncalibrated and "±0.2–1 cm" calibrated. **No test or document in the repo measures these figures.** | `measure_screen.dart:225-241` |
| Level | Real. It has bubble and bullseye modes, a low-pass filtered accelerometer, Set Zero, haptics on level, and Save. It shows **degrees only**: no grade %, no rise-per-run, no pitch, no target. | `lib/screens/level_screen.dart:16-24, 150-174` |
| Compass | Real. Tilt-compensated heading, true north from the World Magnetic Model (`geomag`) once location is allowed, field-strength check, and Save. | `lib/screens/compass_screen.dart:19-31, 176-231, 285` |
| Protractor | **It integrates the gyroscope z-rate to get an angle**, so the reading drifts with time and has no absolute reference. It cannot be saved. | `lib/screens/tools/protractor_screen.dart:10, 57` |
| Barometer | Real. Pressure, pressure altitude and a 10-minute trend, with an honest "no sensor" state and no weather word. It cannot be saved. | `lib/screens/tools/barometer_screen.dart:11-39` |
| Noise meter | Real, and labelled "uncalibrated". It cannot be saved. | `lib/screens/tools/noise_meter_screen.dart:64-69, 387` |
| Screen ruler | Real. A painted ruler with DPI calibration in Settings. It cannot be saved. | `lib/screens/tools/ruler_screen.dart:7-16` |
| **Unit converter** | Six categories. **This is CalcMaster's job (overlap G4).** It is also the store's keyword "converter". | `lib/models/converter_data.dart:26-84`, `lib/screens/tools/converter_screen.dart` |
| **Pedometer** | Accelerometer peak detection, a 7-day chart, **calories and a "health tip"**. **This is MyHealth's job (G5).** | `lib/screens/tools/pedometer_screen.dart:12-17` |
| **Quick Answers** | A chat-style screen (`AiCoachScreen`) over a keyword table, plus a typed-conversion parser that reuses `converter_data`. It is a generic Q&A surface ("AI coach" in the code, "Quick answers" in the UI). | `lib/screens/tools/ai_coach_screen.dart`, `lib/services/quick_answers.dart:1-40` |
| Records | Real. Saved in SharedPreferences JSON, with jobs, free-text search, a job filter, rename and delete. **Export is a CSV copied to the clipboard only**: no file and no share sheet. Only Measure, Level and Compass can save. | `lib/services/records_service.dart:66-336`, `lib/screens/records_screen.dart:32-44` |
| Sign-in | The `LoginScreen` (email/password, Sign in with Apple, Continue with Google, Continue as guest) is reachable from Settings › Account & data **in every build**. That holds even though `AppInfo.accountsEnabled = false` says sign-in is hidden: nothing reads that flag. **Signing in unlocks nothing.** Records never leave the device. Account deletion calls `rpc('delete_user')`, which my memory notes record as not applied in production (MA-044, **not re-verified today**). | `lib/screens/settings_screen.dart:170-196`; `lib/app_info.dart:29`; `lib/services/auth_service.dart:325-326`; `grep -rn accountsEnabled lib` hits only the two declarations |
| Pro / IAP | `PremiumScreen`, `PurchaseService` and the record cap all sit behind the compile-time `kProEnabled = bool.fromEnvironment('IAP_ENABLED')`. It is off, and no products exist. The code is dead weight. | `lib/services/pro_config.dart:1-11`; `settings_screen.dart:213-243` |
| Dead file | `lib/services/app_info.dart` is not imported anywhere. `lib/app_info.dart` replaced it. | `grep -rn "app_info.dart'" lib test` |
| Identity | **The palette is Apple's own Measure look**: black `#000000` background with systemYellow `#FFD60A` as the only accent (`lib/theme/app_theme.dart:82-110`). `AppColors` maps cyan/green/purple/pink all to that yellow (`:173-198`). System font only, with `Typography.material2021(platform: iOS)` (`:241`). The splash shows an "iM" monogram, "iMeasure" and "Precision in your pocket" (`splash_screen.dart:97-123`; `i18n.dart:525`). The icon is a neon cyan-to-green ruler with "iM" on near-black (`ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png`, opened). The launch storyboard is the shared one: shasum `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, measured today. |
| Onboarding | 3 pages ("Measure anything", "Level and true north", "Keep every reading"), then **"Get Started"**. | `onboarding_screen.dart:58-113`; `i18n.dart:253-261, 571` |
| Info.plist strings | The camera string says "**AR mode**", and the app has no AR. The motion string names the **Pedometer**. | `ios/Runner/Info.plist:12, 16` |

### What Apple saw, and why it reads as 4.3 / 4.2.6
1. **4.3(b), a copy of a built-in app.** The name is "i" + "Measure", the job is Apple's Measure app (measure + level), and the colours are Apple Measure's black and yellow. A reviewer opening it on an iPhone sees a weaker clone of something already on the phone.
2. **A grab-bag, not a product.** Home advertises "11 tools", including a unit converter (CalcMaster's job), a pedometer with calories (MyHealth's job) and a chat-style Q&A. That is the "toolbox" template, and it duplicates our own account (4.3(a)).
3. **The review notes contradict the binary** (`store/apps/iMeasure.json` `review_information.notes`): "The app opens on a sign-in screen. Test credentials are in the demo account fields" (it opens on onboarding / Home as a guest), "Supabase — account and data storage" (nothing is stored), "Apple In-App Purchase — paid features" (none exist), and `demo_account_required: true` with the shared `qa@americangroup.ai`. "Intended audience" is just the subtitle pasted in.
4. **Shared tells**: the launch storyboard, the "Get Started" button, the Supabase sign-in wall, and "——" headings in the description.

The 2.1(a) launch crash is **not diagnosed in this spec**. I did not open the crash log, and I cannot say whether HEAD still crashes on iOS 27. Physical-device launch is acceptance item M8.

## 2. User

**Someone fitting things in a home: a DIY renovator, a handyperson, a tiler, or a renter putting up shelves.** They need to know two things: *is this surface level, or at the slope it should be*, and *how much do I raise which end to fix it*. Typical jobs: a shelf or worktop, a drain or gutter run that has to fall, a patio or shower floor that has to drain, a ramp, a deck, a fence rail, a picture rail. They have a phone in their pocket, and they may or may not own a spirit level. They often don't own a digital inclinometer. They want the number in the units their job uses (mm per metre, inches per foot, %, x/12 pitch, 1:N), not only degrees. They want to keep the readings for the job.

They are **not** looking for a unit converter, a step counter or an AR tape measure.

## 3. Product decision

**Core job (one, done well):** put the phone on a surface, or on a straightedge laid across it, and get the slope **in the unit the job uses**, measured against **the slope the job needs**, with **how much to raise which end** over the user's span. Then file the reading under the job.

**Signature feature: "Fall & Shim".** The level reads the slope as all of the following at once:
- degrees,
- grade %,
- rise per run: mm/m or in/ft, following the unit preference,
- ratio 1:N,
- roof pitch x/12.

On top of that, two things built on the readout:
- **Target with tolerance.** The user picks a target slope (level, a preset ratio, or anything typed as `2%`, `1:48`, `1/4 in/ft`, `6/12`, `1.5°`) and a tolerance. The screen shows *in / too steep / too shallow* by how much, with colour and one haptic pulse when the reading enters tolerance.
- **Span shim.** The user enters the length of the thing being levelled, for example a 1200 mm worktop or a 48 in board. The app shows **"Raise the left end 10.5 mm"**, or for a target, "Lower the right end 3 mm to reach 2%". The value is `span × (tan θ_target − tan θ_measured)`.

Everything is on-device. The accelerometer is already wired, and Set Zero is already implemented. There are no keys, no network and no data anyone could fake.

**Competitors.** competitor not verified. The web search and web fetch tools are blocked in this session ("Internet mode is not enabled"), so I could not check any listing. From my own knowledge, **unverified**: Apple's built-in Measure app shows its level in degrees, with no grade, pitch, target or shim output, and dedicated clinometer apps exist that show % and degrees. **The signature feature therefore must not be described in store copy as something "no other app does".** Describe what it does. Before any comparative claim is used, store-compliance or the founder must verify competitor listings.

**What iMeasure keeps from its toolbox, and why:** the instruments a fitter uses on the same job. These are Level (with Fall & Shim), Photo measure (camera + card/A4/Letter reference), Screen ruler, Angle, Compass (true north), Barometer and Sound level. They all save into the same Jobs.

**What it drops:** the unit converter (CalcMaster), the pedometer (MyHealth), Quick Answers / the "AI coach" chat, sign-in, and the unused Pro/IAP layer.

---

## 4. Acceptance criteria

### MUST: required for Apple to see a real, distinct app

**M1. Drop what belongs to other apps (plan criteria 1 and 4).**
- Delete `lib/screens/tools/converter_screen.dart`, `lib/models/converter_data.dart`, `lib/screens/tools/pedometer_screen.dart`, `lib/screens/tools/ai_coach_screen.dart`, `lib/services/quick_answers.dart` and the dead `lib/services/app_info.dart`. Remove their tiles, onboarding mentions, `AppGlyph` entries if unused, and strings (`toolConverter`, `descConverter`, `toolPedometer`, `descPedometer`, `toolQuickAnswers`, `descQuickAnswers`, and so on) in all 16 locales.
- Fold the measurement tips worth keeping from `quick_answers.dart` (true vs magnetic north, card reference accuracy, hanging a frame) into a static "How to get a good reading" info sheet on the instrument they belong to. This is plain text with no input field and no chat.
- `RecordTool.converter` and `RecordTool.pedometer` **stay in the enum** so existing saved records still decode, display and export (the enum is persisted by name, `measurement_record.dart:5-6`). No new record can be created with them.
- Tests: `test/quick_answers_test.dart` goes with its feature, and the converter/pedometer/Quick Answers cases in `test/ui_test.dart`, `test/widget_test.dart` and `test/foldable_layout_test.dart` are removed **only where they test the deleted screens**. The commit message lists each removed test and the feature it covered. That is a feature removal, not "deleting tests to go green", and QA should check it against this list.
- Done when: `grep -rn "ConverterScreen\|PedometerScreen\|AiCoachScreen\|QuickAnswers\|converter_data" lib test integration_test` returns nothing, and a test loads a stored JSON record with `"tool":"converter"` and one with `"tool":"pedometer"` and shows both in Jobs and in the CSV.

**M2. Remove the sign-in and Pro scaffolding (criteria 4 and 5; 5.6).**
- Delete `lib/screens/login_screen.dart`, `lib/services/auth_service.dart`, `lib/services/supabase_config.dart`, `lib/screens/premium_screen.dart`, `lib/services/purchase_service.dart` and `lib/services/pro_config.dart`. Remove the Supabase init and the `AppEnv` Supabase validation in `lib/main.dart:33-38, 58-75, 86`, and the Account rows and Pro section in Settings. Remove `RecordsService.enforceFreeLimit` and the `freeLimit*` toasts.
- Remove from `pubspec.yaml`: `supabase_flutter`, `google_sign_in`, `sign_in_with_apple`, `crypto` (used only by `auth_service.dart`, per grep) and `in_app_purchase`. Run `flutter pub get` and commit `pubspec.lock`.
- `test/account_deletion_test.dart` goes with the feature, listed in the commit message as in M1.
- **No account means no demo login and no in-app account deletion requirement.** A user who created an account on Play through Google/Apple sign-in in the past still has the deletion route on the support site. That is a founder point (Q3).
- Done when: `grep -rni "supabase\|sign in with apple\|continue with google\|continue as guest\|IAP_ENABLED\|kProEnabled" lib test` returns nothing, and Settings has no account row.

**M3. Signature feature: Fall & Shim on the Level tab (criterion 2).**
- A pure, unit-tested module (for example `lib/services/slope_math.dart`) holds:
  - `SlopeReading.fromDegrees(θ)`, which gives `grade% = 100·tanθ`, `mmPerM = 1000·tanθ`, `inPerFt = 12·tanθ`, `pitchPer12 = 12·tanθ` and `ratioN = 1/tanθ` (∞ / "level" when |θ| is below display resolution);
  - `parseSlopeTarget(String)`, which accepts `2%`, `2 %`, `1:48`, `1/4 in/ft`, `0.25"/ft`, `20 mm/m`, `6/12`, `6:12 pitch` and `1.5°`, returns degrees, and returns null (shown as an inline error) for anything else;
  - `shim(spanLength, θmeasured, θtarget)`, which gives the signed height difference across the span and which end to raise.
- Required test values, computed today with Python `math.atan`:
  - 1:12 → 4.7636°, 8.333 %;
  - 1/4 in/ft → 1.1935°, 2.083 %;
  - 6/12 → 26.5651°;
  - span 1200 mm at 0.5° against target 0 → 10.47 mm.
  Assert to ±0.01.
- Level UI:
  - The live readout shows degrees plus the user's chosen secondary unit large, and the other units smaller. The user can cycle the primary unit by tapping it, and the choice persists.
  - Target chip: Level (default), presets shown as plain ratios (1/8 in/ft · 1/4 in/ft · 1:12 · 4/12 · 6/12 · 8/12, with metric equivalents mm/m when metric), and Custom. The tolerance stepper persists per target; the default tolerance is a design choice, not a standard.
  - In-tolerance / too steep / too shallow, shown as colour **plus** a text label (never colour alone) and one haptic pulse on entering tolerance (respecting the existing haptics setting).
  - Span field (persisted) and the shim line: "Raise left end 10.5 mm". The left/right end follows the phone's orientation on the edge.
  - **Hold** freezes the reading. **Save** stores degrees in `value`/`unit: deg`, and adds `target`, `tolerance`, `span` and `shim` fields to the record JSON (nullable, backward compatible).
- Preset labels **must not cite a building code or standard** unless the developer has checked the primary text and puts the citation in a code comment. Otherwise each preset shows only its ratio, and a single line on the target sheet says: "Required slopes vary by local code. Check yours." This avoids presenting unverified data.
- Done when: the unit tests above pass, and a widget test drives the Level screen with an injected accelerometer stream (constructor-injected `Stream<AccelerometerEvent>` used only by tests; release always uses `sensors_plus`). It sets target 2 % and span 1000 mm, feeds 1.0° and expects "too shallow" and a shim of about 2.5 mm (1000·(0.02 − tan 1°) = 2.55 mm). It then feeds 1.15° and expects "in tolerance" with tolerance ±0.1 %.

**M4. Every kept instrument is real and can be filed (criteria 1 and 3).**
- **Angle** replaces the gyroscope Protractor. It is gravity-based, so it is absolute and does not drift. One mode gives the edge angle against horizontal/vertical. "Two surfaces" mode captures surface A, then surface B, and shows the angle between them (for example a mitre or a chair-leg splay). Remove the gyroscope integration.
- **Save to job** on Angle, Barometer (pressure + altitude at the moment of save), Sound level (current, and session max/average), and Screen ruler, joining the Measure, Level and Compass that already save.
- **Measure** keeps two modes, renamed to describe what they are: **Photo** (the camera reference method, default) and **On screen** (object held against the screen; this merges the old grid mode with the Screen ruler, so there are not two tools doing one job).
- Done when: a widget test per instrument opens its save sheet and finds the new record in Jobs with the right `tool` and `unit`.

**M5. Jobs: persistence, search, export, honest states (criterion 3).**
- The Records tab becomes **Jobs**. The list of jobs shows the reading count and last activity. Job detail lists the readings newest first, with the existing free-text search and a tool filter. A "No job" bucket holds unfiled readings.
- **Photo measure saves its evidence.** On Save, the frozen frame with the reference and target lines drawn on it is written as a JPEG to the app documents directory (`path_provider`). The record keeps the relative path, and the job shows a thumbnail that opens full screen. Deleting the record deletes the file, and so does deleting all records.
- **Export a job** as a `.csv` file through the system share sheet (`share_plus`), with columns `job,label,tool,display,value,unit,target,tolerance,span,shim,created_at` (extending `records_service.dart:300-320`). Photo records can share their JPEG from the record view. Keep "Copy CSV" as a secondary action.
- States:
  - empty Jobs: "No jobs yet. Save a reading from any instrument and give it a job name.", with a button that opens Level;
  - empty search: "No readings match "<q>"";
  - sensor missing: existing per-tool states, kept;
  - camera denied: existing, with a Settings link;
  - location denied: compass shows magnetic north labelled "Magnetic. Allow location for true north.";
  - storage write failure on photo save: a snackbar, and the numeric record is still saved.
  The app has no network dependency, so there is no offline state to add beyond ads.
- Done when: a test saves 3 readings in 2 jobs, filters by tool, exports, and checks the CSV text (header + 3 rows), and a test checks that deleting a photo record removes its file.

**M6. Own identity: template tells removed (criterion 4). Use these values.**
- **Drop the Apple Measure look.** No `#000000` + `#FFD60A`. New palette, a surveyor's field book:

  | Token | Light | Dark |
  |---|---|---|
  | background | `#F4F0E6` field-book paper | `#1B1F24` graphite |
  | surface | `#FFFDF7` | `#252A31` |
  | ink / primary text | `#17243A` | `#EEF1F4` |
  | primary (buttons, selected tab, dial ticks) | `#1D4E89` surveyor blue | `#7FA8D9` |
  | vial (in-tolerance, bubble, live accent) | `#5E7A12` for text, `#A7C93A` for fills | `#A7C93A` |
  | off-target / danger | `#B5452F` | `#E07A62` |

  None of these is a Tailwind default hex. Remove the `AppColors` alias class (`app_theme.dart:173-198`) and use `AppPalette` everywhere.
- **Typography:** bundle **Chivo** (UI and headings) and **Chivo Mono** (every live readout, with tabular figures) as TTF assets in `pubspec.yaml`, with no runtime font fetching. Both are published under the SIL OFL on Google Fonts; the developer must include the `OFL.txt` from the download in `assets/fonts/` and confirm the licence there. I checked `projects/real-apps/specs/*.md` and all pubspecs/Dart under `/Users/spatchava/agl`: no other app or spec uses Chivo.
- **Shape:** the instrument dials use 2 px ink hairlines and a vial-shaped bubble. Cards use a 6 pt radius with a 1 px ink-20% border, not the shared 12–14 pt rounded cards.
- **Home layout:** remove the 11-tile dashboard. The app has **4 tabs: Level (the start tab), Measure, Instruments, Jobs.** Level opens straight to the live Fall & Shim readout, because the app is a tool. Instruments is a list of Angle, Compass, Barometer and Sound, each row showing its live value when the sensor exists, or "No sensor on this device". On iOS the tab bar uses `CupertinoIcons`, and on Android Material icons, in the existing adaptive `AppTabBar`.
- **Onboarding:** replace the 3 pages and the "Get Started" button:
  1. "Level is only the start." Body: "Read any slope as %, mm per metre, inches per foot or roof pitch, and set the slope your job needs."
  2. "Know how much to shim." Body: "Enter the length of the board, and the app tells you which end to raise and by how much."
  3. "Keep the numbers with the job." Body: "Readings, photo measurements and angles go into a job you can export as CSV."

  Final buttons: **"Check a surface"** (to Level) and **"Name my first job"**. Onboarding asks for no permissions.
- **Launch screen:** a new `LaunchScreen.storyboard` with background `#1D4E89` and a new `LaunchImage` (the vial mark in `#A7C93A`/`#F4F0E6`), so the shasum differs from `3f6a9b27d8…`. Match it on Android (`android/app/src/main/res/drawable*/launch_background.xml`, values colour).
- **Icon:** a new icon, a horizontal spirit-level vial with a lime bubble slightly off-centre and two hairline tick marks, on surveyor blue `#1D4E89`. It must not be a Material glyph on a gradient, must not be neon, and must not carry an "iM" monogram. Replace iOS `AppIcon.appiconset` and the Android mipmaps (and the adaptive foreground/background) from one SVG in `assets/logo/`.
- **Splash and in-app wordmark:** remove "iM" and "Precision in your pocket". Use the vial mark and the app name. The app name is one constant (`AppInfo.displayName`) so the name decision (Q1) is a one-line change plus `CFBundleDisplayName` / `android:label`.
- **Ads placement:** the banner leaves the live instrument screens (a banner jumping under a level reading is bad for the job) and appears only on Jobs and Instruments list screens, one at a time. This keeps ads and the UMP Privacy choices row, and removes the "banner above every tab" scaffold. (Whether to keep ads at all is Q2.)
- Done when: `grep -rn "0xFFFFD60A\|0xFF000000" lib` returns nothing, `ThemeData.textTheme.bodyMedium.fontFamily == 'Chivo'` is asserted in a test, the storyboard shasum is not `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, "Get Started" is in no locale, and a screenshot of each tab, light and dark, is attached to the QA report.

**M7. Honest (criterion 5).**
- `ios/Runner/Info.plist`: the camera string becomes "Photo measure uses the camera to take a picture of the object next to a card or sheet of paper, so the length can be scaled from it." The motion string drops "Pedometer". Make the same wording change in Android if a rationale string exists.
- Remove the "±1–5 cm" / "±0.2–1 cm" tolerance figures (`measure_screen.dart:225-241`) **unless** the developer adds a documented measurement that backs them. Replace them with conditions: "Estimate. Reference and object must be in the same plane, phone square-on."
- No sample readings, no seeded jobs, no fake history. The store-screenshot integration test must not insert records directly; it already drives the real UI (`integration_test/store_screenshots_test.dart:25-28`), and that stays true.
- No hidden or remote switches. After M2 the only compile-time define left is `SCREENSHOT` (it hides the banner in screenshot builds, `banner_ad_slot.dart:33-48`). It may stay, because it hides an ad, not a feature.
- All new strings exist in all 16 locales (`test/i18n_completeness_test.dart` enforces this).

**M8. Proven (criterion 6).**
- `flutter analyze` is clean, and `flutter test` passes with the new tests from M1–M6. No test is skipped. Removed tests are listed in commit messages (M1, M2).
- Path-limited commits (never `git add -A`; never stage `fastlane/` or `project.pbxproj`), pushed to `main`.
- `flutter build ios --release --no-codesign` and `flutter build appbundle --release` both succeed (quote the output).
- **Launch on a physical iPhone** (Apple's 2.1(a) was a launch crash on iOS 27). If no physical device is available in the session, the QA report says "not verified on a physical device". It does not substitute a simulator and call it done.

### SHOULD
- **S1.** A Fall & Shim "walk" mode: the user saves several readings along a run (for example every metre of a gutter) into one job, and the job shows them as a small profile chart. On-device only.
- **S2.** Calibrate the Sound level with a user offset (against a known meter), with the label "user-calibrated" when set.
- **S3.** A lock-screen-safe "big digits" mode for the Level when the phone is face-down on a high shelf (screen readable from the side). This is a font-size toggle, not an orientation hack.
- **S4.** A Jobs export as a single PDF with the photo frames embedded (`pdf` package, on-device).
- **S5.** iOS pickers (units, theme, target) use `CupertinoActionSheet` / `showCupertinoModalPopup` on iOS.

---

## 5. Data source
- **On-device only.** Accelerometer and magnetometer (`sensors_plus`), barometer (`sensors_plus`), microphone (`noise_meter`), camera (`camera`), location solely to compute declination via the World Magnetic Model in `geomag` (no network), SharedPreferences for records/jobs/preferences, and the app documents directory for photo-measure JPEGs.
- **No Supabase, no public API.** After M2 the app makes no network calls of its own. The only network use is the AdMob SDK and the UMP consent form.
- Slope presets are geometric ratios, not data. No code citation unless the developer checks it (M3).

## 6. Store impact (for store-compliance; I did not edit `store/apps/iMeasure.json` or fastlane)

**Name (founder, Q1).** "iMeasure: Measure & Level" mirrors Apple's Measure app. Proposed instead: **"Plumbline: Slope & Level"** or **"Fall & Shim: Slope Level"**. App Store and Play name availability is **not verified**; ASC returned 409 on taken names for other apps before. The bundle id and package name stay.

**Subtitle (≤30):** "Slope, fall and shim heights". It must not equal the review-notes audience line.

**Keywords:** remove `converter`, `pedometer` and `measure` (Apple's app name). Proposed: `level,slope,grade,pitch,fall,shim,inclinometer,clinometer,angle,bubble,plumb,compass`.

**Description (en), proposed, with no "——" headings, not opening with the app name, and no comparative claims:**
> Put your phone on the board, the pipe or the floor and read the slope the way your job is specified: degrees, percent, millimetres per metre, inches per foot, 1:N or roof pitch.
>
> Set the slope you need, such as level, 1/4 in per ft, 1:12 or 6/12, and a tolerance. The screen tells you whether you are on it, too steep or too shallow. Enter the length of what you are levelling and it tells you which end to raise and by how much.
>
> Photo measure: hold a bank card or a sheet of A4 or Letter against the object, take a picture, mark the reference and the object, and the length is scaled from the reference. The photo is kept with the reading.
>
> Also on board: an angle finder that measures between two surfaces, a compass with true north, a barometer with altitude and a sound-level meter.
>
> Every reading can be filed under a job and exported as a CSV file.
>
> Readings come from your phone's sensors. They are good for DIY and quick checks, not a replacement for a calibrated instrument where a mistake is costly or unsafe. Slope requirements vary by local building code.
>
> The app shows ads. Where required, you can change your ad choices in Settings.

Remove "Eleven tools", "dark HUD", converter, pedometer, Quick Answers and "No account needed" (there will be no account at all). Promotional text and release notes follow the same content.

**Screenshots to retake (iPhone 6.9", iPad 13", Play phone/tablet), in this order:**
1. Level, Fall & Shim with target 1/4 in/ft, in tolerance, and the shim line;
2. the same reading off target ("Raise left end …");
3. Photo measure with the card reference and the object marked;
4. a job with readings and a photo thumbnail;
5. the Angle two-surface result;
6. Instruments list.

**1, 2 and 5 need a physical device**, because the simulator has no accelerometer (`store_screenshots_test.dart:30-36`). They must be real readings from a real surface. Retake the Play feature graphic in the new identity.

**Review notes, full rewrite (owner: store-compliance; founder sends):**
- No sign-in exists. Set `demo_account_required: false` and clear `demo_account_name`.
- External services: Google AdMob + UMP only. Remove Supabase, Google Sign-In, Sign in with Apple and In-App Purchase.
- Getting started: "Opens on Level. Lay the phone on any surface; tap the target chip to set a slope; enter a span to see the shim height."
- Audience is written out (section 2 of this spec), not the subtitle.
- Do not claim physical-device testing unless it happened. Drop the "simulators … a build that cannot start never ships" paragraph.
- The App Review contact should be a real person's name, not "App Reviewer" (founder).

**Age rating:** set Advertising = **Yes** in ASC (Apple 2.3.6 on this thread).

**Privacy label / Play data safety:** with sign-in gone, remove the account, email and user-ID collection. Location is used on the device for declination and is not collected. Camera photos and microphone stay on the device. AdMob's device identifiers and advertising data remain as declared for ads. This label must be **this app's own**, not the shared group label.

**Differentiation answers (Apple's 9 questions):**
- Q3 (gap): describe Fall & Shim factually, without naming competitors until verified.
- Q5/Q6: no other app in the account measures slope or uses the motion sensors, and the converter and pedometer were removed to end the overlap with CalcMaster and MyHealth.
- Q7: shared code is agl_ads and agl_observability only, with no Supabase.

## 7. Out of scope
- AR / LiDAR distance measuring (ARKit), room scanning, floor plans (RoomCraft's area).
- Unit conversion (CalcMaster), step counting or calories (MyHealth), any chat, Q&A or AI.
- Accounts, cloud sync and paid tiers. If sync is wanted later, it needs its own spec, a privacy-policy change and in-app deletion.
- Weather forecasting from the barometer.
- Replying to Apple, resubmitting, editing ASC/Play listings, or changing `store/apps/*.json` or fastlane (other owners; Charter §1).

## 8. Founder questions
- **Q1. App name.** Rename away from "iMeasure" (4.3(b) mirror of Apple Measure) to "Plumbline: Slope & Level" or "Fall & Shim: Slope Level", or another name? Play is live under the current name, so a rename changes a production listing. Name availability is not verified.
- **Q2. Ads.** Keep AdMob? The spec keeps it, but takes it off live instrument screens. Removing ads entirely would simplify the privacy label and the age rating (money decision, Charter §3).
- **Q3. Existing accounts.** Sign-in was reachable on the Play production build (Settings › Account & data). If anyone created an account through Google/Apple/email, after M2 their only deletion route is the support site. Is that acceptable, or should the founder approve a one-off production query to see whether any `auth.users` row came from this app (production data, Charter §2)?
- **Q4. Physical device.** Who captures the physical-device screen recording, the launch check (2.1(a)) and screenshots 1, 2 and 5? The office has no physical device in this session.
- **Q5. Resubmission.** Apple's text says not to resubmit without substantial changes. Once M1–M8 pass QA, does the founder resubmit, given the 5.6 freeze rule in `docs/store-holds.json` (MA-043, Charter §1)?
