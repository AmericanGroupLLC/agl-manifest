# Spec: MyFinance becomes "a hand-kept ledger that tells you what's free until payday"

- Author: product-manager (AI office), 2026-10-12
- Repo: `/Users/spatchava/agl/MyFinance`, branch `main`, base_sha `8c001fd6c9387b891de59619d8a423439edb5640` (`git rev-parse HEAD` and `git branch --show-current`, both run today)
- Apple: rejected under **4.3 Spam / 4.2.6 App Generation Services** (`/Users/spatchava/agl/.dist/rejections.json` key `MyFinance`: 2 threads, version 1.0.0). It is the same 4.3/4.2.6 text that went to 26 apps within one minute on 2026-10-05, and it names no screen. Google Play: PRODUCTION_DRAFT_STAGED.
- Plan: `projects/real-apps/plan.md` (seven acceptance criteria). Overlap table: `projects/real-apps/overlap.md:64`. **MyFinance owns the offline ledger, budgets and recurring money, with no bank login.**
- Baseline, measured today in the repo: `flutter analyze` gave "No issues found! (ran in 9.7s)". `flutter test` gave "+142: All tests passed!".

**Other people have uncommitted work in this repo. Leave it alone.** `git status --short` today shows these files modified: `fastlane/metadata/**` (description, promotional text, review notes, 6 screenshots) and `ios/Podfile.lock`. It also shows 2 untracked `04.png` screenshots. None of the files this spec changes has uncommitted edits right now: `lib/`, `test/`, `integration_test/`, `pubspec.yaml`, `assets/`, `ios/Runner/Info.plist`, `ios/Runner/Base.lproj/LaunchScreen.storyboard`, `ios/Runner/Assets.xcassets`, `android/app/src/main/**`. If that changes before you start, stop and report it. Never `git add -A`.

**Because `ios/Podfile.lock` carries someone else's edits, this spec adds no Flutter plugin with native code** (no `url_launcher`, `local_auth`, `flutter_local_notifications` and so on). A new native plugin forces a `pod install` that rewrites that file. All MUST items use only what is already in `pubspec.yaml` (sqflite, share_plus, agl_*) plus pure-Dart code, bundled fonts and images.

---

## 1. Problem

### What the app is today
I read all of `lib/`: `main.dart` 1285 lines, `ui/sheets.dart` 957, `app/finance_controller.dart` 333, `services/finance_repository.dart` 386, `domain/*` 1056, `ui/common.dart`, `money.dart` and `palette.dart` 279, and `i18n/translations.dart` 2135.

| Area | State | Evidence |
|---|---|---|
| Ledger (transactions) | **Real.** Stored in SQLite, add/edit/delete through a sheet, newest first, built lazily. | `services/finance_repository.dart:68-127` (schema v1), `main.dart:915-959`, `ui/sheets.dart:472` |
| Search / filter | **Dead code.** `applyTxFilter` (query, date range, categories, in/out) exists and has tests, but no screen calls it. The Transactions tab is one unfiltered list. | `domain/filters.dart:29-53`; grep of `lib/` for `applyTxFilter` finds only its definition and an import in `finance_controller.dart:14` |
| CSV export | Real. The whole ledger goes through the share sheet. | `main.dart:227-248`, `domain/filters.dart:58-71` |
| Budgets | Real, thin. One monthly limit per category, with a progress bar for this month. No history and no rollover. | `domain/aggregates.dart:89-120`, `main.dart:963-1105` |
| Subscriptions | **Real, but disconnected.** Weekly/monthly/yearly items, a monthly-equivalent total and the next charge date. **A charge never reaches the ledger or the balance**: "Upcoming charges" is a list and nothing more. No income schedule of any kind. | `domain/models.dart:62-123`, `aggregates.dart:136-200`, `main.dart:626-637,1109-1240` |
| Home | Balance card (opening balance + all rows), this month's in/out/net, up to 3 upcoming charges, 5 recent rows. **It only looks back:** nothing tells the user what they can spend or whether a bill will bounce. | `main.dart:586-726` |
| Account | One auto-created "Cash" account. The currency relabels and does not convert. | `finance_repository.dart:132-140`, `ui/sheets.dart:884-957` |
| "Bills Brain" | **Dead code with invented numbers.** It promises a 30% ISP saving, a 15% insurance saving and a "$300/month" plan topped up with a fixed $45. Nothing in `lib/` calls it, but its tests keep it alive. | `domain/bills_brain.dart:139-147,162-169,252-258`; `test/domain_test.dart:183-304` |
| `translations.dart` | **Dead code from another brand ("Finara").** It contains fake copy: "Your food spending is 12% above average… save ~$40/week", "Unlock Full AI Insights", "Go Premium", "Annual · Save 30%", "Welcome to Finara", "Get Started", "AI that works for you". It is imported only by `test/domain_test.dart:5`. | `lib/i18n/translations.dart:1,89-92,113-146` |
| Sample data | Loading sample data was removed on 2026-10-09 (commit `b017ea4`). A banner, a menu row and a "Remove sample data" action are still left for installs that hold old `is_sample` rows. **These are the "Sample data" strings** the diagnosis found. | `main.dart:256-264,332-345,562-582,620-623`, `finance_repository.dart:358-381` |
| Privacy choices | **Region-conditional.** The row renders only when UMP says it is required. The listing tells everyone to go to "More options > Privacy choices", but a US reviewer never sees that row. | `main.dart:346-365`; `store/apps/MyFinance.json` description, ADS paragraph |
| In-app privacy policy | **None.** No link and no text in `lib/`. The page exists: `curl -L https://www.americangroup.ai/policy/myfinance/` returned `200` today. | grep of `lib/` for `http`/`privacy policy` finds only the dead `translations.dart:103` |
| Identity | **Template.** `class C` palette that calls itself "Robinhood × Revolut × Stripe — dark premium finance UI" (`ui/palette.dart:3-5`). It uses neon green `00C805`, Stripe violet `635BFF` and Tailwind cyan-500 `06B6D4` (`:13,17,22`). The theme is dark-only `fromSeed(violet)` (`main.dart:154-162`). System font. A hand-rolled four-emoji tab bar 🏠💳📊🔁 (`main.dart:110-115,1242-1284`) with `AglAdBanner` directly above it in the shell (`:386`). Generated icon `savings` on #1B5E20→#66BB6A (`agl-manifest/scripts/generate_app_icons.py:73`). Shared splash (`LaunchScreen.storyboard` sha1 `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, re-measured today). Home-screen name `Myfinance` (`ios/Runner/Info.plist:10`), `CFBundleName` `myfinance` (`:18`), Android `android:label="myfinance"` (`AndroidManifest.xml:3`), and pubspec description "A new Flutter project." (`pubspec.yaml:2`). |
| Ads | Shell banner (`main.dart:386`). Interstitial on every tab change (`main.dart:214-218`). `agl_ads` skips the first 2 transitions and then caps at one every 3 minutes (`agl-manifest/packages/agl_ads/lib/src/ads.dart:22,26,145`). |
| Telemetry | No crash reports or analytics are sent. On iOS Firebase is never configured. On Android it is started only to switch Crashlytics off and delete queued reports (`main.dart:55-87`, `Info.plist:284-292`). |
| Network | Only Google AdMob/UMP. The ledger never leaves the phone. No Supabase and no HTTP client in `pubspec.yaml`. |

### What Apple and Play users see
`fastlane/metadata/android/en-US/images/phoneScreenshots/01.png` **at HEAD** (I extracted it with `git show` and looked at it) is the empty state "Nothing recorded yet" on a black screen with a neon-green button, above the emoji tab bar. The Play feature graphic at HEAD is the **Flutter logo** with the tagline "**Personal finance tracker MVP**" (I extracted and looked at that too). Someone else's uncommitted re-capture is in the working tree. I did not use it or judge it.

### Why Apple sees a template
1. **4.3(b): "indistinguishable from what's already widely available."** A manual ledger with category budgets and a subscription list is what Money Manager (Realbyte, id560481810, 19,488 ratings), Spendee (id635861140) and Bobby (id1059152023) already do, and MyFinance does less than each. Nothing on screen answers a question those apps don't.
2. **4.2.6: the scaffold look.** It has the portfolio-wide tells: `class C`, dark plus neon, an emoji tab bar with an ad banner above it, the generated glyph icon, the shared splash, a flutter-create display name, stock Material on iPhone, a Flutter-logo feature graphic and "MVP" in the tagline.
3. **The words don't match the binary.** The 2026-09-29 Resolution Center reply said "calls no external service", while the notes list AdMob. The notes list "Firebase Crashlytics — crash reporting", but the code sends none. The notes claim "follows the device language for 12 locales", but the app declares English only (`main.dart:135`, and `test/release_sanity_test.dart:222` asserts it). "Intended audience: Offline budget and ledger" is the subtitle pasted in.

## 2. User and product decision

**User:** someone paid on a fixed rhythm (weekly, every two weeks or monthly) whose rent, phone, card minimums and subscriptions come out between paydays. They will not give a finance app their bank login, for privacy reasons or because their bank isn't supported, or because much of their money is cash. Every few days they ask: *how much can I actually spend until I'm paid, without a bill bouncing?*

**Core job (one, done well):** keep an honest hand-entered ledger and a list of what comes in and goes out on a schedule. From those, the app answers "what's free until payday" and keeps the balance true **without retyping recurring items**.

**Signature feature: "Until Payday". A ledger-backed runway with a confirm queue.**
1. **Income schedules.** Recurring money *in* (name, amount, next date, repeat: weekly · every 2 weeks · monthly · yearly), next to the existing recurring money *out*. Recurring outflows split into **Bills** and **Subscriptions** for display. They use the same model.
2. **The runway** (pure Dart, `lib/domain/runway.dart`). The window runs from today to the day before the next income date. With no active income schedule it is the next 30 days, labelled as such. The start is the current balance (`totalBalance`). Events are every active scheduled occurrence in the window, plus any past-due occurrence the user has **not yet confirmed**, which is counted as due today and labelled "not confirmed yet". The engine walks the days and records the running balance after each day's events.
   - **Lowest point** = the minimum running balance, with its date and the item that causes it.
   - **Free until payday** = `max(0, lowestPoint − safetyBuffer)`. This is the most the user can spend today without the lowest point dropping below their buffer. It is right even when a second income lands mid-window.
   - **A day** = free ÷ days left in the window (at least 1), rounded down to the currency's minor unit.
   - **Short** = when `lowestPoint < safetyBuffer`: "Short by X on <date>, after <item>", and a day shows 0.
   - The safety buffer is set by the user. It defaults to 0. It is never a suggested figure.
3. **"Did these happen?" The confirm queue.** Every scheduled occurrence whose date is today or earlier and has no resolution appears at the top of the home screen. There are three actions:
   - **Paid** posts a ledger transaction (signed, category from the schedule, date = due date, note "From Plan") and records the resolution.
   - **Different amount** posts the real amount. For a subscription or bill it then asks "Use <new> from now on?" If yes, the schedule's amount is updated and a **price change** row is saved (date, old, new). The item's detail screen shows its price history, e.g. "Streaming: 15.49 → 17.99 on 3 Oct 2026", plus its cost per year at the current price.
   - **Didn't happen** records it as skipped.

   Resolutions are keyed by (schedule, due date), so an occurrence can never be posted twice. Deleting the posted transaction re-opens the occurrence. The queue starts at the later of the schedule's anchor date and its `created_at`, so an old schedule never floods the queue with backlog.
4. **Every number is the user's own.** No averages, no "people like you", no savings estimates, no tips.

**Why it is distinct.** I checked these competitors today through the keyless iTunes Search/Lookup API (`itunes.apple.com/lookup?id=…&country=us`). What follows is from their own App Store descriptions, not hands-on tests. WebSearch is disabled in this session, so nothing beyond those descriptions was checked.
- **PocketGuard** (id949414211, 4.6★ / 7,677): "know what's safe to spend". Its description is built on bank connection ("Connect your bank and PocketGuard automatically identifies bills…", via Plaid/Finicity/Salt Edge). It says manual entry is possible. PocketGuard Plus costs $12.99/month or $74.99/year.
- **Foreseenly Cash Flow Forecast** (id965047409, 170 ratings) and **Stay Above** (id6789789322, 1 rating): forecast low points with no bank login, on-device. Neither description mentions a spending ledger, category budgets, or turning a confirmed bill into a ledger entry.
- **Kualto** (id1217021017): forecasts, with "transaction statuses" for paid/due. It has an account accessed "via the app or with a browser" and requires a subscription after a 30-day trial.
- **Money Manager** (Realbyte, id560481810) and **Bobby** (id1059152023): a ledger with budgets, and a subscription list with reminders. Neither description mentions a payday forecast.
- **MyFinance's honest angle** is that one free, account-free, offline app ties the hand-kept ledger, budgets and recurring bills/income into a single "free until payday" answer. The confirm queue turns each scheduled bill into a ledger entry with one tap, and records price changes. I make no claim that no other app does this. The store copy (section 5) describes only what MyFinance does.

**Lane boundaries (MUST NOT):**
- No currency conversion (CalcMaster, NexusTransferPay). The currency stays a label.
- No quotes or markets (ApexMarketWatch, daily-pulse).
- No mileage (MileMaster).
- No home or car "affordability" calculator, and no use of the word "afford" in UI or store copy (HomeWise, CarDeal).
- No bill splitting (CalcMaster).
- No card vault (MyCard).
- GroceryMatch has a single grocery budget screen (`GroceryMatch/lib/features/budget_coach/budget_coach_screen.dart`). This is noted, not a conflict: MyFinance's budgets are per category across the whole ledger.

**Data: 100% on-device** (SQLite). No Supabase, no API, no keys. A bank API would need paid aggregator keys (Charter §3) and would break the product's promise, so it is not used.

---

## 3. Acceptance criteria

### MUST: what Apple needs to see a real, distinct app. Each one is testable.

**M1. Core job end to end on a fresh install (criterion 1).**
1. Onboarding (M5) sets the balance, one income schedule and bills.
2. "Until Payday" shows the real runway.
3. Add a transaction and the runway updates.
4. Advance past a bill's date (widget test with an injected clock) and it appears in "Did these happen?".
5. Tap **Paid** and the ledger gains the row, the balance and runway update, and the queue item disappears.

Every visible control does something. Delete `lib/domain/bills_brain.dart` and `lib/i18n/translations.dart`, because both are dead and full of invented figures. Delete the sample-data banner, menu row, `removeSample`/`hasSampleData` and their strings. A **schema v2 migration** deletes any remaining `is_sample = 1` rows in one SQLite transaction. Those rows were never typed by a user: the app wrote them and labelled them "made-up" on screen (`main.dart:571`). The migration leaves user rows untouched. The `is_sample` columns may stay, unused.

**M2. Signature feature "Until Payday" (criterion 2).** Implement items 1–3 of section 2.
- **Pure Dart, no Flutter imports:** `lib/domain/runway.dart`, `lib/domain/occurrences.dart` (occurrence generation and queue), `lib/domain/price_history.dart`.
- **Schema v2** (`FinanceRepository.schemaVersion = 2`, `onUpgrade` from 1, tested from a real v1 file):
  - `subscriptions`: add `kind TEXT NOT NULL DEFAULT 'subscription'` (`subscription|bill|income`) and `created_at TEXT`. Existing rows get the migration date. Rename the Dart model to `Scheduled`; keep the table name.
  - `BillingPeriod`: add `biweekly`, a 14-day step in `_advance` (`aggregates.dart:136-140`).
  - New table `occurrences(scheduled_id TEXT NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE, due_date TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('paid','skipped')), amount REAL, transaction_id TEXT REFERENCES transactions(id) ON DELETE SET NULL, resolved_at TEXT NOT NULL, PRIMARY KEY (scheduled_id, due_date))`. A paid occurrence whose transaction is deleted (`transaction_id` becomes NULL through `SET NULL`) is re-opened by the controller.
  - New table `price_changes(id TEXT PRIMARY KEY, scheduled_id TEXT NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE, date TEXT NOT NULL, old_amount REAL NOT NULL, new_amount REAL NOT NULL)`.
  - `settings` keys: `safety_buffer`, `onboarding_done`.
- **"Paid" happens in one SQLite transaction** (`FinanceRepository.batch`): insert the transaction and the occurrence together. A failure writes neither.
- **The runway is deterministic.** It takes `today` as a parameter, never `DateTime.now()` inside domain code, and makes no network call.

**M3. Depth (criterion 3).**
- **Persistence:** everything above lives in SQLite and survives a process kill (the existing pattern: write, then re-read).
- **Ledger search / filter:** wire `applyTxFilter` into the Ledger tab:
  - a search field that also matches the note (extend the filter and its test);
  - a month stepper "‹ October 2026 ›" plus "All time";
  - chips for In · Out · All and a category multi-select;
  - a running line "23 entries · −412.80" for the filtered set.
- **Export:** "Export these entries" exports the **filtered** set as CSV. The existing "Export all" stays. Add an `account` and `currency` column to the CSV (extend `transactionsToCSV` and its test). Add **"Share runway"**: a plain-text summary through `share_plus` ("Until Fri 24 Oct: 516.00 free after bills · lowest 140.00 on 21 Oct after Rent…"). It contains only the user's own figures.
- **Plan tab:** sections Income · Bills · Subscriptions · Budgets, each with an add button. Bills + Subscriptions show "per month" and "per year" totals (`monthlyCost × 12`). Tapping a schedule opens its detail: next 3 dates, price history, Pause, Delete.
- **States:**
  - **Fresh install:** onboarding (M5).
  - **No income schedule:** the runway runs 30 days and says "Add when money comes in to see your runway to payday" with one button.
  - **No scheduled outflows:** "Nothing scheduled before payday."
  - **Short:** red-ink banner.
  - **Empty queue:** the section is hidden. No "all caught up" filler.
  - **Ledger filter with no match:** "No entries match" with "Clear filters".
  - **DB open failure:** the existing error, Retry and Erase (`main.dart:517-539`) stay.
  - **Stale read:** the existing banner (`main.dart:543-560`) stays.
  - **Share failure:** a snackbar.
  - **Offline:** the app makes no network calls for its job, so it has no offline state. Say so in a code comment, not on screen.

**M4. Own identity, not the shared scaffold (criterion 4).** The concept is an accountant's columnar pad: pale green ruled paper, navy and blue ink, red ink for shortfalls. Use these values exactly.
- **Palette.** Light is the default and follows the system; dark is the alternative. Build explicit `ColorScheme`s, not `fromSeed`.

  | Token | Light | Dark |
  |---|---|---|
  | Paper (background) | `#EAF1E6` | `#101815` |
  | Sheet (surface) | `#F9FBF6` | `#19231F` |
  | Ink (text) | `#1C2833` | `#E6EDE4` |
  | Pencil (secondary text) | `#51606B` | `#A9B5AE` |
  | Rule (lines) | `#C3D5BA` | `#2A3832` |
  | Blue ink (primary) | `#1F4E9C` | `#93B4F2` |
  | Red ink (short / over budget) | `#A5302A` | `#F2877D` |
  | Money in | `#2D6A3E` | `#8DCC9C` |
  | Caution fill (not-confirmed badge, ink text) | `#F2C14E` | `#F2C14E` |
  | Caution text | `#7F5600` | — |

  Contrast I computed today (WCAG):
  - Light: ink on paper 13.01:1, blue ink on paper 6.93:1, white on blue ink 7.99:1, red ink on sheet 6.60:1, money-in on paper 5.62:1, pencil on paper 5.63:1, ink on caution fill 8.93:1, caution text on sheet 6.23:1.
  - Dark: text on background 15.13:1, blue on surface 7.72:1, red on surface 6.56:1.

  A grep of `*.dart`, `*.md`, `*.yaml` and `*.json` under `/Users/spatchava/agl` found 0 files for every one of these hexes. (`8A5A00` was in TripNest, so I replaced it with `7F5600`.) Nothing neon, no violet, and no Tailwind default.
- **Typography.** Bundle **Literata** (`Literata[opsz,wght].ttf`) for screen titles, the hero "a day" figure and the Balance column, and **Public Sans** (`PublicSans[wght].ttf`) for all other UI. Every amount uses `FontFeature.tabularFigures()`, so columns line up like a ledger.
  - Both are SIL OFL in `github.com/google/fonts` (`ofl/literata`, `ofl/publicsans`). I listed both directories with `gh api` today.
  - I downloaded both TTFs and parsed their GSUB tables: both contain `tnum` and `lnum`.
  - Ship each `OFL.txt` under `assets/fonts/` and register it with `LicenseRegistry`.
  - A grep for "literata" and "public sans/publicsans" across `/Users/spatchava/agl` (`*.dart`, `*.yaml`, `*.md`) found no app or spec using either. Source Serif 4 is taken by the HerJourney spec. IBM Plex, Figtree, Young Serif, Fraunces and others are taken by other specs.
- **Shape language: ledger, not cards.**
  - Lists are **ruled rows** separated by 1 px rule lines, on a sheet with a **4 px** radius.
  - Amounts are right-aligned in a fixed column.
  - Totals sit above an accounting **double rule** (two 1 px lines, 2 px apart).
  - No 12/20 px rounded dark panels, no glass, and no emoji anywhere in the chrome (tabs, headers, rows, empty states). Category markers become small Cupertino or Material glyphs in pencil colour.
- **Home layout: "Until Payday"** (replaces Home):
  1. A large title "Until payday" with "Fri 24 Oct · 12 days" (or "Next 30 days").
  2. The hero "**43.00 a day**" in Literata at 44 pt, with "516.00 free after bills and your 100.00 buffer".
  3. A red-ink "Short by…" block when it applies, with buttons "Open <item>" and "Change buffer".
  4. "Did these happen?" queue rows, each with Paid / Different amount / Didn't happen.
  5. **The runway chart:** a `CustomPainter` step line of the daily balance over the columnar ruling. The buffer is a dashed blue line. The low point is a red-ink dot. Event ticks are tappable. It has a Semantics summary.
  6. A **"Before payday" ledger table** with columns Date · Item · Amount · Balance after. Balance is in red ink when below the buffer.
  7. A compact "This month" line: spent vs total budgets, double-ruled. It opens Plan.

  An **Add** button sits in the nav bar. Navigation has **3 destinations: Until Payday · Ledger · Plan**, with Settings behind a gear in the Until Payday bar.
  - **On iOS:** `CupertinoTabScaffold`/`CupertinoTabBar` with `CupertinoIcons` (`graph_square`, `book`, `repeat`), `CupertinoSliverNavigationBar` large titles, `CupertinoActionSheet` for the queue's "Different amount / Didn't happen", `CupertinoDatePicker` in the sheets, and `CupertinoSwitch`.
  - **On Android:** Material 3 equivalents (`NavigationBar`, `Icons.show_chart` / `menu_book` / `event_repeat`) with the same palette and fonts.
- **Code structure:** split `lib/main.dart` into `lib/app/` (theme, shell, adaptive widgets) and `lib/features/payday|ledger|plan|onboarding|settings/`. **Delete `lib/ui/palette.dart`. No `class C`.**
- **Onboarding (first run only, skipped when the ledger is not empty), 3 steps:**
  1. "What's in your account right now?" Amount, currency (prefilled from locale, as today) and account name (default "Everyday").
  2. "When does money next come in?" Name, amount, date and repeat. The text button reads "I don't have a regular income".
  3. "What has to be paid before then?" Name chips: Rent · Phone · Internet · Electricity · Insurance · Streaming · Gym · Loan · Something else. Tapping one opens amount + date + repeat. **No amounts are prefilled.**

  The primary button "Show my runway" goes home. Do not use "Welcome", "Get started" or marketing copy.
- **Settings (own copy):**
  - Account & currency (the existing sheet)
  - Safety buffer
  - Export all entries (CSV)
  - Erase everything on this phone, with confirmation (reuse `eraseAndRestart`)
  - Privacy choices (M6)
  - Privacy policy: shows `https://www.americangroup.ai/policy/myfinance/` with "Copy link" (Flutter `Clipboard`) and "Share link" (`share_plus`). There is no url_launcher; see the native-plugin note above.
  - About: version, font licences, and "Your ledger is stored only in this phone's app storage."

  The shared `AglLanguageScreen` is **not** added: the app is English-only.

**M5. Remove this app's template tells (criterion 4).**
- **New icon, not from the generator.** A flat navy `#1C2833` square holding a pale-green `#EAF1E6` ledger sheet. The sheet has three vertical `#C3D5BA` rules and a blue-ink `#1F4E9C` step line that dips and recovers, with one red-ink `#A5302A` dot at the low point.
  - Draw it as vector geometry: no Material glyph, no gradient.
  - Regenerate every size in `ios/Runner/Assets.xcassets/AppIcon.appiconset` and every `android/app/src/main/res/mipmap-*`, plus the adaptive foreground and background.
  - Delete the `"MyFinance"` entry at `agl-manifest/scripts/generate_app_icons.py:73` so a re-run cannot overwrite it. (`scripts/` is not on the do-not-edit list. Commit it separately in agl-manifest.)
- **Own launch screen.** `LaunchScreen.storyboard` with background `#EAF1E6` and the sheet mark, plus a new `LaunchImage`. Its sha1 must differ from `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`.
- **Names.** `CFBundleDisplayName` and `CFBundleName` (`Info.plist:10,18`) and `android:label` (`AndroidManifest.xml:3`) must equal the store name decided in founder question 1. If there is no decision, use `iMyFinance`, so device and store match (2.3.8). `MaterialApp.title` follows. Replace the `pubspec.yaml` description with a real one and delete the flutter-create comment boilerplate.
- **Colours and theme.** No `00C805`, `635BFF`, `FF5000`, `F5A623` or Tailwind defaults (`06B6D4 F59E0B 10B981 EF4444 3B82F6 8B5CF6 EC4899`) in `lib/`. No dark-only theme.
- **Ad slot out of the shell.** `AglAdBanner` no longer sits between content and the tab bar. One banner goes in a separated, labelled ("Advertisement") row at the end of the Ledger list and at the end of the Plan list. It never appears on Until Payday, onboarding, the queue or any sheet. The final placement waits on founder question 2.

**M6. Honest, and nothing that could read as hidden (criterion 5, Apple 5.6).**
- **Real data only:** what the user typed and what was derived from it. No sample rows, invented savings, averages, tips or "AI". The existing test `no screen offers to load a made-up ledger` (`test/widget_test.dart:150`) stays and extends to the new screens. It must also ban "AI", "premium", "save up to", "average" and "%".
- **Privacy choices is always visible** in Settings. Where UMP requires it, it opens Google's form (`AglConsent.showPrivacyOptions`). Elsewhere it opens a short sheet that says, in wording checked against what `packages/agl_ads` actually does, that ads come from Google AdMob and that no consent form applies in this region. The two tests asserting the row is *hidden* or *offered only where required* (`test/widget_test.dart:217,226`) are **replaced** by tests asserting it is present in both consent states. Say in the commit message that this is an intended behaviour change.
- **Interstitial.** Remove the tab-change interstitial (`main.dart:214-218`). Pending founder question 2, either there is none, or there is one only after "Paid" in the queue. If there is one, set `AglAds.warmupTransitions = 0` in MyFinance's `main()` (`ads.dart:26` is a public static), so a reviewer sees what a user sees. The store copy and notes must describe the final behaviour exactly.
- **No hidden behaviour.** No demo login, no remote switches, no hidden gestures, no long-press-only actions, no debug menu. Every feature is within 2 taps of Until Payday. Add a test that greps `lib/` for `RemoteConfig`, `AglInsights`, `Platform.localeName`, `kReleaseMode`/`kDebugMode` feature branches and date-gated `DateTime(20` literals, and fails on any hit outside an allow-list.
- **Positive copy.** Copy says what the app does in positive terms. One plain line about having no bank connection is fine. Disclaimer paragraphs are not.

**M7. Proven (criterion 6).** `flutter analyze` clean. Every test passes. No test skipped.

**Removed or replaced tests, all named in the commit message:**
- the `bills brain` groups (`test/domain_test.dart:183-304`): the module is deleted;
- the `i18n` group for `translations.dart` (`:306-356`): the module is deleted;
- `sample rows left by an older version are labelled and removable` (`test/widget_test.dart:175`): replaced by a migration test;
- the two Privacy-choices tests (M6).

**New tests, at least:**
- `test/runway_test.dart`:
  - window ends the day before the next income; 30 days with no income;
  - a weekly, a biweekly and a monthly income, including 31 Jan → 28/29 Feb;
  - lowest point, its date and item;
  - free = lowest − buffer, floored at 0;
  - "a day" divides by days left and rounds down;
  - a mid-window second income does not inflate "free" beyond the lowest point;
  - unconfirmed past-due items count as due today;
  - paused schedules are ignored.
- `test/occurrences_test.dart`:
  - the queue starts at max(anchor, created_at);
  - Paid writes the transaction and occurrence atomically (inject a failure and assert neither row exists);
  - a second Paid for the same (schedule, date) is impossible;
  - deleting the posted transaction re-opens it;
  - "Didn't happen" removes it from the queue and the runway;
  - "Different amount" records a price change only when the user accepts.
- `test/migration_test.dart`: build a real v1 file with the v1 schema (user rows plus `is_sample` rows), open it with v2, and assert that user rows survive, sample rows are gone, new columns and tables exist, and `created_at` is set.
- Filter tests: note search, month stepper bounds, the filtered-CSV export, and the new CSV columns.
- Widget tests:
  - onboarding shows once, writes balance, income and bills, and is skipped for a non-empty ledger;
  - Until Payday shows the computed day figure and the "Short by" banner for a fixture;
  - queue Paid updates the ledger and the runway;
  - Ledger search, chips and month work;
  - the Plan per-month and per-year totals;
  - schedule detail shows price history;
  - Share runway hands the expected text to an injected sharer;
  - Privacy policy Copy link puts the URL on the clipboard.
- `test/identity_test.dart`:
  - no `class C` and no `ui/palette.dart`;
  - none of the banned hexes;
  - Literata and Public Sans are declared in `pubspec.yaml` and present on disk;
  - light and dark themes are defined;
  - the LaunchScreen sha1 differs from the shared one;
  - display name == store name;
  - no `AglAdBanner` in the shell above the tab bar;
  - no emoji code points in `lib/features/**` and `lib/app/**`.
- `integration_test/store_screenshots_test.dart`: update it to go through onboarding (real dates relative to today), add a few transactions, advance the injected clock in a test-only seam, or create a bill dated yesterday, so the queue appears. Tap Paid, then capture the 5 screens in section 5.

**Launch it and look at it.** Build for the iOS simulator (iPhone and iPad) and the Android emulator. Screenshot onboarding, Until Payday (normal and Short), the queue, Ledger with a filter, Plan and Settings, in light and dark. Green tests do not prove the screens render.

**Commit path-limited:** `git add lib test integration_test pubspec.yaml pubspec.lock assets ios/Runner/Info.plist ios/Runner/Base.lproj ios/Runner/Assets.xcassets android/app/src/main`. Never `fastlane/` or `ios/Podfile.lock`. Push to `main`. If `pubspec.lock` changes only for fonts/assets, that is expected. If it gains a native plugin, stop: see the note at the top.

**M8. Store impact written down (criterion 7):** section 5. store-compliance applies it. The office does not submit (5.6 freeze, MA-043).

### SHOULD (valuable, not required for resubmission)
- **S1. Planned one-offs.** A dated one-time expense or income (e.g. "car service, 240, 18 Oct") that appears in the runway and joins the queue on its date.
- **S2. Twice-a-month pay** (1st and 15th, or two fixed days) as a repeat option.
- **S3. Reserve remaining budgets** toggle: the runway subtracts this month's unspent budget for chosen categories.
- **S4. Full backup and restore** as a JSON file through the share sheet and a file import. A file import may need a picker plugin, so it waits until the Podfile.lock owner is done.
- **S5. App lock with Face ID / fingerprint** (`local_auth`) and **bill-due notifications** (`flutter_local_notifications`). Both are native plugins and wait for the same reason.
- **S6.** Translate, and only then declare more locales.

---

## 4. Data source
- **Everything:** the on-device SQLite file `myfinance.db`. That covers accounts, transactions, schedules (income/bills/subscriptions), occurrences, price changes, budgets and settings. It is never uploaded and is deleted with the app or by "Erase everything".
- **No Supabase, no public API, no keys.** Bank aggregation was rejected: it needs paid keys (Charter §3) and contradicts the product.
- **Off-device, unchanged:** Google AdMob and UMP consent only. The Firebase SDKs stay linked (removing them would rewrite `ios/Podfile.lock`). They are not started on iOS, and on Android they are started only to switch Crashlytics off (`main.dart:68-87`). **Not verified by traffic capture in this session.** store-compliance should confirm with a proxy before changing the privacy label (section 5).

## 5. Store impact (proposals only; I edited nothing under `store/apps/`, `fastlane/` or `docs/`)

**Name:** founder question 1. If unchanged, the store keeps "iMyFinance" and the home-screen name becomes `iMyFinance` (M5).
**Subtitle (≤30):** "What's free until payday" (24).
**Promotional text (≤170):** "Enter your balance, your pay day and your bills. See what's free to spend each day until you're paid, and confirm each bill with one tap. No bank login." (149)
**Play short description (≤80):** "Hand-kept ledger that shows what's free to spend until payday. No bank login." (77)
**Keywords (≤100):** `payday,bills,budget,ledger,spending,cash flow,subscriptions,expense tracker,offline,no bank,runway` (98)

**Description (proposed).** It does not open with the app name, uses no ALL-CAPS section skeleton, and does not repeat the portfolio's shared ads paragraph word for word.
> Rent goes out on the 1st, your phone on the 8th, and you're paid on the 15th. How much of what's in your account is actually yours to spend?
>
> Tell the app your balance, when money comes in and what has to be paid. It walks every day until your next payday and shows the lowest your balance will reach, what's free after your bills and the safety buffer you choose, and what that comes to per day. If a bill would take you below your buffer, it tells you which one and when.
>
> When a bill's date comes round, it asks "Did this happen?". Tap Paid and it goes into your ledger. If the amount changed, record the new amount and keep a price history for that subscription.
>
> Your ledger is yours to search by word, month, category and money in or out, and to export as a CSV file. Set monthly limits per category and see how this month is going.
>
> Everything is typed by you and stored only on this phone. There is no bank connection, no sign-up and no sync. The interface is in English; amounts and dates follow your phone's region.
>
> Ads are provided by Google AdMob and appear at the end of the Ledger and Plan lists. [Interstitial sentence only if founder question 2 keeps one.] Where Google needs your consent (for example in the EEA and UK) you are asked first. Settings › Privacy choices is always there. Your ledger is never sent to Google or anyone else.

**Screenshots to retake (iPhone 6.9", iPad 13", Play phone and tablet), from `integration_test/store_screenshots_test.dart`:**
1. Until Payday: "43.00 a day", the runway chart with its low point, and the "Before payday" table.
2. "Did these happen?" with Rent and a subscription, Paid being tapped.
3. Price history on a subscription after "Different amount".
4. Ledger filtered to a month and a category, with the running total.
5. Plan: Income, Bills, Subscriptions (per month and per year) and Budgets.

All of these use rows typed through the UI in the test. No empty-state screenshot goes first.

**Play feature graphic:** replace the Flutter-logo "Personal finance tracker MVP" graphic. Show the new icon mark on `#EAF1E6`, the runway step line across the graphic, and the line "What's free until payday" in Literata. Do not use the shared generated layout.

**Review notes (replace the shared skeleton; write as prose, not the numbered "2. DEVICES…" headings):**
- **What it does and for whom.** Say it in a paragraph: a person paid weekly, fortnightly or monthly, who keeps their money by hand and won't link a bank, sees what's free to spend until the next payday, and confirms each scheduled bill into the ledger. Do not paste the subtitle.
- **How to see the main feature in under a minute.** First run asks 3 questions. Enter a balance of 800, pay of 1,200 in 10 days and Rent of 650 due tomorrow, and the home screen shows the runway. To see the confirm queue, add a bill dated yesterday in Plan.
- **External services:** Google AdMob and UMP only. Firebase SDKs are linked from an earlier build. The app does not start Firebase on iOS. On Android it starts it only to switch crash collection off and delete unsent reports. No analytics and no crash reports are sent. (This corrects the 09-29 reply, which said "calls no external service", and the current notes, which list Crashlytics crash reporting.)
- **Regional differences:** English interface in every region. Only the Google consent form depends on region, and Settings › Privacy choices is visible everywhere. (This corrects the "12 locales" claim.)
- **Devices:** state only what was actually run on physical devices. Do not reuse the "simulators… a build that cannot start never ships" sentence.
- **Account:** none is created. "Erase everything on this phone" in Settings deletes all data.
- **Differentiation answers for a 4.3 reply** (founder sends; Charter §1): use section 2. For Apple's question 6, it is not a feature of ApexMarketWatch (market data), HomeWise (mortgage maths), NexusTransferPay (exchange rates) or MyCard (card vault), because none of them holds a personal ledger.

**Privacy label (`store/privacy/MyFinance.json`):** today it is the 4-app shared label (sha prefix `09336fbd27`, identical for ApexMarketWatch, CarDeal, GadgetNest and MyFinance) and declares `CRASH_DATA` for app functionality. The code sends no crash data (section 4). Proposal: remove `CRASH_DATA`, keep `DEVICE_ID` and `ADVERTISING_DATA` (third-party advertising, not linked), **after** a proxy capture confirms that no Crashlytics endpoint is contacted.

### 5a. What the build actually does, for store-compliance (software-developer, 2026-10-13)

Added after implementation. It corrects or completes the proposals above where the code settled a detail. Nothing under `store/`, `fastlane/` or `docs/` was edited.

- **Interstitial: none.** The tab-change interstitial was removed, and no interstitial was added anywhere (`test/honesty_test.dart` fails on `AglAds.onTransition`, `InterstitialAd` or `warmupTransitions` in `lib/`). In the proposed description, delete the bracketed "[Interstitial sentence only if...]". Founder question 2 is still open. If the founder wants one after "Paid", it is a code change plus a copy change.
- **Banner placement:** one row labelled "Advertisement" at the end of the Ledger list and at the end of the Plan list (`lib/app/widgets.dart` `AdvertisementRow`). There is none on Until Payday, onboarding, the queue, Settings or any sheet, and none in the shell.
- **Home-screen name:** `iMyFinance` (`CFBundleDisplayName`, `CFBundleName`, `android:label`, `MaterialApp.title`), so device and store match while founder question 1 is open.
- **Where Privacy choices lives:** Settings, behind the gear on Until Payday, then Privacy choices. It is visible in every region. Where UMP requires a form, it opens Google's form; elsewhere it explains that no form applies. The listing's path should read "Settings (gear on Until Payday) > Privacy choices", not "More options > Privacy choices".
- **Privacy policy in the app:** Settings > Privacy policy shows `https://www.americangroup.ai/policy/myfinance/` with Copy link and Share link.
- **Review notes, "see the main feature in under a minute":** the confirm queue asks about any scheduled date from the day before an item was added, onward. A reviewer can therefore add a bill dated **today** (or yesterday) in question 3 or in Plan and see "Did these happen?" at once. Replace "add a bill dated yesterday in Plan" with "add a bill dated today or yesterday (in the first-run questions or in Plan)". A bill dated further back is not asked about, because the balance the user typed already includes it.
- **"Different amount":** both questions come before anything is written (the real amount, then "Use X from now on?"). The price history records a change only when the user accepts. Editing a bill's or subscription's amount in Plan also records a change, dated that day.
- **Screenshots:** `integration_test/store_screenshots_test.dart` writes `01_until_payday`, `02_did_these_happen`, `03_price_history`, `04_ledger` (filtered to Food & Dining in the current month) and `05_plan` into `store_screenshots/`. Every row in them is typed through the UI by the test on a fresh install. Retake them on iPhone 6.9", iPad 13" and Play phone/tablet with `--dart-define=SCREENSHOT=true`, so no test ad appears.
- **Languages:** English only (`supportedLocales: [Locale('en')]`, one `CFBundleLocalizations` entry). Dates and amounts follow the phone's region.

## 6. Out of scope
- Bank connections, CSV/OFX statement import, receipts/OCR, multi-device sync, sharing a budget with a partner, investments and net worth, debt payoff planning, currency conversion and any "AI".
- Adding any native plugin while `ios/Podfile.lock` holds someone else's uncommitted edits (S4, S5).
- Editing `store/apps/MyFinance.json`, `fastlane/`, `store/privacy/` or `docs/`. store-compliance applies section 5.
- Submitting, replying to Apple, Beta App Review, or promoting on Play (Charter §1, MA-043).

## 7. Founder questions
1. **Name.** Keep "iMyFinance" (the 'i' prefix was a 409 workaround, and overlap.md lists it as a suite tell)? Or rename to a name that says the job? An example to try in App Store Connect is "Columnar: Ledger to Payday". A US iTunes search today returned no app named "Columnar", but only App Store Connect can confirm availability. The home-screen name follows the choice.
2. **Ads.** Remove the interstitial entirely, or keep one only after "Paid" with no warm-up? Is a single end-of-list banner on Ledger and Plan acceptable? This changes ad revenue (Charter §3).
3. **Privacy label.** Approve removing `CRASH_DATA` once store-compliance's proxy capture confirms no crash reporting.
4. **Beta evidence for Apple's question 4.** TestFlight records 0 feedback items for this app (`store/apps/MyFinance.json` differentiation §4). Do you want an external TestFlight round before resubmitting? It needs a Beta App Review submission, which falls under the 5.6 freeze.
