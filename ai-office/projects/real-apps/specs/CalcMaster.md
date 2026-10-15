# Spec: CalcMaster — a calculator that works on ruled sheets, with each currency line priced at the ECB rate for its own date

Author: product-manager (AI office), 2026-10-12
Project: real-apps (`../plan.md`, criteria 1–7). Overlap: `../overlap.md` G3 (line 35) and G4 (line 36).
Repo: `/Users/spatchava/agl/CalcMaster`
Base: `main` @ `24efa5c4696ff1b762b530c675291beea6dec0d9` (`git rev-parse HEAD` and `git branch --show-current`, both run 2026-10-12)
Baseline on that base, run 2026-10-12 with `/Users/spatchava/agl/.flutter-sdk/bin/flutter`:
- `flutter analyze` → "No issues found! (ran in 30.5s)".
- `flutter test` → "+342 ~1: All tests passed!". The one skip is `test/design_render_test.dart`, which is tagged `design` ("Render-only; run with --run-skipped --update-goldens --tags design").
- `git status --short` was the same before and after both runs (diffed), so the runs changed no files.

**Other people's uncommitted work is in this repo. Do not touch it.** `git status --short` shows edits under `fastlane/**`: descriptions, notes.txt, every screenshot, and `04.png`/`05.png` deleted, plus untracked new screenshots. It also shows **`ios/Runner.xcodeproj/project.pbxproj`** as modified. Do not stage, revert or overwrite any of those files:
- Commit by path (`git add lib test assets pubspec.yaml pubspec.lock ios/Podfile.lock ios/Runner/Assets.xcassets ios/Runner/Base.lproj android/app/src/main/res …`). Never use `git add -A` or `git commit -a`.
- Adding `share_plus` (M4) makes CocoaPods rewrite `ios/Podfile.lock`. That file is clean today, so it may be committed. If `pod install` also touches `project.pbxproj`, leave `project.pbxproj` uncommitted and report it.
- Do not run `dart format`.

---

## 1. Problem

### Store state
- **Apple** rejected version 4.0.2 under **4.3(a), 4.3(b) and 4.2.6** (`/Users/spatchava/agl/.dist/rejections.json` → "CalcMaster", message 0). The batch was the identical 26-app message.
- An earlier review of 4.0.2 (4) on 2026-08-21 (message 2) added three issues:
  - **2.1:** the ATT prompt was not found.
  - **2.1(b):** "one or more of the In-App Purchase products have not been submitted for review".
  - **3.1.2(c):** no functional Terms of Use (EULA) link in the metadata.
- **Google Play:** LIVE_PRODUCTION. This spec ships to existing Play users, so the data migration in M1 matters.

### What Apple was told, and what is true
Our reply (message 1) opened: "CalcMaster is the only calculator you need on your phone. One polished app, ten unit categories, five calculator modes, seven finance tools, eight engineering utilities, and a notes pad". The "WHO IT IS FOR" line was the subtitle: "World calculator & converter". The reply also said "The app opens on a sign-in screen". The code says otherwise: `splash_screen.dart:105-110` goes to `/calculate`, and the current notes say "it does not open on a sign-in screen".

### What the app is today (read 2026-10-12)
**A grab-bag of 30 tools across five tabs.**
- `lib/app_router.dart:31-127`, `widgets/tab_scaffold.dart:44-50` define the tabs:
  - **Convert:** 10 unit categories (`lib_units.dart:74+`).
  - **Calculate:** Standard, Scientific, Percentage, Base, Fraction.
  - **Finance:** Tax, Paycheck, Tip & Split, Discount, Compound, EMI, Currency, Unit price.
  - **Tools:** GPS, Ohm, BMI, Date diff, Time zones, ADC/DAC, Age, Aspect ratio, Calendar.
  - **Notes.**
- The maths is real and tested: `lib_calc.dart` is a shunting-yard evaluator, and there are `lib_tax.dart`, `lib_payroll.dart` and `lib_units.dart`, with 342 passing tests.
- **What is missing is a product.** Each tool forgets its result the moment you leave it. A grep of `lib/` for `history` finds none outside the currency cache. Nothing can be shared or exported; the only Clipboard use is copying a single result row (`widgets/result_row.dart:48`). Notes are a separate free-text pad (`state/notes_provider.dart`) that is not linked to any calculation.

**Indistinguishable from what's widely available (4.3(b)).** Checked through the keyless iTunes Search/Lookup API on 2026-10-12 (descriptions only):
- **Calculator₊** (id398129933, 1,733,611 ratings) lists standard, scientific, history, units, percentage, currency "with the latest exchange rates" and fractions. That is CalcMaster's scope.
- **OneCalc: All-in-one Calculator** (id1324977193, 5,098 ratings) has "over 40+ calculators and unit converters".
- On top of that, CalcMaster's Standard calculator copies the iOS Calculator's look: `theme/tokens.dart:4` says "Near-black canvas in the spirit of the iOS Calculator", and `KeyColors` (`tokens.dart:26`) says "iOS Calculator layout: gray functions, darker digits, amber operators".

**Duplicates inside our own account (4.3(a)).** Store screenshot 01 and the Finance → Currency screen are the same ECB converter that NexusTransferPay opens on (`overlap.md:35`, G3). Both call `api.frankfurter.dev/v1` (`lib_currency.dart:159`).

**Template tells in this app (evidence):**

| Tell | Evidence |
|---|---|
| Supabase sign-in family on a calculator | `screens/auth/login_screen.dart` (489 lines): "Continue with Google" (`:368`), "Continue with Apple", "Welcome Back" (`:218`), `authTwoFactor`/`authOtpHint`. Also `state/auth_provider.dart` with an "offline demo session" (`:44-64`, `:346-357`), `services/auth_service.dart`, `services/supabase_config.dart`, `app_env.dart`. **The account does nothing in this app.** The only Supabase calls are auth and `rpc('delete_user')` (`auth_provider.dart:375`). Store review info uses the shared demo login `qa@americangroup.ai`. |
| Paywall copy and a dead subscription message | `app_en.arb:85-100`: "BEST VALUE", "Ad-free experience", "Priority email support", and `paywallSubscriptionsDisabled` "Subscriptions are not yet enabled in this build." (`:97`, reachable from `paywall_screen.dart:35-38`). RevenueCat keys are `'appl_DUMMY_REPLACE_BEFORE_LAUNCH'` (`monetization/monetization_config.dart:100-103`). Apple's 2.1(b) and 3.1.2(c) are both about this paywall. |
| Icon | The bundled icon is **a white swap-arrows glyph on a violet→sky diagonal gradient**: `ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png` and `android/.../mipmap-xxxhdpi/ic_launcher.png`, both viewed. It is the portfolio's glyph-on-gradient formula, and it is not a calculator. The repo also holds a different, unused calculator icon (`assets/icon/app_icon.png`, viewed; shasum differs from the bundled one). |
| Launch screen | `ios/Runner/Base.lproj/LaunchScreen.storyboard:22` sets a white background (`red="1" green="1" blue="1"`) with a centred `LaunchImage`. This is the shared look, although the shasum `7691c606…` is not the portfolio-wide `3f6a9b27…`. |
| Animated splash that imitates Apple naming | `screens/splash_screen.dart:12-15,34-43` shows a 2.2-second "i" morphing into "Calculator" on iOS, and "a" on Android. |
| Near-black + neon look and stock furniture | Animated gradient + particle grid "for the futuristic look" (`tab_scaffold.dart:76`), `glass_card.dart`, `glow_text.dart`. Inter via `GoogleFonts.interTextTheme` (`main.dart:83`) plus `fontFamily: 'Inter'` (`app_theme.dart:21`). Shell: banner ad directly above the bottom nav (`tab_scaffold.dart:68-74`). |
| Dead code and strings | `screens/diagnostics_screen.dart` has no route (grep `diagnostics_screen` in `lib/` → 0). `widgets/affiliate_cta.dart` is imported nowhere. `widgets/hub_tile.dart` is used only by a test. There are commented-out duplicate classes in `screens/tools/tools_screens.dart:333-388` and `:760-813`. The ARB keys `aiChatHint`/`aiChatTitle`/`aiChatEmpty` remain after the AI chat was removed (commit `90a8946`). AGENTS.md still lists `state/ai_chat_provider.dart`, which no longer exists. |
| A currency that always shows "—" | The region list includes AED (`lib_currency.dart:110-116`), but the ECB does not publish AED. `curl https://api.frankfurter.dev/v1/latest?base=USD&symbols=AED` → HTTP 404 `{"message":"not found"}`. `CurrencyCalc` still offers AED and renders "—" for every row (`finance_screens.dart:808-880`). |
| Store copy | "the only calculator you need", '—— Heading ——' sections, a description that opens with the app name, "Download CalcMaster and replace your stock calculator", and the audience line equal to the subtitle (`store/apps/CalcMaster.json`). |

## 2. User and core job

**User.** Someone who works out real-life sums that **mix currencies, units and dates, and then has to keep or hand over the working**:
- a freelancer billing a client abroad;
- an expat or frequent traveller adding up a trip or filling in an expense claim;
- someone planning a DIY job in feet and metres.

They currently use a calculator plus a currency site plus a notes app, and then retype the numbers.

> "I paid €38.50 for dinner on 14 September and £120 for the hotel on the 15th. What is that in dollars at the rate on those days? And will it still say the same number when I open it next month to file the claim?"

**Core job: work it out on a sheet.**
- A **sheet** is a ruled page of numbered lines. Each line is typed like a note, and its answer appears right-aligned on the same line as you type.
- A line can be any of these:
  - arithmetic, using the existing `lib_calc` evaluator;
  - a reference to another line (`#3`, `prev`);
  - a percentage (`+ 18%`, `18% of #2`);
  - a unit conversion (`12 ft in m`), using `lib_units`;
  - a currency conversion (`38.50 EUR in USD`);
  - a plain heading with no result.
- A pinned footer shows the **total**.
- Sheets are saved automatically, listed, searchable, renamable and duplicable, and they can be shared as text or CSV.

**The 30 existing tools become inputs to the sheet, not separate destinations.** A **Tools** drawer holds them in groups: Money, Measure, Time, Maths, Engineering, Body. Every tool except BMI gets **Add to sheet**, which appends its result to the current sheet as a labelled line (for example `Tip per person: 23.60 USD`). That gives the app one job: you work out a sum, and the tools feed it.

**Signature feature: "Rate on the day".**
- Any currency line can carry a date: `38.50 EUR on 14 Sep in USD` or `120 GBP on 2026-09-15 in USD`.
- The app converts that line at the **European Central Bank reference rate for that date**, using Frankfurter's historical endpoint. Coverage goes back to 1999-01-04; this was verified, see §3.
- Under the result it prints the rate and the date it actually used, e.g. "ECB 1.1551 · 14 Sep 2026". A weekend or holiday date shows the previous working day the ECB published, e.g. "ECB 1.1206 · Fri 9 Oct (no rate on Sat 10 Oct)".
- **Pinned rates.** An undated currency line is pinned to the rate it was first computed with. A sheet therefore shows **the same answer next month**, and the header says "Rates as of 9 Oct 2026 · Re-price". Re-pricing is always an explicit tap. Dated lines never change, because historic ECB rates are fixed.
- **Export carries the evidence.** The shared text and CSV list every currency line with its rate, the rate's date and the attribution "Reference rates: European Central Bank, via Frankfurter". That makes the export usable as working for an expense claim or an invoice note.

**Competitors.** WebSearch is disabled in this session ("Internet mode is not enabled"). On 2026-10-12 I used Apple's keyless iTunes Search/Lookup API and read **store descriptions only**. I did not run these apps.
- **Soulver 4** (id1508732804, Zac Cohan, 430 ratings, one-time purchase). **This is the closest.** It is "a natural-language notepad calculator" with "sheets", "Live currency conversions — 190 currencies", unit and date maths, and "Export to PDF & plain text". **So the sheet-calculator idea itself is not unique**, and neither is export.
- **CalcMate – Notes Calculator** (id6449422062, 96 ratings) offers "500 USD in EUR", "subtotal", "line5" references and folders.
- **Calculator₊** (id398129933) and **OneCalc** (id1324977193) are all-in-one tool collections, CalcMaster's current shape.

**The claimed gap, stated narrowly:**
- (a) **Per-line historical reference rates**: a currency line converted at the ECB rate of the date the user names, with that rate and date printed on the line and in the export.
- (b) **Pinned rates**: a saved sheet does not silently change when it is reopened.

The descriptions of Soulver 4 and CalcMate say "live" or "latest" rates only. A grep of their descriptions for `histor` returns 0. Calculator₊'s two `histor` hits are about calculation history, and OneCalc's one hit is a "history viewer".
- (c) **The tool drawer feeds the sheet**: tax, paycheck, loan, tip-and-split, unit price, and date and age results land as labelled lines. Notepad calculators make you type the formula yourself.

**Competitor behaviour beyond their store descriptions is not verified.** Soulver may support dated rates without saying so.

**Risk stated honestly.** "A notepad calculator" is a known category. What distinguishes the app is (a)+(b)+(c) together and the visual identity in M5, not the category. If Apple judges the category itself as 4.3(b), only the reply can argue this gap. The reply is a founder decision (Q6).

## 3. Data sources (real, keyless; curl-verified 2026-10-12)

| Data | Endpoint | Proof (2026-10-12) |
|---|---|---|
| Latest ECB rates | `https://api.frankfurter.dev/v1/latest?from=USD` (already in code, `lib_currency.dart:159`) | HTTP 200, 436 B, `"date":"2026-10-12"`, 29 quote currencies, e.g. `"EUR":0.89437,"GBP":0.75555,"INR":95.78` |
| Rate on a date | `https://api.frankfurter.dev/v1/{YYYY-MM-DD}?base={CUR}&symbols={CUR}` | `2026-09-14?base=EUR&symbols=USD,GBP` → `{"date":"2026-09-14","rates":{"GBP":0.85598,"USD":1.1551}}` |
| Weekend or holiday date | same | `2026-10-10` (Saturday) `?base=EUR&symbols=USD` → `"date":"2026-10-09"`, `USD 1.1206`. **Always display the returned `date`, not the requested one.** |
| Earliest and future dates | same | `1999-01-04` → 200, `USD 1.1789`. `1998-12-01` → **404** `{"message":"not found"}`. `2030-01-01` → **404** |
| Range (only for S1 history) | `https://api.frankfurter.dev/v1/{from}..{to}?base=USD&symbols=EUR` | `2025-10-01..2026-10-10` → 200, 7,652 B, `end_date` `2026-10-09` |
| Currency list | `https://api.frankfurter.dev/v1/currencies` | 200, **30 codes** (the 29 above plus USD) |
| Unsupported currency | `latest?base=USD&symbols=AED` | **404** `{"message":"not found"}` |
| Sheets, pinned rates, rate cache, settings | on-device, `shared_preferences` (already a dependency) | — |

**Rules the developer must follow:**
- **ECB covers 30 currencies only.** The currency picker and the line parser accept exactly the codes returned by `/v1/currencies`. Bundle a snapshot as a fallback for the first offline launch, and refresh it when online. AED leaves the region currency list's conversion options; the AE region keeps its tip and tax defaults. A line naming an unsupported code shows "The ECB publishes no reference rate for AED". **Never estimate a rate and never use a second rate source.**
- **Cache historic rates forever**, keyed `date|base|quote`, because published ECB rates do not change. Cache `latest` together with its `date`.
- **Offline:**
  - A cached rate shows "(offline · cached ECB rate of 9 Oct)".
  - A dated line whose rate is not cached shows "Needs a connection to get the ECB rate for 14 Sep". The line is **excluded from the total**, and the footer says "Total excludes 1 line".
- **Dates:**
  - A date before 1999-01-04 → "ECB rates start on 4 Jan 1999".
  - A date in the future → "That date is in the future".
  - `14 Sep` with no year means the most recent 14 September that is not in the future.
- `api.frankfurter.dev` is already in the app. No new hosts, no keys, no Supabase and no sign-in. After the build, run `python3 scripts/verify_api_hosts.py --print` from `agl-manifest` and confirm Frankfurter shows `ok` for CalcMaster.
- **Test inputs only** (use a mocked `http.Client`, never live calls in tests):
  - `38.50 EUR on 2026-09-14 in USD` with rate 1.1551 → **44.47 USD**.
  - `100 EUR on 2026-10-10 in USD` → the line uses 2026-10-09, rate 1.1206 → **112.06 USD**, and the caption names Fri 9 Oct.

## 4. Acceptance criteria

### MUST (what Apple has to see to judge this a real, distinct app)

**M1. Sheets: the core job, end to end (criteria 1 and 3).**
- **App start.** Delete `screens/splash_screen.dart` and the `/splash` route. The app opens directly on the **last edited sheet**. On first launch it opens a new empty sheet. There is no sign-in, no carousel and no "Get started".
- **The editor:**
  - Each line has a gutter number, the input, and a right-aligned result. Currency results carry a rate caption.
  - A pinned footer shows the total.
  - An input-accessory row offers `+ − × ÷ ( ) % # in on`.
  - Tapping a result inserts `#n` into the focused line. Long-pressing a result copies it.
- **Line grammar.** Implement it in a pure-Dart `lib/sheet/sheet_engine.dart` with no Flutter imports:
  - text with no number is a heading;
  - `label: expr` puts a label left of the result (the label is the text before the first `": "`);
  - arithmetic uses the existing `evaluate()` (`lib_calc.dart`);
  - `#n` and `prev` reference other lines; a reference to a line that has no result is an error on the referencing line;
  - percentages: `expr + N%`, `expr - N%`, `N% of expr`;
  - `<n> <CUR>` is an amount tagged with a currency, and `<n> <unit>` an amount tagged with a unit;
  - `<n> <unit> in|to <unit>` converts units across every `lib_units` category, with aliases (`m, metre, meter, ft, feet, ', in, inch, ", km, mi, kg, lb, l, gal, °C, C, °F, F`, …). An incompatible pair gives "Can't convert kg to m";
  - `<n> <CUR|€|£|$|¥|₹|₩> [on <date>] in|to <CUR>` converts currency (see M2);
  - `total` sums the results above that carry the footer's tag.
- **Total.** The footer total is in the sheet's main currency or unit: the most common tag, or plain numbers. Lines with another tag and no conversion are excluded, and the footer says so ("Total excludes 2 lines in GBP").
- **Errors.** An error shows in place of the result, in the error colour, with a short reason. It never crashes, and it never shows `NaN` or `Infinity`.
- **Persistence.** Store under a new `sheets_v1` key in `shared_preferences`: `{id, title, createdAt, updatedAt, lines:[{text, pin?:{base,quote,rate,date}}]}`. Results are recomputed on load. Saving is automatic, debounced at about 500 ms, and also happens on app pause.
- **Sheets list.** Newest edit first. **Search** across titles and line text. Rename, duplicate, and delete with an **Undo** snackbar. **Empty state:** "No sheets yet. Start one — every line works out as you type."
- **Notes migration (Play users have data).** On first run, each existing note (`notes` key, `notes_provider.dart:47`) becomes a sheet with the note's title, one line per body line. Then set `notes_migrated_v1`. Leave the old `notes` key untouched for this release. The migration is idempotent. Remove the Notes tab and `NotesScreen`.
- **Acceptance:**
  - A widget test on a fresh install finds the empty-sheet hint and no `LoginScreen`.
  - Typing `12 ft in m` shows `3.6576 m` (to the shown precision).
  - Killing and relaunching (re-pumping with the same prefs) restores the sheet.
  - Migration tests cover 0, 1 and 3 notes, and running twice.

**M2. Signature: Rate on the day (criteria 2 and 5).**
- The currency lines and rules are exactly as in §2 and §3: dated ECB rate, the returned date shown, pinned undated rates, a header with "Rates as of … · Re-price" (an explicit tap), and dated lines that never re-price.
- **Rate client.** One client in `lib/lib_currency.dart` (extend it, do not fork it):
  - `fetchRateOn(date, base, quote)` → `{rate, ecbDate}` or a typed failure (`unsupported`, `beforeEcb`, `future`, `offline`, `http`);
  - an 8-second timeout, as today;
  - a permanent cache for dated rates.
- **The existing Currency tool stays.** It becomes a Money tool with a date field ("Rate on: Today ▾") and **Add to sheet**. Its picker lists only the 30 ECB codes, so the AED "—" rows are gone.
- **Boundary with NexusTransferPay** (record it in the commit message): CalcMaster converts amounts at a reference rate. It does **not** add provider quote checks, fee or exchange-margin breakdowns, a remittance ledger, provider rankings or World Bank cost benchmarks (`specs/NexusTransferPay.md` M5).
- **Acceptance (unit tests with a mocked client):**
  - the two worked examples in §3;
  - weekend → the returned date is shown;
  - AED → `unsupported` with no number shown;
  - 1998-12-01 → `beforeEcb`;
  - a future date → `future`;
  - the second identical dated lookup makes **zero** HTTP calls (cache);
  - offline with no cache → the line is excluded from the total and the footer note appears;
  - a pinned undated line keeps its value after `latest` changes until Re-price is tapped.

**M3. Tools feed the sheet; the five-tab grab-bag goes (criteria 1 and 4).**
- **Navigation.** Replace `StatefulShellRoute` and `TabScaffold` (five tabs plus the banner above the bar) with one stack:
  - **Sheet** (home);
  - **Sheets** list (top-left button);
  - **Tools** drawer (top-right button: a full-height sheet grouped Money · Measure · Time · Maths · Engineering · Body);
  - Settings (from the overflow menu).
- **Bottom bar.** There is **no bottom NavigationBar** on phones. The desktop/foldable rail logic (`tab_scaffold.dart:21-33`) may be kept as a two-pane layout: Sheets list on the left, Sheet on the right.
- **Tool groups.** Every existing tool screen stays and keeps its tests, regrouped:
  - Money: Tip & split, Discount, Sales tax/VAT, Income tax est., Paycheck est., Loan/EMI, Compound, Unit price, Currency;
  - Measure: the 10 unit categories, Aspect ratio;
  - Time: Date difference, Age, World clock, Calendar;
  - Maths: Scientific, Percentage, Base, Fraction;
  - Engineering: Ohm, ADC/DAC, GPS DMS;
  - Body: BMI.
- **Add to sheet.** Each tool except **BMI** gets an **Add to sheet** button. It appends one parseable labelled line to the current sheet, e.g. `Loan payment (250,000 at 6.5%, 30 y): 1,580.17 USD`, and shows "Added to <sheet title>" with Open.
- **BMI stays a calculator.** It gets no Add to sheet, no history and no storage (`overlap.md` G4 guidance).
- **The iOS Calculator clone goes.** Delete the standalone **Standard** calculator screen: the sheet replaces it. **Scientific** stays as a tool, restyled (M5), with its own Add to sheet.
- **Do not add** home-affordability maths (DTI, PMI, HOA; that is HomeWise) or car-buying flows (CarDeal). Loan/EMI stays generic.
- **Acceptance:**
  - Widget tests: from the Tools drawer, Tip & split → Add to sheet appends a line whose result equals the tool's per-person figure.
  - BMI has no Add to sheet button (finder returns nothing).
  - `grep -rn "NavigationBar\|StatefulShellRoute" lib` → 0 hits outside the optional wide-layout rail.

**M4. Share and export (criteria 3 and 5).**
- The sheet overflow menu offers **Share as text** and **Export CSV**, via `share_plus`. If `Podfile.lock` cannot be committed cleanly, the fallback is Copy to clipboard; see the header.
- **Text format:**
  - the title;
  - one line per sheet line: `input  →  result`;
  - currency lines add `(ECB 1.1551, 2026-09-14)`;
  - then the total;
  - then "Reference rates: European Central Bank, via Frankfurter (api.frankfurter.dev). Reference rates are not the rate your bank or card charged."
- **CSV** columns: `line,label,input,result,unit_or_currency,ecb_rate,ecb_date`.
- **Acceptance:** pure-Dart tests on `sheet_export.dart` cover the exact text and CSV for one mixed sheet (a heading, units, a dated EUR line, a pinned GBP line, an error line). An error line exports its error text, never a number.

**M5. Own identity (criterion 4). Concrete values, checked against the portfolio.**
- **Palette "Ledger" (light, the default; `ThemeMode.system`).**
  - Paper `#F4F0E6` (scaffold), rule lines `#D9D2C1`, ink `#22201C`, secondary ink `#6B6457`.
  - Primary / seed **bottle-green `#2C5E4F`**, result figures copper `#9A4A14`, errors `#A8322A`.
  - **"Night ledger" (dark):** background `#161A17`, surface `#1F2420`, ink `#EAE5D7`, primary `#7FB89F`.
  - Contrast (WCAG formula, computed 2026-10-12): ink on paper 14.29, green on paper 6.54, copper on paper 5.49, error on paper 5.85, secondary ink on paper 5.15, white on green 7.44, night ink on night background 13.84, night green on night background 7.75. All ≥ 4.5.
  - Uniqueness: I grepped every `/Users/spatchava/agl/*/lib`, `*/mobile/*/lib` and every spec in `specs/` for these 11 hexes on 2026-10-12. There were 0 hits each. (`#E9E4D6` was dropped for 2 hits; `#B3261E` for 2.)
  - Delete the near-black/amber `AppColors`/`KeyColors`/`CategoryAccent` and every Tailwind or neon value.
- **Typography.** **Golos Text** (`ofl/golostext/GolosText[wght].ttf`, 184,292 B) for all UI. **Reddit Mono** (`ofl/redditmono/RedditMono[wght].ttf`, 203,908 B) for every figure: line input, results, gutter numbers, the total and keypad labels. Use `FontFeature.tabularFigures()`.
  - Both are OFL in github.com/google/fonts. The URLs and sizes were confirmed by `curl` (HTTP 200) on 2026-10-12.
  - Bundle the fonts under `assets/fonts/` with both `OFL.txt` files, declare them in `pubspec.yaml`, and **remove `google_fonts`** and every `Inter` reference.
  - Neither family appears in any portfolio `pubspec.yaml`, any `lib/` or any spec (grep, 2026-10-12). Fragment Mono was rejected because Photriya's spec uses it.
- **Shape and texture.**
  - The sheet is drawn as ruled paper: a `CustomPainter` draws a 1 px `#D9D2C1` rule under every line, with a 1 px left margin rule in green at 40 % opacity beside the gutter.
  - Radii: **4** for buttons and chips, **8** for the top corners of bottom sheets, **0** for sheet rows (the portfolio's most common radius is 12).
  - No cards, glass, glow, gradients or particle backgrounds. Delete `animated_gradient_background.dart`, `particle_dot_grid.dart`, `glass_card.dart`, `glow_text.dart`, `rich_hub_card.dart` and `pill_badge.dart` once unused.
- **Onboarding.** There is no onboarding flow. The empty first sheet shows four grey **placeholder hint lines**, which vanish on typing and are **never saved**: `Dinner: 38.50 EUR on 14 Sep in USD`, `12 ft in m`, `#1 + 18%`, `total`. A one-line link "How lines work" opens a static help page listing the grammar in M1.
- **Settings copy is the app's own.** Sections: Home currency & region; Appearance (System / Ledger / Night ledger); Language (the shared `AglLanguageScreen` may stay); Rates ("Reference rates from the European Central Bank. Cached rates: N · Clear cache"); Help; Privacy policy; Privacy choices (only when UMP requires it); About.
- **Icon.** A new vector, generated by the repo's `tools/gen_icon.dart`:
  - a full-bleed paper field `#F4F0E6`;
  - three horizontal rules `#D9D2C1`;
  - a heavy **"="** in `#2C5E4F`, right of centre, with a short double underline in `#9A4A14` (the "total" mark).
  - No Material glyph and no gradient.
  - It replaces every size in `ios/Runner/Assets.xcassets/AppIcon.appiconset/` and the Android `mipmap-*` and adaptive icon (background `#F4F0E6`). Update `flutter_launcher_icons` (`background_color_ios`, `adaptive_icon_background`) to `#F4F0E6`.
- **Launch screen.** In `flutter_native_splash`, set `color "#F4F0E6"`, `color_dark "#161A17"` and `image` to the new "=" mark, then regenerate. The result is the iOS storyboard background in paper rather than white, plus Android and Android 12.
- **Ads placement.** The banner stays (agl_ads infrastructure), but it is **never on the sheet editor or near the keypad row**. It shows only at the bottom of the Sheets list and the Tools drawer. ATT and UMP behaviour stays unchanged.
- **Acceptance:**
  - A test asserts `colorScheme.primary == Color(0xFF2C5E4F)` and `scaffoldBackgroundColor == Color(0xFFF4F0E6)` in light mode, and `0xFF161A17` in dark mode.
  - The font files exist and are declared, and `google_fonts` is absent from `pubspec.yaml`.
  - `grep -rn "Inter'\|GoogleFonts" lib` → 0.
  - The developer views the regenerated 1024 icon and the launch screen in a simulator screenshot and attaches both to the report. Per memory "build it and look at it", a green test run is not enough.

**M6. Remove this app's template tells and dead code (criteria 4 and 5).**
- **Sign-in family (the account does nothing here).** Delete:
  - `screens/auth/login_screen.dart`, `state/auth_provider.dart`, `services/auth_service.dart`, `services/supabase_config.dart` and `app_env.dart`;
  - the `/login` route, the `Supabase.initialize` and `AppEnv.validate` calls in `main.dart`, and Settings → Account (sign in, sign out, delete account);
  - the dependencies `supabase_flutter`, `google_sign_in`, `sign_in_with_apple` and `crypto`;
  - the ARB keys `authTwoFactor`, `authCancel`, `authVerify`, `authOtpHint`.
  - Account deletion (5.1.1(v)) no longer applies because the app no longer creates accounts. Accounts created earlier are shared across AGL apps and can still be deleted from the support site; see Q4.
- **Pro paywall (default path, pending Q2).** Delete:
  - `screens/paywall_screen.dart`, `monetization/premium_provider.dart`, `premium_gate.dart` and `widgets/pro_badge.dart`;
  - the `in_app_purchase` dependency, the RevenueCat DUMMY keys and the product ids;
  - every `paywall*`/`settingsSubscription*`/`settingsCalcMasterPro`/`settingsRestorePurchases` ARB key.
  - The **year-by-year EMI and compound breakdowns become free** (`finance_screens.dart:667-781`: drop `_BreakdownLocked`).
  - With nothing for sale there is no 2.1(b) IAP to submit and no 3.1.2(c) EULA requirement. *If the founder chooses to keep Pro (Q2), skip this bullet. Instead, the IAP products must be submitted in App Store Connect with review screenshots, and the paywall and description must carry a working Terms of Use link (Apple standard EULA URL).*
- **Dead code.** Delete:
  - `screens/diagnostics_screen.dart`, `widgets/affiliate_cta.dart`, `monetization/affiliate_service.dart` (`affiliatesEnabled = false`, no call site), `widgets/hub_tile.dart` and its test case;
  - the commented-out classes at `tools_screens.dart:333-388` and `:760-813`;
  - the ARB keys `aiChatHint`, `aiChatTitle`, `aiChatEmpty` and `pillUnitConversion`/`pill*`;
  - in AGENTS.md, the `ai_chat_provider` and "demo mode" lines (update the file map).
- **Copy.** Remove "World calculator & converter" (`appTagline`), "Tap any unit to convert instantly" and the hub headings. New strings describe sheets and tools.
- **Locales.** Every new or removed key changes in **all 12** `lib/l10n/app_*.arb` files, then run `flutter gen-l10n`. `test/locales_test.dart` must still pass. Do not ship English text inside a non-English ARB while claiming it is translated: either translate it, or list the untranslated keys in the report.
- **Tests that exercise deleted features are deleted with them, and only those.** Expected: `account_deletion_test.dart`, `paywall_screen_test.dart`, `premium_provider_test.dart`, and the Pro parts of `pro_and_region_test.dart`, `monetization_seams_test.dart` and `monetization_config_test.dart`. Name every deleted test file and case in the commit message so QA can check that nothing else was dropped.
- **Acceptance.** `grep -rn -i` over `lib/` and the generated l10n for each of these returns 0: `Sign in with Apple`, `Continue with Google`, `Welcome Back`, `BEST VALUE`, `Ad-free experience`, `in this build`, `only calculator you need`, `supabase`, `RevenueCat`, `DUMMY`, `aiChat`, `Cupertino` (the world-clock label; replace it with San Francisco or the user's zones, see S3).

**M7. Honest states everywhere (criterion 5).**
- No invented numbers anywhere. Every currency figure comes from a real ECB rate, shown with its date, or is replaced by a reason. There is no static fallback rate table: AGENTS.md still lists `staticRates`, but `grep -rn staticRates lib` returns 0 (checked 2026-10-12). Correct AGENTS.md, and do not reintroduce one.
- **Income tax and paycheck.** These screens show the year of the table they use, right beside the result: "Estimate using 2025 brackets — check your current year's rules". `lib_payroll.dart:9` and `finance_screens.dart:343` say "simplified 2025". The Tax screen shows no year today. Do not label 2025 tables as current.
- **Offline.** Every screen that needs the network (currency tool, dated lines, Re-price) shows an offline state with the cached date, or a reason. Re-price while offline shows "Can't re-price offline — showing rates as of 9 Oct".
- **Copy.** No "coming soon", "not connected", "in this build" or "unavailable" copy remains for a feature that exists. The only "unavailable" message allowed is a specific reason ("The ECB publishes no reference rate for AED").
- **5.6.** One build for everyone. There are no remote feature switches, no reviewer, region or date detection, no hidden gestures and no demo login.
- **Acceptance.** Tests for the offline Re-price message and the tax-year label on both the Tax and Paycheck screens.

**M8. Proven (criterion 6).**
- `flutter analyze` → "No issues found!". `flutter test` → all pass. The only skip allowed is the existing `design` tag.
- **New tests:** `test/sheet_engine_test.dart` (every line type in M1, references, percentages, units, errors, total exclusion); `test/rate_on_day_test.dart` (M2 list); `test/sheet_store_test.dart` (persist and reload, notes migration, delete and undo); `test/sheet_export_test.dart` (M4); `test/identity_test.dart` (M5); and widget tests for first launch, Tools → Add to sheet, and BMI having no Add to sheet.
- Rewrite `tabs_test.dart`, `accessibility_test.dart`, `semantics_labels_test.dart`, `foldable_layout_test.dart` and `smoke_test.dart` for the new navigation. **Do not weaken their assertions:** the accessibility tests must still check labels on every interactive control, including the sheet rows and accessory keys.
- Regenerate `test/goldens/*` with `--run-skipped --update-goldens --tags design` after M5, and view them.
- Launch the app on the iOS simulator; per memory, an Android emulator cannot be built here. Take screenshots of: the first launch (empty sheet with hints), a sheet with a dated EUR line, the Tools drawer, Share, and the Night ledger theme. Attach them to the report.
- Commit by path (see the header) and push to `main`. Quote the analyze and test output in the report.

### SHOULD (if time allows, in this order)

- **S1. Rate history for a line's pair. Conditional on D3 (Q1).** If the founder retires NexusTransferPay, tapping a currency line opens its pair's 1M / 3M / 1Y ECB history (range endpoint, §3) with the line's date marked. Use a simple `CustomPainter` line and no new chart dependency. If NexusTransferPay is kept, do not build S1: its spec keeps the corridor history there.
- **S2. Date lines.** `today + 90 days`, `days from 2026-01-01 to 2026-10-12` and `age on 2026-10-12 born 1990-05-01`, reusing the Date difference and Age logic.
- **S3. World clock with real zones.** Replace the fixed 10-city list with fixed offsets and DST rules (`tools_screens.dart:601-613`) with the device zone plus user-picked IANA zones, via the pure-Dart `timezone` package (bundled tzdb, no native code).
- **S4. Unit arithmetic.** `2.5 m × 3.2 m` → `8 m²`, and `÷ 2.2 m² per box` → boxes. Dimension checking only for length, area and volume.
- **S5. Cupertino affordances on iOS.** `CupertinoIcons` for the top-bar actions, and adaptive switches and dialogs on iOS. Material stays on Android.
- **S6. Year labels for other dated tables.** Apply the same "table year" label to customary tips and sales-tax defaults where they are hard-coded.

## 5. Store impact (proposed; store-compliance applies it later. Nothing was written to `store/` or `fastlane/`)

**Name and subtitle.** The name change is optional: Q3.
- Name (≤30): **"CalcMaster: Sheet Calculator"** (28). The current name is "CalcMaster: World Calc".
- Subtitle (≤30): **"Sums with units & dated rates"** (29). The current subtitle is "World calculator & converter".

**Promotional text (≤170):** "Convert a receipt at the European Central Bank rate for the day you paid. Every line shows its rate and date, and your sheet gives the same answer next month."

**Description (draft).** It does not open with the app name, has no '——' headings, and has no "only calculator you need":
> Work out real-life sums on ruled sheets. Type a line, and its answer appears beside it: 18% of a bill, 12 ft in metres, 38.50 EUR in dollars. Reference earlier lines with #2, and keep a running total at the bottom.
>
> Rate on the day: add a date to any currency line — "120 GBP on 15 Sep in USD" — and it is converted at the European Central Bank reference rate published for that day, back to January 1999. The rate and its date are printed under the result. Weekend dates use the ECB's previous working day, and the app tells you which day that was. Rates on a saved sheet are pinned, so it shows the same answer when you reopen it; re-price to today's rates only when you choose.
>
> Thirty tools feed your sheets: tip and split, discount, sales tax and VAT, income-tax and paycheck estimates for 11 regions (the table year is shown on every result), loan payments with a year-by-year schedule, compound interest, unit price, ten unit categories, date difference, age, world clock, calendar, scientific, percentage, number bases, fractions, Ohm's law, ADC/DAC, GPS coordinates and BMI. Tap Add to sheet and the result becomes a labelled line.
>
> Share a sheet as text or export it as CSV, with each exchange rate, its date and its source listed — ready to paste into an expense claim or an invoice note.
>
> Your sheets stay on your device. There is no account. Exchange rates come from the European Central Bank via Frankfurter (api.frankfurter.dev) and cover 30 currencies. They are reference rates, not the rate your bank or card charged. Ads are shown on the sheet list and the tools page, never on the sheet you are working on.

- Keep the ads-consent sentence that store-compliance requires, in its own words. Do not reuse the 32-app sentence verbatim if policy allows.
- If Pro is kept (Q2), add the subscription terms and the Terms of Use (EULA) link (3.1.2(c)).

**Keywords:** `sheet,notepad,calculator,currency,exchange rate,ECB,units,converter,tip,split,expense,invoice,loan` (98 characters, under the 100 limit).

**Screenshots.** Retake all; the current 01 is the converter that duplicates NexusTransferPay. iPhone 6.9" and iPad 13", in this order:
1. A trip sheet: three currency lines with dates (EUR, GBP) in USD, each with its ECB caption, and the total. Caption: "Converted at the rate on the day you paid".
2. A DIY sheet in feet and metres with a percentage line for waste. Caption: "Units, percentages and totals, line by line".
3. The Tools drawer. Caption: "30 tools that add straight to your sheet".
4. The Share/CSV preview showing the rate, date and source. Caption: "Export with every rate and its source".
5. The Sheets list with search, in Night ledger. Caption: "Every sheet saved and searchable".

The amounts are typed in the simulator as scenario inputs. The rates must be the real fetched ECB values; the captions on screen show their dates. No sign-in, paywall or consent screens. Update `integration_test/store_screenshots_test.dart` accordingly.

**Play.** A new feature graphic in the Ledger palette with the "=" mark. Today it uses the shared generated layout. Release notes: "CalcMaster now works on sheets. Your notes were moved into sheets automatically. Sign-in has been removed — nothing was stored in your account."

**Review notes (rewrite; do not reuse the numbered skeleton that starts at "2. DEVICES"):**
- What it does, and for whom, in the words of §2 above, not the subtitle.
- How to reach the signature feature: "On the first sheet, type `38.50 EUR on 14 Sep in USD`. The line shows the converted amount and, under it, the ECB rate and the date it used. Type `100 EUR on 2026-10-10 in USD`: Saturday has no ECB rate, so the caption names Friday 9 October."
- **No demo account.** Set `demo_account_required: false` and remove `demo_account_name`. State "No account exists in this app."
- Devices tested: list **only** what was actually run, and do not claim physical-device testing unless it happened.
- Contact name: a real person (Q5), not "App Reviewer".

**Privacy label (`store/privacy/CalcMaster.json`, `_derived_from` `account:true, iap:true`).**
- With the default path, drop `EMAIL_ADDRESS`, `NAME`, `USER_ID` (no account) and `PURCHASE_HISTORY` (no IAP).
- Keep `DEVICE_ID`/`ADVERTISING_DATA` (ads, ATT), `CRASH_DATA`, `PRODUCT_INTERACTION` and `PERFORMANCE_DATA`.
- The privacy *policy* text change is legal text (Q4).

**Differentiation answers (`store/apps/CalcMaster.json` `differentiation`):**
- §3 gap: (a)–(c) from §2, naming Soulver 4 and CalcMate and the narrow difference.
- §5 and §6: "Not a feature of NexusTransferPay: CalcMaster converts amounts at reference rates; it has no remittance fee or margin audit. Not iMeasure (its converter is removed per `overlap.md` G4), HomeWise (no affordability) or CarDeal (no car flows)."
- §7: Supabase is removed from the shared-code list.

## 6. Out of scope

- Accounts, cloud sync or iCloud. Sheets are on-device only.
- Any second rate source, crypto, or currencies outside the ECB's 30. Never estimate a missing rate.
- Remittance quote checks, fee or margin audits, provider rankings, World Bank benchmarks (NexusTransferPay's lane).
- Budgets, categories, recurring expenses or account balances (MyFinance). Home affordability (HomeWise). Car buying (CarDeal). Health logging; BMI stays a calculator.
- Free-form natural-language parsing beyond the M1 grammar. Photo or receipt OCR. An AI assistant.
- Home-screen widgets, a watch app, Siri.
- Pricing changes, new IAP products, ad budgets (Charter §3).
- The shared infrastructure files (`error_reporter.dart`, `crash_reporter.dart`, `agl_observability`, `agl_ads`, `agl_i18n`). They may stay.

## 7. Not verified

- Competitor behaviour beyond the App Store descriptions I read. Soulver 4 may support dated rates without saying so.
- Whether App Store Connect currently holds CalcMaster IAP products, and in what state. Apple's 2.1(b) message implies they exist but were not submitted. I made no ASC call.
- Whether any user ever created an account through CalcMaster. I did not query Supabase.
- How the new build behaves on a physical device or an Android emulator. I built nothing; this is a spec.
- The quality of translations for new strings in 11 locales.
- Whether adding `share_plus` changes `project.pbxproj` in this repo.

## 8. Founder questions (Charter decisions; the office does not take them)

- **Q1. D3: retire or keep NexusTransferPay (Charter §8).** `overlap.md` G3 recommends that CalcMaster absorb the ECB rate-history view and that NexusTransferPay be retired. `specs/NexusTransferPay.md` instead proposes keeping it as a remittance-cost audit tool. This spec builds the history view (S1) only if NexusTransferPay is retired. Either way, CalcMaster stays out of fee and margin auditing.
- **Q2. CalcMaster Pro (Charter §3, money).** The default in this spec is to remove the paywall and make the year-by-year breakdowns free. That removes Apple's 2.1(b) and 3.1.2(c) issues. Alternatively, keep Pro: someone must create and submit the IAP products in App Store Connect with review screenshots and add a Terms of Use link. Which one?
- **Q3. Store name** "CalcMaster: Sheet Calculator" instead of "CalcMaster: World Calc". This is listing text the office may change, but it is a brand change, so I am asking first.
- **Q4. Privacy policy (Charter §6, legal text).** Remove account data (email, name, user id) and purchase history from the CalcMaster policy. Confirm that the support-site account-deletion path stays live for accounts created earlier, since they are shared across AGL apps.
- **Q5. App Review contact.** A real person's name instead of "App" / "Reviewer" (`store/defaults.json`).
- **Q6. Resubmission and reply (Charter §1).** Nothing is submitted while the 5.6 hold (MA-043) stands. When it lifts, the 4.3 reply should argue §2's narrow gap and admit that the sheet-calculator category exists.
