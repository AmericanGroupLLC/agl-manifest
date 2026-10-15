# Spec: MileMaster: a mileage logbook that tells you which entries won't hold up before you file

Author: product-manager (AI office), 2026-10-12
Project: real-apps (`../plan.md`, criteria 1–7)
Repo: `/Users/spatchava/agl/MileMaster` (app at repo root, single `lib/`)
Base: `main` @ `95990de7a2f6c5f443f4939022aacfef91ca9d2d` (from `git rev-parse HEAD` and `git branch --show-current`, run 2026-10-12)
Baseline (run 2026-10-12 against that base):
- `flutter analyze` → "No issues found! (ran in 75.2s)"
- `flutter test` → "+207: All tests passed!"

**Other people's uncommitted work is in this repo. Do not touch it.** `git status --short` shows these as modified or untracked:
- `fastlane/metadata/**` (descriptions, notes.txt, promotional text, every screenshot, plus new 03–05 screenshots)
- `fastlane/screenshots/en-US/*`
- `ios/Podfile.lock`

This spec changes none of those files. The MUST items need **no new native plugin**: geolocator, sqflite, share_plus and shared_preferences are already present, and fonts are plain assets. CocoaPods therefore has no reason to rewrite `Podfile.lock`. If you take S3 (local notifications), it adds a plugin. Before you do, run `git diff ios/Podfile.lock`, and do not commit `Podfile.lock` while someone else's edit is in it.

---

## 1. Problem

**Store state:**
- **Apple:** rejected under **5.6** on 2026-10-08T14:19:42Z (`/Users/spatchava/agl/.dist/rejections.json` → "MileMaster"). Apple's words: "the app contains features that appear to have been intentionally hidden during the review process". The text is identical to the other 15 apps in that batch, so Apple judged the whole account.
- **Google Play:** PRODUCTION_DRAFT_STAGED.
- **4.3 / 4.2.6:** MileMaster was not among the apps rejected under these. It carries the portfolio's template tells, so it has to lose them before it is resubmitted.

**What works today:** read 2026-10-12, every file in `lib/`. Unlike several siblings, MileMaster does a real job:
- `services/trip_recorder.dart` + `services/distance.dart`: live GPS distance from a geolocator stream, with accuracy, jitter and speed filters. Unit-tested.
- `services/trip_repository.dart`: SQLite log, schema v1, one `trips` table.
- Manual entry by typed miles or an odometer pair (`main.dart:1300-1549`). Trips can be edited, deleted with Undo, and deleted by an accessibility action.
- `services/mileage_export.dart`: real PDF (`pdf` package) and RFC 4180 CSV, rated per trip, handed to the share sheet with an iPad popover anchor.
- `models/mileage_rates.dart`: per-year IRS rates with provenance, user overrides (`services/rate_settings.dart`), and a fallback that is flagged on screen.
- Twelve locales.

**What is wrong:**

1. **The rates are out of date, and the first screenshot says "this build".**
   - `kPublishedMileageRates` (`models/mileage_rates.dart:101-122`) stops at 2025, and today is 2026-10-12.
   - So every total on the dashboard renders the fallback line: "Rates: 70.0¢/mi — 2025 IRS rate, applied to 2026 because no 2026 rate is built in. This build ships no 2026 rate — check the current IRS figure and set it in Settings." I saw it in `fastlane/screenshots/en-US/iphone69-01.png` (someone else's uncommitted file, read only). The ARB strings are `app_en.arb:422` `rateFallbackWarning` and `:569` `rateNoteFallback`.
   - Every 2026 deduction is understated. The IRS set **two** 2026 rates, 72.5¢ for Jan 1–Jun 30 and 76¢ for Jul 1–Dec 31 (§3), and the app's one-rate-per-year model cannot represent a mid-year change.
   - The app also applies 70¢ to all of 2026.
2. **Recording stops when the phone locks.**
   - Recording is foreground-only. `location_gateway.dart:79-87` sets no `UIBackgroundModes`, and the app uses no Android foreground service.
   - The app keeps the screen awake with a wake lock and tells the driver: "Keep the app on screen while driving" (`app_en.arb:254`).
   - Every major competitor records with the screen locked (§2). A reviewer sees a trip tracker that needs the phone unlocked and open on the dashboard. It looks unfinished, and it is a bad thing to ask of a driver.
3. **The app does not say how much is enough.**
   - It produces a log, but never says whether that log would satisfy the IRS rules it cites: date, destination, written business purpose, total vehicle miles, and kept "at or near the time".
   - Filing season needs **last** year's log. The period picker offers only This month / This year / All time (`deductions.dart:178-205`).
   - The log has no search and no filter.
   - It has no commuting category, but Schedule C line 44b asks for commuting miles separately.
4. **5.6 exposure. Nothing is deliberately hidden, but some things are hard to find or hard to explain:**
   - The rates screen, the only settings screen, sits behind an unlabelled "tune" glyph (`main.dart:519-523`).
   - The Privacy choices row appears only where Google UMP requires it (`main.dart:1714-1770`). Meanwhile the review notes say "Features are identical in every region".
   - `AglInsights.init` (`main.dart:33`) starts Firebase Remote Config from the shared package (`agl_observability/lib/src/insights.dart:104-119`). MileMaster reads no key today, and it must stay that way.
5. **Template tells in this app** (the portfolio diagnosis in the task, checked here):
   - **Icon:** comes from the generator, `agl-manifest/scripts/generate_app_icons.py:71` `"MileMaster": ("speed", "#0D47A1", "#42A5F5")`.
   - **Splash:** shared. `ios/Runner/Base.lproj/LaunchScreen.storyboard` has shasum `3f6a9b27d80dda327ce7df82d4887e3adbac50e4` (measured), with a white background and a centred `LaunchImage`.
   - **`class AGL` neon monolith:** `lib/main.dart:131-166`, with Tailwind `3B82F6/06B6D4/10B981/F59E0B/EF4444` on `050A14`. Radial glow blobs at `main.dart:423-428`, blue gradient button, glow shadows. `main.dart` is 1,856 lines.
   - **Shared shell:** a custom bottom bar with `AglAdBanner` directly above it (`main.dart:444-451`). The header carries the shared "EN" language button (`main.dart:527-538`).
   - **Typography:** no typeface (pubspec has no `fonts:`), so the platform default renders.
   - **Platform style:** Material only. Zero Cupertino.
   - **Names:**
     - Home-screen and process names are `CFBundleName` "milemaster" (`ios/Runner/Info.plist:17-18`) and Android `android:label="milemaster"` (`AndroidManifest.xml:12`).
     - The store name is "iMileMaster" (`store/apps/MileMaster.json` → `copy.en.name`), while `CFBundleDisplayName` is "MileMaster".
   - **Play feature graphic:** shows the **default Flutter logo** on grey. I read `fastlane/metadata/android/en-US/images/featureGraphic.png`, 1024×500, and the subtitle is cut off: "GPS mileage tracker with IRS-compliant ded…".
   - **Privacy label:** `store/privacy/MileMaster.json` is byte-identical (after the app name is normalised) to 19 other apps, measured by md5. The content is *accurate* for this app, as §5 explains.
   - **Store copy:** the description opens with the app name, uses ALL-CAPS headings and the shared ads paragraph. By my regex count, 9 of 32 sentences (28%) are negations. The task's figure is 34%, by a different method.
   - **Review notes:** the shared "2. DEVICES…" skeleton. The audience line is the subtitle pasted in ("GPS mileage log for taxes").

**Worth keeping exactly as is:**
- the distance accumulator and its tests;
- the repository pattern;
- the honest empty and error states;
- delete with Undo plus the semantics action;
- the export's `pdfSafe` handling and iPad anchor;
- the rate provenance principle (a figure always shows its rate and source);
- `PrivacyChoicesTile`;
- foreground location *permission* only (no `ACCESS_BACKGROUND_LOCATION`, no "Always").

## 2. User, core job, signature feature

**User.** A US driver who files **Schedule C** and takes the **standard mileage rate**:
- a rideshare or delivery driver;
- a real-estate agent;
- a home-care, cleaning or field-service contractor;
- a sales representative on the road.

They drive several times a day for work. They need a log they would be comfortable handing to a preparer or an IRS examiner, and they want it in February without reconstructing a year from memory.

**Core job: log every work drive with a defensible record, and hand over the year's log at tax time.**
- Tap **Start drive**, put the phone away (screen locked), and drive.
- Tap **Stop** and pick a purpose: Business / Commute / Personal / Medical / Charity. A business trip asks for a one-line business purpose.
- The trip is rated at the IRS rate **for the date it was driven**, including mid-year changes.
- At year end, pick the tax year and export a PDF and a CSV.

**Signature feature: "Records check".** For any tax year it does two things.

1. **It fills in the vehicle questions.** Schedule C Part IV asks them: line 43 date placed in service, 44a business miles, 44b commuting miles, 44c other miles. Form 4562 Part V asks the same questions. MileMaster answers them from the log plus the user's year-start and year-end odometer readings, and adds the business-use percentage.
2. **It lists every entry that is missing what IRS Publication 463 says a car record needs.** Measured from the IRS page on 2026-10-12, Table 5-1 lists: "the mileage for each business use, and the total miles for the year", the "Date", "Your business destination", and "Business purpose". The page also says "If you maintain a log on a weekly basis … the log is considered a timely kept record". The checks are:
   - a business trip with no written purpose;
   - a destination that is only coordinates or "not specified";
   - a trip entered more than 7 days after it was driven;
   - a GPS trip with an untracked straight-line stretch;
   - a year with no start or end odometer reading.

Each gap is one tap from the trip editor and disappears when fixed. The figures and the gap list are printed as the first page of the exported PDF.

**Competitor check.** WebSearch is disabled in this session ("Internet mode is not enabled"). On 2026-10-12 I used Apple's keyless iTunes Search API (`itunes.apple.com/search?term=mileage+tracker&entity=software&country=us`, HTTP 200) and read the store descriptions only. **I did not run these apps. How they behave beyond their own descriptions is not verified.**

| App (App Store id, rating count) | Its description claims |
|---|---|
| MileIQ (578830929, 114,550) | Automatic background tracking; "IRS-compliant reports… Schedule C or 1099 filings"; "audit readiness"; "40 free drives every month", then Premium |
| Everlance (985378916, 52,751) | Automatic background recording; "current irs rate of 76 cents per mile"; paid "Professional" with "$1M audit protection" |
| Stride (1041591359, 97,961) | Automated GPS tracking; "IRS-ready standard mileage log"; reminders |
| Driversnote (924418916, 39,104) | Automatic tracking, iBeacon; odometer readings; multiple vehicles; "percentage split… work vs personal"; annual Pro subscription |
| TripLog (585918522, 4,749) | Free automatic detection; "commute deductions"; one free 7-day premium pass a year for annual reports |
| Mile Logger (Dajax, 1078393112, 3,871) | Free, no account, iCloud; "2026 irs rate built in… $0.725/mile" (that is the Jan–Jun 2026 rate only) |

**The honest gap is narrow.** All six claim "IRS-compliant / audit-ready" logs, and Driversnote already offers a work/personal percentage. None of the six descriptions mentions any of these (keyword scan for "missing", "substantiat", "timely", "part iv", "4562", "line 44", "placed in service" found none):
- (a) checking each entry against the Pub 463 elements and listing the gaps before filing;
- (b) producing the Schedule C Part IV line values (43/44a/44b/44c);
- (c) rating each trip by the half-year IRS period it falls in. Mile Logger's description quotes only $0.725.

MileMaster's further angle:
- free with nothing to buy;
- no account;
- the log never leaves the phone.

It **does not** detect drives automatically. Every competitor above does, and we say so plainly (out of scope, §7). Calling it "audit-proof", or promising any IRS outcome, is forbidden.

## 3. Data sources (real, keyless or on-device; verified 2026-10-12)

| Data | Source | Proof |
|---|---|---|
| IRS standard mileage rates, all periods 2022 onward | Shipped constant table, copied from `https://www.irs.gov/tax-professionals/standard-mileage-rates` | `curl -A "Mozilla/5.0"` → HTTP 200, 109,863 B. The page was last reviewed 28-Jul-2026. Rows (business / charity / medical, ¢/mi, with source): **2026 Jul 1–Dec 31: 76 / 14 / 23.5, IR-2026-29**. **2026 Jan 1–Jun 30: 72.5 / 14 / 20.5, IR-2025-128**. 2025: 70 / 14 / 21, IR-2024-312. 2024: 67 / 14 / 21, IR-2023-239. 2023: 65.5 / 14 / 22, IR-2022-234. 2022 Jul 1–Dec 31: 62.5 / 14 / 22, IR-2022-124. 2022 Jan 1–Jun 30: 58.5 / 14 / 18, IR-2021-251. |
| What a car record must contain, and the weekly "timely kept" rule | IRS Publication 463, `https://www.irs.gov/publications/p463` | HTTP 200, 848,614 B. Quotes in §2. Used for the check rules and the on-screen citations, not fetched at run time. |
| What Schedule C Part IV asks | Instructions for Schedule C, `https://www.irs.gov/instructions/i1040sc` | HTTP 200, 337,816 B. Has the "Part IV. Information on Your Vehicle" and "Line 44b" commuting definitions. |
| Trips, odometer readings, vehicle, onboarding answers | On-device: SQLite (`milemaster.db`, schema v2) and `shared_preferences` | n/a |
| Start/end address labels | OS geocoder through the `geocoding` plugin (existing). Falls back to coordinates offline. | existing code, `location_gateway.dart:168-195` |
| Typeface | **Overpass** and **Overpass Mono**, SIL OFL, bundled as assets. Overpass is derived from Highway Gothic, the US road-sign face. | `raw.githubusercontent.com/google/fonts/main/ofl/overpass/METADATA.pb` → HTTP 200, `license: "OFL"`, `Overpass[wght].ttf`. `ofl/overpassmono/METADATA.pb` → HTTP 200, `license: "OFL"`. |

The app makes no network call of its own: no API, no Supabase, no key. Rates are not fetched at run time, because irs.gov is an HTML page, not an API, and scraping it in-app would be fragile. A new IRS period therefore needs a release. Until then the user can type it in (§4 M1).

**Notes for the developer:**
- Use the IR news-release numbers above as the `source` labels. They are what the IRS table cites, and I verified them. The current labels ("IRS Notice 2023-03", "2024-08", "2025-05") are not on that page and I did not verify them.
- The fonts' upstream files are variable TTFs. Either bundle them and set the weight through `fontVariations: [FontVariation('wght', w)]` in the text theme, or bundle static instances from the upstream Overpass release. Add a widget test that renders text in each weight you use, so a missing weight fails the test.
- Do not add `google_fonts`. It fetches fonts at run time, and the app must work offline.
- Ship `OFL.txt` beside the fonts and list it in the app's licences (`LicenseRegistry.addLicense`).

## 4. Acceptance criteria

### MUST (what Apple must see to judge this a real, distinct app)

**M1. Correct rates for every day a trip can fall on, including mid-year changes, and the "this build" fallback copy removed.**

*Model:*
- Replace the per-year `Map<int, MileageRateTable>` with a list of `MileageRatePeriod {DateTime from; DateTime toExclusive; business; medical; charity; source}` holding the seven periods in §3.
- `resolve(DateTime date)` returns the period containing the trip's start date.
- User overrides are keyed by period start and persisted in `shared_preferences` under a new key.
- Migrate the old `milemaster.rate_overrides.v1` year overrides into full-year periods (Jan 1 → next Jan 1) on first load. A user's edit must not be lost.

*Calculation:*
- `MileageSummary`, the trip row, the stats breakdown, the PDF and the CSV all rate **per trip date**.
- A period that straddles a change (for example "2026") shows one line per rate period: "Jan 1–Jun 30 · 72.5¢ · IR-2025-128" and "Jul 1–Dec 31 · 76¢ · IR-2026-29".

*After the last shipped period* (2027-01-01 onward):
- Apply the newest period's rate.
- Show, without the word "build", for example: "No IRS rate for 2027 is included in MileMaster yet. Using 76¢ (Jul–Dec 2026) until you enter the 2027 rate." Include a button that opens the rate editor for 2027.

*Acceptance:*
- (a) Unit tests:
  - a 2026-06-30 23:30 local business trip → 72.5¢;
  - 2026-07-01 00:10 → 76¢;
  - 2022-06-30 → 58.5¢, 2022-07-01 → 62.5¢;
  - medical 2026 H1 → 20.5¢, H2 → 23.5¢;
  - 2027-02-01 → 76¢ with `isFallback == true`;
  - an old v1 override for 2025 survives the migration.
- (b) `grep -rniE "this build|in this build|ships no" lib` → 0 hits. That covers Dart, all 12 ARBs and the generated localisations.
- (c) With clock 2026-10-12 and a fresh install, the home screen shows no fallback warning.

**M2. A started drive keeps recording with the screen locked (core job).**

The user starts the drive, and permission stays **When In Use**.

*iOS:*
- Add `UIBackgroundModes` → `location` to `ios/Runner/Info.plist`.
- `positions()` uses `AppleSettings(accuracy: high, distanceFilter: 10, activityType: ActivityType.automotiveNavigation, allowBackgroundLocationUpdates: true, showBackgroundLocationIndicator: true, pauseLocationUpdatesAutomatically: false)`. The blue status-bar pill shows the user that a drive is recording.

*Android:*
- `AndroidSettings(foregroundNotificationConfig: ForegroundNotificationConfig(notificationTitle: "Recording a drive", notificationText: "<miles> so far · tap to return", enableWakeLock: true, setOngoing: true))`.
- Add `FOREGROUND_SERVICE` and `FOREGROUND_SERVICE_LOCATION` to `AndroidManifest.xml`. geolocator_android 5.1.1+1, already in the pub cache, declares its service with `foregroundServiceType="location"`.
- **Still no `ACCESS_BACKGROUND_LOCATION`.**

*Wake lock:*
- Remove the screen wake lock (`wakelock_plus`). It is no longer needed, and it drained the battery on the dashboard.
- Keep the `TripRecorder.backgroundGaps` accounting. A gap now means the OS actually delivered no fixes, not that the screen locked. Persist `gap_seconds` on the trip (M4).

*Copy:*
- Replace `driveBackgroundGap` ("Keep the app on screen…") with, for example: "No position arrived for {minutes} min (no GPS signal). That stretch is counted as a straight line."
- Update the `NSLocation…UsageDescription` strings to: "Measures the distance of a drive you start in MileMaster, including while the phone is locked, until you tap Stop. MileMaster never detects drives on its own and never uses location when no drive is running."

*Acceptance:*
- (a) `plutil -extract UIBackgroundModes json -o - ios/Runner/Info.plist` → `["location"]`, plus the other modes the file already lists.
- (b) A unit test with a fake gateway asserts that `positions()` is requested with background settings.
- (c) On a **physical** iPhone and Android phone: start a drive, lock the screen, drive or walk at least 0.5 mi, unlock, stop. Distance > 0.4 mi and `gap_seconds == 0`. Record it on screen. If nobody can do this in the session, report "not verified on device". Do not claim it.
- (d) If the founder declines the Play foreground-service declaration (Q2), ship the Android build with foreground-only recording. In that case the Android-specific copy must say so, and the store copy in §5 must be split per platform.

**M3. Signature: Records check (per tax year).**

*Entry:* a row on the home screen, "Records check · 2026 · {n} to fix" (or "Nothing to fix"), opening a full screen with a tax-year picker covering every year that has trips, plus the current year.

*Section 1, "Your vehicle (Schedule C Part IV)":*
- **43** Date placed in service, from M6 onboarding or Settings. If it is missing: "Add the date you started using this car for business."
- **44a** Business miles: sum of business trips.
- **44b** Commuting miles: sum of commute trips.
- **44c** Other miles:
  - If both a year-start and a year-end odometer reading exist (a reading within ±31 days of Jan 1 and of Dec 31, or today for the current year): (end − start) − 44a − 44b.
  - Otherwise: personal + medical + charity logged miles, labelled "from your log only — add odometer readings for the full figure".
  - A negative result (logged miles exceed odometer miles) is shown as a gap: "Your trips add up to more than the odometer moved — check the readings", never clamped silently.
- **Business-use %**: 44a ÷ total vehicle miles, shown only when both odometer readings exist.
- Each line shows its IRS line number and one sentence of what it means. The commuting definition is paraphrased from the Schedule C instructions with a link to `irs.gov/instructions/i1040sc`.

*Section 2, "Entries to fix" (Pub 463 elements). Each row names the trip (date, from → to, miles) and the rule:*
- (a) Business trip whose purpose text (M4) is empty → "No written business purpose".
- (b) End label equals the not-specified/not-located strings, or matches the coordinate format `^-?\d+\.\d{5}, -?\d+\.\d{5}$` → "Destination is only coordinates" or "No destination".
- (c) `created_at − started_at > 7 days` → "Entered {n} days after the drive. Pub 463 treats a log kept weekly as timely." Trips from schema v1 have `created_at = NULL` and are **not** flagged; they show "entry date not recorded (logged before version 1.1)" once, as a group.
- (d) `gap_seconds > 0` → "{m} min of this drive had no GPS and was estimated".
- (e) No year-start or year-end odometer reading → "Add the odometer reading for Jan 1" / "for Dec 31".
- Tapping a row opens the trip editor (or the odometer sheet). On save, the row disappears without reloading the screen.

*Section 3:* "What this check is". Two sentences:
- It checks the elements Publication 463 lists for car use.
- It is not tax advice and does not guarantee any outcome.

Link `irs.gov/publications/p463`.

*Export:* page 1 of the PDF becomes "Vehicle summary — {tax year}". It holds lines 43, 44a, 44b, 44c, the business-use %, the odometer readings with dates, and "Entries flagged: {n}" listing each flagged trip and its rule. The CSV gains `Purpose detail`, `Entered on` and `Flags` columns.

*Acceptance:* unit tests for every rule (a)–(e) and for 44c, using:
- both odometer readings;
- one reading;
- readings that make 44c negative;
- a mixed year with v1 rows (created_at null).

Plus a widget test: fix a flagged trip from the Records check screen, and the count drops by one. Plus a PDF test: page-1 text contains "44a" and the computed business miles.

**M4. Depth: persistence, search/filter, tax-year export, error/offline states.**

*Schema v2*, a migration in `onUpgrade` that keeps every v1 row:
- `ALTER TABLE trips ADD COLUMN created_at INTEGER` (NULL for old rows);
- `ADD COLUMN gap_seconds INTEGER NOT NULL DEFAULT 0`;
- `CREATE TABLE odometer_readings (id INTEGER PRIMARY KEY AUTOINCREMENT, read_on INTEGER NOT NULL, value REAL NOT NULL, note TEXT NOT NULL DEFAULT '')`.

*Other model changes:*
- New purpose `TripPurpose.commute`. It is not deductible and is exported as "Commute".
- For business trips, the existing `notes` field is labelled **"Business purpose (who / why)"** with the hint "e.g. Site visit for the Lee kitchen job". That is a format example in the hint text, not stored data.

*Trip log ("Full log" screen):*
- Grouped by week. Each week header shows its miles and a ✓ when every business trip in it has a purpose.
- A search field matching from, to and purpose text.
- Purpose filter chips.
- A "Needs attention" filter (the M3 rules).
- A tax-year picker.

*Export:*
- Tax-year picker: every year with trips, "This month", "All time". Default in Jan–Apr is the **previous** year.
- File names carry the period: `milemaster-2025.pdf` / `.csv`.

*States:*
- **Location permission denied forever:** an inline card with "Open Settings" (`Geolocator.openAppSettings()`) and "Add a trip by hand". This replaces the snackbar-only message.
- **Offline:** labels fall back to coordinates (existing), and M3 rule (b) flags them so the user can rename them later.
- **Load error:** keep the existing error state.
- **Delete all data:** in Settings, "Delete all trips and readings". A confirmation offers **Export first** before it deletes.

*Acceptance:*
- a repository test opens a v1 database containing rows, upgrades it, and every row survives with `created_at == null`;
- search/filter widget tests;
- a test that commute miles appear in 44b and are excluded from the deduction;
- an export test that the 2025 tax-year CSV holds only 2025 trips.

**M5. Its own identity: visual system and layout, with the shared furniture removed.**

*Palette, a light-first "logbook paper":*

| Role | Light | Dark |
|---|---|---|
| Page background | `#F6F1E4` | `#121814` |
| Card | `#FFFDF7` | `#1C231F` |
| Ink | `#1F2A24` | `#E9E4D6` |
| Muted ink | `#5E6B63` | — |
| Ruled lines | `#D9D2C0` | — |
| Primary (road-sign green) | `#0E6B47`, on-primary `#FFFFFF` | `#3FA27A` |
| Recording / warning (sign amber) | `#E8A317` | — |
| Error | `#B3261E` | — |

Purpose colours:
- business `#0E6B47`;
- commute `#5E6B63`;
- personal `#8A7F68`;
- medical `#B3261E`;
- charity `#6B4E9B`.

I grepped every sibling's `lib/` and found no use of `0xFF0E6B47`, `F6F1E4`, `1F2A24`, `E8A317` or `B3261E`. Follow the system brightness. Build the `ColorScheme` explicitly from these values, not `fromSeed`.

*Typography:*
- **Overpass** for all UI text.
- **Overpass Mono** for every figure: miles, money, odometer, rates.
- Titles at weight 700, body 400.

*Shape:*
- 4 px corners on cards, inputs and buttons. The sheet top is 12.
- 1 px ruled borders.
- **No** gradients, glow shadows or radial blobs.

*Home layout, "Logbook":* one screen, no bottom navigation bar. Top to bottom:
1. App name and a labelled **Settings** button (on iOS a `CupertinoIcons.gear` with the text "Settings"; on Android an icon button with a tooltip).
2. **Odometer strip:** this tax year's business miles in boxed Overpass Mono digit cells, like a mechanical odometer, with the deduction and the current rate period underneath.
3. A full-width **Start drive** bar (green; amber "Stop" while recording).
4. The Records check row (M3).
5. **This week**: ledger rows (date | from → to | purpose | miles) on ruled lines, then "Open full log" and "Add trip by hand".

*Recording screen:*
- Full screen while a drive runs: a large distance in Overpass Mono, the elapsed time, "Recording — you can lock your phone", and a full-width Stop.
- No ads and no other controls.

*Code:*
- Delete `class AGL`.
- Split `main.dart`:
  - `lib/main.dart` keeps bootstrap only, at most 120 lines;
  - `lib/ui/theme.dart` (`MileMasterTheme`, no class named `C` or `AGL`);
  - `lib/ui/logbook_screen.dart`, `recording_screen.dart`, `full_log_screen.dart`, `records_check_screen.dart`, `trip_editor_screen.dart`, `settings_screen.dart`, `onboarding_screen.dart`.

*iOS feel:*
- On iOS use `CupertinoIcons` for navigation and actions.
- Use `Switch.adaptive`, `showAdaptiveDialog` and `CupertinoSlidingSegmentedControl` for the tax-year and purpose filters.
- `CupertinoPageRoute` transitions come from `ThemeData.platform`. The default Material theme on iOS already uses them; keep them.
- `cupertino_icons` is already a dependency (`pubspec.yaml`).

*Header furniture:*
- Remove the "EN" language button from the header. Language moves into Settings and still uses `AglLanguageScreen`, because it serves 12 locales.

*Ads:*
- `AglAdBanner` appears **inline**: as the last item of the Logbook scroll content and as the footer of the Full log list. It is never pinned above a navigation bar, and never on the recording, onboarding, Records check or Settings screens.
- `AglAds.onTransition()` is called only when the user returns from Full log to Logbook, and never while a drive is recording. Q5 asks the founder whether interstitials stay at all.

*Icon and launch screen:*
- A new icon that is **not** from `generate_app_icons.py`: a cream ledger page (`#F6F1E4`) with a green (`#0E6B47`) road curving up the page and a small amber mile-marker post. No Material Icons glyph.
- Remove the `"MileMaster"` row from the `DESIGN` table in `agl-manifest/scripts/generate_app_icons.py`, so a re-run cannot overwrite it. That script is not one of the paths frozen for this task.
- Own `LaunchScreen.storyboard`: background `#F6F1E4` with the new mark. Its shasum must differ from `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`. Android `launch_background.xml` uses the same colour.

*Names:* `CFBundleName` → "MileMaster"; Android `android:label` → "MileMaster".

*Acceptance:*
- (a) `grep -rnE "0xFF(3B82F6|06B6D4|10B981|F59E0B|EF4444|050A14|A78BFA|1D4ED8|DC2626)" lib` → 0.
- (b) `grep -rn "class AGL\b\|class C\b\|RadialGradient\|LinearGradient" lib` → 0.
- (c) `grep -rn "NavigationBar\|bottomNavigationBar" lib` → 0.
- (d) `shasum ios/Runner/Base.lproj/LaunchScreen.storyboard` ≠ `3f6a9b27…`.
- (e) `grep -n MileMaster agl-manifest/scripts/generate_app_icons.py` → 0 lines inside `DESIGN`.
- (f) A golden or widget test asserts the Logbook's `TextStyle.fontFamily == 'Overpass'` and that figures use `'Overpass Mono'`.
- (g) Launch the app on the iOS simulator and on an Android emulator and take a screenshot of Logbook, Recording, Records check and Full log. Look at each one: no white screen, fonts rendered (not the fallback). Attach the screenshots to the report.

**M6. Its own onboarding and settings copy.**

*First run: three short screens, stored in `shared_preferences`, re-openable from Settings → "How MileMaster works":*
1. **"What do you log miles for?"** Choices: Self-employed or gig work (Schedule C) / An employer reimburses me / Medical and charity only. The choice sets the default purpose for new drives and whether Records check opens on the Schedule C section.
2. **"Your car."**
   - A name, typed by the user. The hint "e.g. Blue Civic" is a hint, not a value.
   - "Date you started using it for business."
   - "Odometer now", optional, saved as the first odometer reading dated today.
   - "Skip" is allowed.
3. **"How recording works."**
   - You tap Start; it keeps going with the phone locked; you tap Stop and choose a purpose.
   - It never starts on its own.
   - Your log stays on this phone.
   - Then **"Open my logbook"**.

Location permission is still requested only at the first Start drive.

*Settings*, MileMaster's own sections in this order:
- Mileage rates (periods and overrides);
- Your car and odometer readings (add, edit, delete, each dated);
- Default purpose;
- Language;
- Privacy choices (only where Google requires it; see §5 review notes);
- Delete all trips and readings;
- How MileMaster works;
- About (version, "stored only on this phone", the tax disclaimer, open-source licences).

*Acceptance:*
- `grep -rniE "get started|welcome back|welcome to" lib/l10n/app_en.arb lib/ui` → 0.
- A widget test covers a fresh install: onboarding → choose Schedule C → skip car → Logbook is shown. A second launch skips onboarding.
- The odometer value from step 2 appears in Records check as the year-start reading when it is dated within 31 days of Jan 1. Otherwise it is listed as a dated reading.

**M7. Honest and nothing hidden (5.6).**
- Every screen is reachable from Logbook by visible, labelled controls: Settings, Records check, Open full log, Add trip, Start drive.
- No feature depends on region, locale, date, build flag or remote value. There are two exceptions, both stated in the review notes:
  - rates depend on the **trip's date** by design;
  - the Privacy choices row depends on Google UMP.
- `grep -rnE "fromEnvironment" lib` → only `AglAdIds.fromEnvironment` in `main.dart`. That call is the shared ads package's API; mention it in the commit message.
- `grep -rnE "AglInsights\.(get|remote|config)|RemoteConfig" lib` → 0. MileMaster reads no Remote Config value.
- No demo data, no sample trips, no seeded odometer. Fresh install: empty Logbook with "No drives yet. Tap Start drive, or add a trip by hand." Records check on a fresh install: "No trips in 2026 yet."
- In user-facing English strings: `grep -niE "coming soon|not connected|simulator|unavailable in" lib/l10n/app_en.arb` → 0.
- No copy claims "IRS-approved", "audit-proof" or "guaranteed": `grep -niE "audit-proof|irs[- ]approved|guarantee" lib/l10n/app_en.arb` → 0.

**M8. Proven.**
- `flutter analyze` → "No issues found!".
- `flutter test` → all pass. The count must be **≥ 207 plus the new tests**, with no test deleted or skipped. If an old test is rewritten because its UI moved, say which one and why in the commit.
- Update `test/l10n_coverage_test.dart`'s walk so it covers the new screens (Onboarding, Logbook, Recording, Full log, Records check, Settings). Every new string goes into all 12 ARB files; the test fails on any English left in Spanish.
- Update `integration_test/store_screenshots_test.dart` to drive the new flows (decision Q3 governs what data it types).
- `strings build/ios/iphoneos/Runner.app/Frameworks/App.framework/App | grep -ciE "this build|ships no"` → 0 on a release build. This checks the binary Apple inspects.
- Commit path-limited (`git add lib test integration_test pubspec.yaml pubspec.lock assets ios/Runner/Info.plist ios/Runner/Base.lproj ios/Runner/Assets.xcassets android/app/src/main` …). **Never** `git add -A`; never touch `fastlane/` or `ios/Podfile.lock`. Push to `main`.
- `python3 scripts/verify_api_hosts.py --print` is n/a: the app adds no host.

### SHOULD (after every MUST passes)

- **S1. Several vehicles.** A `vehicles` table and a `vehicle_id` on trips and odometer readings. Records check and export are per vehicle; Schedule C Part IV is per vehicle. One vehicle stays the default UI.
- **S2. Frequent places.** Autocomplete for From/To and the business purpose, built from the user's own past trips (on-device, most-used first). "Add trip by hand" then takes a few seconds.
- **S3. Weekly "close the week" reminder.** A local notification on a weekday and time the user picks, saying how many of this week's business trips lack a purpose. It needs `flutter_local_notifications`, a new plugin: mind the `Podfile.lock` trap in the header.
- **S4. Round trips.** "Return trip" on any trip row duplicates it reversed, with today's date.
- **S5. Accessibility re-check** of the new layouts at 2.0× text scale and on a 320 pt-wide screen, following the existing `layout_test.dart` / `foldable_layout_test.dart` patterns.

## 5. Store impact

The office applies these after the build and QA pass, through store-compliance. **This spec does not edit `store/apps/*.json`, fastlane metadata or `docs/`.**

**Name.** Store "iMileMaster" (the 'i' was a workaround for a name already taken, per the task's evidence) and device "MileMaster". Proposed store name: **"MileMaster: IRS Mileage Log"** (27 characters). I have not checked whether App Store Connect accepts it. Founder decision, Q1.

**Subtitle** (≤30): "Mileage log, checked for taxes" (30).
**Promotional text** (≤170): "Rates each drive at the IRS figure for its date — including July 2026's change to 76¢ — and shows which entries still need a purpose or destination before you file."
**Keywords**: `mileage log,mileage tracker,schedule c,irs rate,business miles,odometer,gig driver,1099,deduction,trip log`

**Description draft.** It does not open with the app name and uses no ALL-CAPS headings, and only states what the app does not do where the user needs to know it:

> Keep a mileage log you'd be comfortable handing to your tax preparer.
>
> Tap Start drive, lock your phone and drive. When you stop, choose Business, Commute, Personal, Medical or Charity, and add a line about who the trip was for. Every trip is rated at the IRS standard mileage rate for the date you drove it — 72.5¢ for January–June 2026 and 76¢ from July 1, 2026 — with the IRS release named beside the figure.
>
> Records check looks over your tax year the way IRS Publication 463 describes a car record: mileage, date, destination, and business purpose, kept close to the time. It lists the trips that are missing one, and fills in the vehicle figures Schedule C asks for — business, commuting and other miles — from your trips and your odometer readings.
>
> Search and filter your log by place, purpose or week. Export any tax year as a PDF with a vehicle summary on the first page, plus a CSV of the same trips.
>
> Trips can also be entered by hand from miles or two odometer readings. Your log is stored only on this phone, with no account. MileMaster records only drives you start yourself. It shows Google AdMob ads, never while a drive is recording; where the law requires consent you are asked first and can change it in Settings. MileMaster is a record-keeping tool, not tax advice.

If Q2 is declined, replace "lock your phone and drive" with platform-accurate wording.

**Screenshots to retake** (iPhone 6.9", iPad 13", Play phone and tablet), in this order:
1. Recording screen over a locked-phone context ("Recording — you can lock your phone")
2. Records check with Schedule C lines and two flagged entries
3. Logbook with odometer strip and this week's ledger
4. Full log, search and "Needs attention" filter
5. PDF page 1, "Vehicle summary"

The current screenshot 01 shows the "This build ships no 2026 rate" line and must not be reused. Data shown: see Q3.

**Play feature graphic.** Replace the Flutter-logo graphic with one built from the new icon and palette (paper `#F6F1E4`, green road, Overpass headline "Mileage log, checked for taxes"). The current one is the default Flutter logo.

**Review notes**: replace the shared skeleton entirely. Draft:

> MileMaster is a mileage log for US self-employed drivers — rideshare and delivery drivers, real-estate agents, home-care and field-service contractors — who deduct business miles at the IRS standard rate on Schedule C.
>
> To see the main feature: open the app (no account), answer the three first-run questions (you can skip the car step), tap Start drive, allow location "While Using", lock the phone and walk or drive a short distance, unlock, tap Stop and choose Business. Then tap "Records check" on the home screen: the new trip is listed as missing a business purpose; tap it, type a purpose and save, and it leaves the list. Export (Full log → Export) produces a PDF and CSV.
>
> Location: used only between Start and Stop of a drive the user begins, including while the phone is locked (iOS shows the blue location indicator; Android shows a persistent notification). The app never detects drives by itself and never requests "Always" access. Trips are stored only on the device; the address labels come from the system geocoder.
>
> Everything is reachable from the home screen. Two things vary by design: rates depend on the date of each trip (IRS periods built in up to December 31, 2026, editable in Settings → Mileage rates), and the "Privacy choices" row in Settings appears only where Google's consent rules apply (EEA, UK, Switzerland). Ads are Google AdMob banners on the home and log screens and an occasional full-screen ad when returning from the log; none appear while a drive is recording.
>
> No demo account is needed.

Add a device-testing sentence **only** after a person has run the release build on a physical iPhone. Name the device and the iOS version (Q4). Drop the simulator sentence and "a build that cannot start never ships".

**Privacy label.** The data practices do not change: location never leaves the device; ads use the device ID and advertising data; crash and analytics data come through the shared packages. So the current label stays **accurate**, even though it is byte-identical to 19 other apps. Do not invent a difference. On Play's Data safety form, re-confirm "Location: not collected", because coordinates stay on-device.

**Play Console.** Adding `FOREGROUND_SERVICE_LOCATION` requires the foreground-service declaration (task type plus a short video of the recording flow) before the update can be published. That is Q2.

**`store/apps/MileMaster.json` → `differentiation`:**
- §3 "GAP IT FILLS" can now be answered from §2 of this spec: the Records check, and per-date IRS periods, against named competitors.
- §1 lists the new screens.

## 6. Founder questions

See the structured output. They are also listed here:
1. **Store name.** Change "iMileMaster" to "MileMaster: IRS Mileage Log"? Availability is not checked.
2. **Play foreground-service declaration** for location (needed for M2 on Android). Approve filing it? If not, Android stays foreground-only and the copy splits by platform.
3. **Screenshot data.** The committed screenshot test types invented trips with fictional businesses ("Hartwell & Co., 410 Market St", "Brightline Logistics, Fremont"; `integration_test/store_screenshots_test.dart:57-92`). Should screenshots use your own real drives, or neutral entries typed through the real form ("Home office → Client site")? The office will not invent figures on its own say-so.
4. **Physical-device test and review contact.** Who runs the release build on a physical iPhone, so the notes can truthfully name the device? And what real name replaces "App Reviewer" as the review contact?
5. **Ads.** Keep the occasional interstitial (on return from Full log), or drop interstitials and keep inline banners only? This is a money decision (Charter §3).
6. **Category.** Stay in Business, or move to Finance where the named competitors sit? MyFinance is already in Finance on this account.

## 7. Out of scope

- **Automatic drive detection** (starting a log without a tap). It needs "Always" location or activity recognition and an always-on background service. Stated plainly in the copy.
- Accounts, cloud sync, Supabase. The log stays on-device.
- Expense, receipt, fuel or budget tracking: that is MyFinance's job, and must not be duplicated.
- Maps, routing, turn-by-turn, or computing road distance between typed addresses: that is iMaps's job. The public OSRM/Nominatim demo servers' usage policies also rule them out for production.
- The actual-expense method, depreciation, reimbursement approval workflows, team accounts.
- Non-US rates (CRA, HMRC, ATO).
- Fetching IRS rates at run time.
- Any change to `store/apps/*.json`, fastlane metadata, `docs/`, `ios/Podfile.lock`, or other people's uncommitted files.
