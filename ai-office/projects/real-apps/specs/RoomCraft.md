# Spec: RoomCraft becomes "know the furniture fits before you buy it"

- Author: product-manager (AI office), 2026-10-12
- Repo: `/Users/spatchava/agl/RoomCraft`, branch `main`, base_sha `e2201bc1349841c0d145f66752baf3cbcef3c81f`. Both values come from `git rev-parse HEAD` and `git branch --show-current`, run today.
- Apple: rejected under **5.6** on 2026-10-08T14:19:41.128Z (`/Users/spatchava/agl/.dist/rejections.json` key `RoomCraft`: 1 thread, 1 message). The text names no feature. It says only "the app contains features that appear to have been intentionally hidden during the review process". The same text went to 16 apps within one minute. `docs/store-holds.json:197-201` records the hold. Google Play: PRODUCTION_DRAFT_STAGED.
- Plan: `projects/real-apps/plan.md`, which sets seven acceptance criteria. Overlap: `projects/real-apps/overlap.md:43` (G11) says "RoomCraft searches only material shops for a design". NearServe owns service providers.
- Baseline, measured today: `flutter analyze --no-pub` reported "No issues found! (ran in 8.2s)" and `flutter test --no-pub` reported "+96: All tests passed!". The shasum of `git status --short` was `f466daba…` both before and after, so the runs changed nothing in the repo.

**Other people have uncommitted work in this repo. Leave it alone.** `git status --short` today shows modified `fastlane/metadata/**` (descriptions, notes.txt, every screenshot), new `*-04.png` screenshots and a modified `ios/Podfile.lock`. **None of the files this spec asks the developer to change has uncommitted edits right now.** Those files are `lib/**`, `test/**`, `integration_test/**`, `pubspec.yaml`, `assets/**`, `ios/Runner/Info.plist`, `ios/Runner/Base.lproj/LaunchScreen.storyboard`, `ios/Runner/Assets.xcassets/**` and `android/app/src/main/AndroidManifest.xml`. The fastlane screenshots and notes belong to store-compliance (section 5).

---

## 1. Problem

### What the app is today
I read all of `lib/`: 6 files, 2,083 lines. Tests: 10 files, 1,701 lines, plus `integration_test/store_screenshots_test.dart`.

| Area | State | Evidence |
|---|---|---|
| Shell | One 849-line `main.dart`. It has a Material `NavigationBar` with three tabs (Design / Redesign / Sourcing), `AglAdBanner` directly above the bar, and an app-bar title "RoomCraft — <tab>". | `lib/main.dart:137-180`, banner at `:159` |
| Design tab | A form: room type, square footage, style. It returns cards of text: philosophy, a palette shown as hex strings in bullets, a furniture name list cut to N pieces, one of three size paragraphs, and the room type's guideline paragraph. **It works, but it only produces a printout.** It has no dimensions, no drawing and no check of whether anything fits. | `main.dart:385-491`; `roomcraft_service.dart:227-249`; `layout_planner.dart:41-94` |
| Redesign tab | Free text in "What is in the room?". A keyword match finds only `window`, `door`/`entrance`, `fireplace`/`hearth` and `radiator`/`heater`, then prints up to 3 canned sentences and 4 canned steps. The code still calls it "OCR" (`ocrRedesign`, `ocrAnalysisText`) and the tab icon is `Icons.document_scanner`, but **nothing scans anything**. The code says so: "nothing reads a photo" (`roomcraft_service.dart:251-252`). | `main.dart:170-171, 493-616`; `layout_planner.dart:59-82` |
| Sourcing tab | This part is real. The user enters a typed place (Nominatim) or lat/lng plus a free-text material. Overpass then returns `shop=*` within 15 km, nearest first, with an honest error and an honest empty state, and no sample fallback. **It is disconnected from the design**: the material is typed by hand and is unrelated to the room the user just planned. | `roomcraft_service.dart:161-202, 285-419`; `main.dart:620-824` |
| Domain data | 6 room types, each with clearance rules: walkway 30 in, sofa to coffee table 14–18 in, bedside 24 in, 36 in in front of dressers, kitchen aisle 42/48 in, work triangle 13–26 ft, bathroom 21 in clear and 15 in from toilet centreline, desk chair 36 in, dining 36/42–48 in, 24 in per seat. It also has 6 styles × 6 rooms × 9 furniture names. **These clearance numbers are the most valuable thing in the repo, and the app only prints them as prose.** | `room_type.dart:9-75`; `design_styles.dart:28-503`; radiator 12 in at `layout_planner.dart:80-81` |
| Persistence | None. Every result is lost when the user switches tab or relaunches. | no storage package in `pubspec.yaml` |
| Share / export | None. | |
| Settings / onboarding | None. "Privacy choices" lives in an overflow menu that appears only where UMP requires it. | `main.dart:208-239` |
| Identity | Seed `0xFFD4A373`, system font, stock Material 3. pubspec `description: "A new Flutter project."`. `CFBundleDisplayName` `Roomcraft`, `CFBundleName` `roomcraft`, Android `android:label="roomcraft"`. | `main.dart:45, 110-120`; `pubspec.yaml:2`; `Info.plist:9-18`; `AndroidManifest.xml:5` |
| Infrastructure | `lib/core/observability/crash_reporting.dart` duplicates `AglCrash.init` (the brief says it is an exact copy of CarDeal/GadgetNest/WiFiTrail). `main.dart` calls both, at `:17` and `:26`, so Firebase is initialised twice. | `main.dart:17-26`; `agl_observability/lib/src/crash.dart:37-72` |

### What Apple and Play users saw
- **Screenshots at HEAD.** I extracted all three with `git show HEAD:fastlane/screenshots/en-US/iphone69-0{1,2,3}.png` and opened each. They show **three empty forms**: Design with defaults and no result, Redesign with an empty text box, and Sourcing with lat/lng `42.3601, -71.0589` prefilled and no results. **No screenshot shows the app doing anything.** The Sourcing shot comes from an older build: the current code prefills nothing (`main.dart:629-634`) and has a place field that the shot lacks. So the listing showed a screen the reviewer could not find. (Someone else's uncommitted working copy replaces these screenshots. I did not open or judge those files.)
- **Play feature graphic** (`fastlane/metadata/android/en-US/images/featureGraphic.png` at HEAD, opened): the **default Flutter logo** on grey, with the tagline "Interior design from square footage and OCR". **The app has no OCR.**
- **Icon:** a white Material `weekend` sofa glyph on a `#4E342E → #A1887F` gradient, from `scripts/generate_app_icons.py:78`. **Splash:** the shared storyboard, shasum `3f6a9b27d80d…`, measured today.
- **Store name** "iRoomCraft" (`store/apps/RoomCraft.json` `copy.en.name`, with a `_name_note` explaining the 409 name conflict). The home screen says "Roomcraft".

### Why Apple would see hidden features (5.6) or a template (4.3)
Apple named no feature, so none of these is confirmed as the cause.
1. **The listing promises a feature the binary lacks.** The feature graphic says "OCR". The Redesign tab uses a document-scanner icon. The HEAD screenshots show a Sourcing screen from an older build. A reviewer who looks for scanning, or for the screen in the screenshot, will not find it. That is the plainest reading of "features that appear to have been hidden".
2. **The review notes contradict the binary.** Notes §6 says "The app follows the device language for 12 locales… shared labels are translated" (`store/apps/RoomCraft.json` `review_information.notes`). The app has declared English only since `e4e551f` (`main.dart:43, 104-107`), and `test/i18n_test.dart:60,70` enforces that.
3. **Remote Config is fetched at launch.** `AglInsights.init` (`main.dart:21`) starts Firebase Remote Config and runs `fetchAndActivate()` (`packages/agl_observability/lib/src/insights.dart:104-125`). RoomCraft reads **no** key: grep of `lib/` for `AglInsights.flag|AglInsights.setting|getBool|getString` found 0 hits. Even so, the mechanism Apple associates with switching features on after review is present in the binary.
4. **The ads behave differently in a short session.** Interstitials have a warm-up of 2 transitions and a 3-minute cap (`agl_ads/lib/src/ads.dart:22,26`). "Privacy choices" appears only in UMP regions. Both are legitimate, but neither is explained to the reviewer.
5. **Our own history contains a false statement.** Commit `c75f90e` says screenshots were "signed in with the QA account", but the app has no sign-in. It did not ship in the binary.
6. **The 4.3 look:** a generator icon, the shared splash, a Material bar with a banner above it, the system font, stock Material on iPhone, and output that is a stack of text cards. That last part is "what's already widely available": a style quiz that prints furniture names.

---

## 2. User and product decision

**User:** someone furnishing or rearranging **one real room** with a tape measure in hand. Typically a renter who has just moved in, or someone about to buy a sofa, bed, desk or dining table. They want to know: *will this piece fit, and will the room still work: can I walk past, open the wardrobe, get into bed from both sides, open the door?* They do not want to learn a 3D modelling tool, browse an 8,000-item catalogue or create an account.

**Core job (one, done well):** from a few tape-measure numbers (wall lengths, door and window positions, the actual dimensions of the pieces), draw the room **to scale** and **check every clearance that matters for that kind of room**. The answer is a verdict: **Fits / Tight / Doesn't work**.

**Signature feature: "Clearance Check". Every gap measured against the rule for this room, with the fix.**
Each saved room gets an automatic layout and a list of checks. Each check shows **the measured gap, the gap needed, and the source rule**. The rules are the ones already in `room_type.dart`, plus door swing and the radiator 12 in. Examples:
- "Sofa to coffee table: 9 in. Needs 14–18 in."
- "Left side of bed: 18 in. Needs 24 in to get in."
- "Door swing (32 in) hits the wardrobe."
- "Kitchen work triangle: 29 ft. Keep it within 13–26 ft."

For each failure RoomCraft computes **a concrete fix**: "Move the desk 6 in toward the window", or "**The widest sofa that passes on this wall is 78 in**". The second is solved by shrinking the piece until every check passes.

**Why it is distinct.** I checked competitors today with the keyless iTunes Search/Lookup API (`itunes.apple.com/search?…&entity=software`, `itunes.apple.com/lookup?id=…`). What follows is each app's own App Store description, not hands-on testing. WebSearch is disabled here ("Internet mode is not enabled"), so I verified nothing beyond these descriptions. I also searched every full description for the terms `clearance`, `walkway`, `walking space`, `door swing` and `spacing`. **None of the five planners below contains any of them.**
- **Planner 5D: AI Home Design** (Planner5D, UAB, id606173978, 4.36★ / 41,846): "2D & 3D floor plans", "8,400+ furniture and decor items", "drag-and-drop", AI generation and a subscription. It is a catalogue and visualiser. **Its description mentions no clearance checking.**
- **Home Planner AI: Room Design 3D** (Room Planner Ltd, id1076159017, 4.6★ / 46,316): 3D modelling, a 3D scanner, "precise measure functionality". **It mentions no clearance rules.**
- **4Plan Home & Interior Planner** (Alatona UAB, id1570446253, 4.58★ / 3,014): 2D drawing and 3D view, a catalogue with adjustable width and depth, PDF share. **It mentions no clearance rules.**
- **magicplan** (Technologies magicplan Inc., id427424432, 4.66★ / 41,220): professional floor plans for remodelers and claims, with estimates. It targets a different user.
- **Will It Fit? AR** (id6768062410, 0 ratings): places an AR box of given dimensions. It shows **one object, with no room rules**.
- RoomCraft's honest angle is the **rules**: a room-type-specific clearance check with measured gaps and computed fixes, from typed measurements, on the device, with no account, no camera and no catalogue. IKEA's and Wayfair's in-app planners: competitor not verified. The store copy (section 5) must not claim "only app" or "competitors can't".

**What stays, scoped (MUST OWN, from the brief):**
- **Room layout from room size and the user's notes:** the to-scale plan plus auto-layout. The notes field stays: keywords pre-fill feature chips (`layout_planner.dart:59-68`), which the user then positions.
- **Redesign mode:** "Rearrange what you have". The user's own pieces at their measured sizes are re-laid out and checked, with a style direction.
- **Materials from nearby shops:** quantities computed from this room's geometry, then OSM shops for those materials only (`roomcraft_service.dart:161,288`).

**MUST NOT:**
- No general directory of service providers: no trades, cleaners or installers (NearServe). The shop search covers only the materials on a room's list.
- No affordability or mortgage maths (HomeWise). No device or remote control (PlantPulse).
- No catalogue of priced products, no retailer or affiliate links, no prices of any kind.

---

## 3. Acceptance criteria

### MUST: what Apple needs to see a real, distinct app. Each item is testable.

**M1. Core job end to end: a to-scale room plan (plan criterion 1).**
- **New room** is a 4-step flow, with no carousel:
  1. Room type (the 6 in `RoomType`) and a name.
  2. Width and length, plus an optional ceiling height. Units are ft+in or m+cm, set in Settings and defaulted from the device locale's measurement system. Shape: rectangle only.
  3. Openings and fixed features. For each of the 4 walls the user can add doors (width, offset from the corner, hinge side, swing in/out), windows (width, offset, sill height), a radiator/heater and a fireplace. A **Notes** field ("Anything else in the room?") is kept. Typing "radiator under the window" adds suggested feature chips through the existing keyword parser. The user places each chip on a wall, and **nothing is placed without the user confirming it**.
  4. Pieces. Start from the room type's list in the chosen style (`design_styles.dart`). Each piece carries an editable width × depth, pre-filled with a **typical size**. Every pre-filled size is labelled "Typical — measure yours", and the user can type exact sizes. Standard mattress sizes (Twin, Full, Queen, King) are offered as named presets.
- **Plan view:** a `CustomPainter` canvas drawn to scale on a 1 ft (or 25 cm) grid. It shows walls with dimension lines in the mono font, door swing arcs, windows, radiator and fireplace, and pieces as labelled outlines. The user can **drag pieces, rotate them in 90° steps** and pinch-zoom. Position snaps to 1 in (or 1 cm).
- **Auto-layout:** a deterministic placement that ports the existing rules: anchor piece first (bed headboard on a solid wall, not under a window; sofa facing the focal point; desk at right angles to the window), then the remaining pieces by importance. It tries wall-aligned positions and keeps the arrangement with the fewest failed checks. **The same inputs always give the same layout.** A piece that cannot be placed anywhere is listed as "Doesn't fit in this room", with the largest size that would fit.
- Remove every "OCR" name in the code (`ocrRedesign`, `ocrAnalysisText`, class `OcrRedesign`) and the `document_scanner` icon.
- Accessibility: the canvas exposes a `Semantics` summary (e.g. "Bedroom 12 ft by 14 ft, 5 pieces, 2 checks failing"). The Check list (M2) is the full accessible equivalent of the plan.
- *Tests:* wizard validation (zero, negative or non-numeric sizes rejected with a live-region error; a door wider than its wall rejected). Auto-layout for a 12×14 ft bedroom with a queen bed puts the headboard on a wall with no window. The layout is deterministic: same input, same output. Unit conversion round-trips.

**M2. Signature feature: Clearance Check (plan criterion 2).**
- For every room, compute and list checks from `RoomType` rules plus door swing (no piece inside the arc), radiator (≥12 in), windows (pieces over 36 in high must not stand in front of a window), and walkway (≥30 in clear path from each door to every piece that needs access).
  - The existing numbers stay the single source of truth and move from prose into a typed rule table.
  - **Do not attribute a rule to an outside body (e.g. NKBA) unless the developer verifies that citation.** Otherwise the label is "RoomCraft's clearance rule for <room type>".
- Each check shows: the pieces involved, the measured gap, the required gap or range, and pass / tight (within 10% of the minimum) / fail. On the plan, failing gaps are drawn as hatched clash-red bands, and tapping a check highlights its gap.
- **Fix suggestions**, computed and never canned:
  - (a) the smallest move of one piece that makes the check pass without breaking another, if one exists;
  - (b) the largest width or depth of the offending piece that passes every check in its current spot, found by bisection.
- **Room verdict:** Fits (all pass) / Tight (no fails, at least one tight) / Doesn't work (at least one fail). It is shown on the room card and in the editor header.
- *Tests:* a unit test for each rule type, using hand-built geometry where the gap is known exactly: sofa–table 9 in fails, 16 in passes; bedside 18 in fails; door arc intersection fails; kitchen triangle 29 ft fails, 20 ft passes; bathroom 21 in passes at 21 and fails at 20. Fix (b) returns a width that passes, and a width +1 in that fails. Verdict mapping.

**M3. Redesign mode: rearrange what you have (MUST OWN).**
- On any saved room, **Redesign** duplicates the room as "<name> — redesign" (the original stays unchanged), keeps the user's own pieces and sizes, re-runs auto-layout, and shows **Before / After**: two plans side by side on tablets, a toggle on phones, each with its failing-check count. That makes "4 checks failing → 0" visible.
- Optional target style. Pick one of the 6 styles to get the palette as **real colour swatches** (not hex text) and the style's suggested additions that still fit. Each suggestion is checked: a piece is offered only if a spot exists where it passes every check.
- *Tests:* redesign never mutates the source room. The after-layout has at most as many failing checks as the before-layout for a fixture room. A suggested addition is offered only when it can be placed.

**M4. Materials list and nearby shops for this room (MUST OWN, scoped per overlap G11).**
- **Materials** tab of a room, every number computed from the room's geometry and shown with its formula:
  - Wall paint: (perimeter × ceiling height − door and window areas) × coats ÷ coverage. Coats default to 2. Coverage is an editable assumption labelled "from your tin's label", defaulting to 10 m² per litre (about 400 sq ft per US gallon). The result is shown in litres and US gallons. This step is hidden until a ceiling height is entered.
  - Flooring: floor area + waste %, editable, default 10%.
  - Skirting/baseboard: perimeter − door widths.
  - Rug: the size that holds the front legs of the seating group (living room rule), or extends 18–24 in beyond the bed sides (bedroom). These are computed from the placed pieces.
  - The furniture pieces themselves, with their sizes.
- **Find shops for this list:** a typed place (keep the existing Nominatim geocode) or the room's last-used place. Then one Overpass query whose `shop=*` set is the **union of the shop types for the items on this list only** (reuse `_shopsByMaterial`; add `flooring`, `carpet` and `furniture` mappings for flooring, rug and furniture).
- Each shop row shows name, kind, distance (km and mi), and the address, `opening_hours`, `phone` and `website` **only where OSM tags them**. OSM `opening_hours` strings are shown verbatim, labelled "Hours as listed on OpenStreetMap".
- **Directions** opens the platform maps app (`url_launcher`: `https://maps.apple.com/?daddr=lat,lon` on iOS, `geo:lat,lon?q=lat,lon(name)` on Android).
- **Save to this room** keeps a shop on the room's list, so it is still there offline.
- "Shop data © OpenStreetMap contributors (ODbL)" stays on every result screen.
- There is **no free-text "any material anywhere" search** and no category browser. The search exists only inside a room's Materials list.
- *Tests:* paint, flooring and skirting maths against hand-computed values in both unit systems. The Overpass query for a list with paint and rug contains `paint` and `carpet` and contains no type that is not on the list. The existing offline, empty and no-place tests are kept and moved to this screen. A saved shop survives a reload of storage.

**M5. Depth: persistence, search, share, states (plan criterion 3).**
- **Persistence:** rooms (geometry, openings, pieces, notes, style, saved shops, last place) are stored on the device as versioned JSON in the app documents directory (`path_provider`). Rename, duplicate and delete are available, and a delete can be undone from a snackbar.
- **Rooms home:** filter chips for room type and verdict (Fits / Tight / Doesn't work), and a search by name. The search is shown only when there are more than 6 rooms.
- **Share/export:**
  - "Share plan" renders the to-scale plan with dimensions, the verdict and the failing checks to a PNG and opens the share sheet (`share_plus`).
  - "Share materials list" shares plain text: quantities, formulas, and any saved shops with addresses.
- **States:**
  - Empty Rooms: this is the onboarding, see M6.
  - Room with no pieces: "Add the pieces you have or plan to buy".
  - Shops offline: "Can't reach OpenStreetMap. Your plan and list are saved on this phone." with **Retry**. Today's curl shows Overpass can fail transiently: the first query returned a non-JSON body and the second returned HTTP 200.
  - No shops: the existing honest message, naming the shop types searched.
  - Corrupt storage file: keep a backup copy and show "One saved room could not be read". Never crash.
- Everything except the shop search works in airplane mode.
- *Tests:* a save → kill → reload round-trip, including saved shops. Filter by verdict. The PNG export produces non-empty bytes at the plan's aspect ratio. A corrupt JSON fixture yields the message, not a crash. In airplane mode (stub fetcher throws), every non-shop screen still works.

**M6. Own identity: template tells removed (plan criterion 4). "Tracing paper and tape measure" look. Use these values exactly.**
- **Colour.** I grepped every `.dart` and `.md` under `/Users/spatchava/agl` (excluding build and SDK folders) for all six hexes today and found 0 hits.
  - Seed and primary: **eucalyptus `#35524A`**.
  - Accent, used only for dimension lines, the measuring cursor and the selected piece outline: **tape-measure yellow `#F2C230`**.
  - Light background: **tracing paper `#EEF0EA`**, with grid lines **`#D5DBD0`**.
  - Ink and text: **graphite `#2D3033`**.
  - Clash and fail: **brick `#C8442B`**. Pass uses the primary. Tight uses the accent outline.
  - Dark theme: background `#2D3033`, surface `#383C3F`, grid `#454A4D`, text `#EEF0EA`, with the same accent and clash colours. It follows the system setting.
  - Remove `_seed = 0xFFD4A373`.
- **Typography,** bundled under `assets/fonts/` with no `google_fonts` runtime download:
  - **Albert Sans** (`AlbertSans[wght].ttf`) for all UI.
  - **Geist Mono** (`GeistMono[wght].ttf`) for **every measurement**: dimension lines, gaps, sizes and quantities, with tabular figures.
  - Both are SIL OFL. On 2026-10-12, `curl -L` of `github.com/google/fonts/raw/main/ofl/albertsans/AlbertSans%5Bwght%5D.ttf` returned 200 (129,000 B) and `ofl/geistmono/GeistMono%5Bwght%5D.ttf` returned 200 (171,948 B). Both `OFL.txt` files returned 200 and must be shipped beside the fonts.
  - Grep: neither name appears in any spec or app here. "Albert" matched no spec. I am not reusing Jost (FashionFactory), Azeret Mono (MyCard), Spline (MyHealth), Martian Mono (EventSpark/CodeDeal) or Manrope (MyCard/HomeWise).
- **Shape language:** square corners (radius 2) on pieces and cards, 1 px graphite hairline borders, no elevation shadows, and no `BorderRadius.circular(12)`. Selected state is a tape-yellow outline, not a tonal fill.
- **Home layout** replaces the bottom `NavigationBar` and the shell entirely.
  - The **Rooms** screen is a large-title screen (`CupertinoSliverNavigationBar` on iOS, `SliverAppBar.large` on Android). Below it is a 2-column grid (1 column under 360 dp) of room cards. Each card shows a **live mini floor plan** drawn by the same painter, the name, dimensions in Geist Mono, and the verdict.
  - App-bar actions: **+ New room** and **Settings**.
  - The room editor is a pushed page with a segmented control **Plan · Check · Materials** (`CupertinoSlidingSegmentedControl` on iOS, `SegmentedButton` on Android) and a **Redesign** action.
- **Platform-adaptive on iOS** (today there is no Cupertino in any app): `CupertinoIcons` for navigation and actions on iOS, `showCupertinoModalPopup` action sheets for piece actions (rotate, resize, delete), `Switch.adaptive`, and Cupertino page transitions.
- **Onboarding:** no carousel and no "Get started". The empty Rooms screen is the onboarding:
  - a painted illustration of one room outline with a tape-yellow dimension line;
  - the line "Grab a tape measure. Two walls, the doors and your furniture sizes are all RoomCraft needs.";
  - the button **Measure your first room**.
- **Settings** (own copy):
  - Units.
  - Default ceiling height.
  - Paint coverage default.
  - "Privacy choices", only where UMP requires it (legally required). It moves here from the overflow menu.
  - "About the clearance rules": lists every rule with its number.
  - "Map data © OpenStreetMap contributors".
  - "Delete all rooms", with confirmation.
  - Version and contact.
  - **No `AglLanguageScreen`**: the app is English only.
- **Ads placement, own pattern:** one `AglAdBanner` as the last item of the Rooms grid and one at the end of the shop results, in layout flow. **Never** on the plan canvas, in the wizard or above a navigation bar. The interstitial on tab switch goes, because the tabs go. Whether any interstitial stays is a founder question (section 7).
- **Names:** `CFBundleDisplayName` and `CFBundleName` → `RoomCraft`, Android `android:label` → `RoomCraft`, `MaterialApp.title` → `RoomCraft`, and the pubspec `description` becomes a real sentence.
- **Icon:** a new 1024² master **not** from `generate_app_icons.py`. Motif: the corner of a floor plan in graphite on tracing paper, with a door-swing quarter arc and a tape-yellow dimension line with end ticks. No Material glyph, no diagonal gradient. Regenerate every `AppIcon.appiconset` size and the Android mipmaps and adaptive icon from it. Ask the `generate_app_icons.py` owner to delete the `RoomCraft` row (`:78`) so it cannot be regenerated over the new icon. The developer does not edit that shared script.
- **Splash:** replace the shared `LaunchScreen.storyboard`. The new one has a tracing-paper `#EEF0EA` background and the new mark, and its shasum must differ from `3f6a9b27d80d…`. Android `launch_background` uses the same colour.
- **Remove** `lib/core/observability/crash_reporting.dart` and its call at `main.dart:26`. `AglCrash.init` already initialises Firebase and Crashlytics and installs both error handlers (`crash.dart:46-72`). `test/release_sanity_test.dart:113` already asserts `AglCrash.init`.
- **Split** `main.dart` into feature files (`rooms/`, `editor/`, `check/`, `materials/`, `settings/`, `theme/`).
- *Tests:* `test/identity_test.dart`:
  - The theme's primary is `0xFF35524A` and the light scaffold background is `0xFFEEF0EA`.
  - The font families are Albert Sans and Geist Mono, declared in pubspec and present on disk.
  - `lib/` contains none of `0xFFD4A373`, `NavigationBar(`, `document_scanner`, `ocr`, `Get started`, `AglLanguageScreen`.
  - `Info.plist` `CFBundleDisplayName == "RoomCraft"` and the Android label is `RoomCraft`.
  - The storyboard shasum is not `3f6a9b27d80d…`.
  - The 1024 icon's hash differs from HEAD's.
  - On iOS (`debugDefaultTargetPlatformOverride = iOS`) the editor uses `CupertinoSlidingSegmentedControl`.

**M7. Honest, with nothing that looks hidden (plan criterion 5, Apple 5.6).**
- Every feature is reachable from the Rooms screen on first launch, with no account, no sign-in, no demo data and no seeded rooms. No `--dart-define` changes features or content: AdMob unit ids are the only defines. There is no region, date, locale or reviewer detection beyond UMP's own consent requirement. There are no hidden gestures.
- **No Remote Config in this app's behaviour:** add a test that greps `lib/` for `AglInsights.flag(`, `AglInsights.setting(`, `FirebaseRemoteConfig` and `getBool(` and expects 0 hits. Ask the agl_observability owner for `AglInsights.init(remoteConfig: false)`, so no fetch happens at all. That is the same request as in the AGCleaner spec (S4). RoomCraft uses it once it exists.
- Real data only:
  - geometry, pieces and checks are on the device;
  - shops come from live OSM;
  - every assumed default (typical piece size, paint coverage, waste %) is labelled as an assumption and is editable.
  - No prices, ratings, review counts or "popular" lists anywhere.
- *Tests:* the Remote Config grep. A fresh install shows the empty Rooms onboarding, not a sample room. No string in `lib/` contains "in this build", "coming soon", "not connected" or "unavailable" in user-visible copy.

**M8. Proven (plan criterion 6).**
- `flutter analyze` clean and `flutter test` all green. The baseline is 96 tests, and the final count must be higher.
- The existing test areas keep equivalent coverage against the new UI:
  - accessibility (headings, labelled controls, live-region errors, spoken measurements with "inches" and "square feet" spelled out);
  - responsive (320 px, short landscape, tablet clamp);
  - foldable;
  - ads placement (banner in flow and never on the canvas);
  - privacy-choices visibility;
  - i18n (English only, `CFBundleLocalizations`);
  - release sanity;
  - privacy manifest.
- Tests tied to removed UI (e.g. "app launches on the Design tab", "the coordinate pair re-flows") are **rewritten** for the screens that replace them. **No test is deleted or skipped to go green.**
- `integration_test/store_screenshots_test.dart` is rewritten to drive the real UI as listed in section 5.
- Build and launch on the iOS simulator and an Android emulator, take screenshots, and look at them. A green test run once missed a white screen.
- Commit path-limited (never `fastlane/` or `ios/Podfile.lock`) and push to `main`.

### SHOULD
- S1. **Use my location** for the shop search: `geolocator`, when-in-use permission, requested only when the user taps it. This changes the privacy label and Info.plist strings (section 5).
- S2. Share as PDF (the `pdf` package with the bundled fonts), A4 or Letter by locale.
- S3. L-shaped rooms (rectangle minus one corner rectangle).
- S4. Free rotation at 15° steps, with checks generalised to oriented rectangles.
- S5. iPad two-pane editor (plan beside the Check list).
- S6. Haptic tick when a dragged piece snaps to a wall or a check flips from fail to pass.

---

## 4. Data source
- **On-device:** room geometry, pieces, notes, layouts, checks, materials maths and saved shops. These are pure Dart functions plus JSON in the app documents directory. Clearance rules come from `lib/domain/room_type.dart:9-75` and `layout_planner.dart:80-81`, already in the app.
- **OpenStreetMap Nominatim** (geocode of a typed place). Curl-verified today: `nominatim.openstreetmap.org/search?format=jsonv2&q=Leeds&limit=1` returned HTTP 200 in 0.65 s, using the app's User-Agent (`roomcraft_service.dart:143`).
- **OpenStreetMap Overpass** (shops). Curl-verified today: around Leeds (53.7974, -1.5438), 15 km, `shop~paint|doityourself|hardware|fabric|tiles|flooring|curtain|carpet`. It returned HTTP 200 in 4.6 s with real elements, e.g. "Mike's Carpets" (`shop=carpet`), "Airedale DIY" (`shop=doityourself`), and "Everard Gas Appliance Spares" (hardware, with a full `addr:*`). An identical first attempt seconds earlier returned a body that was not JSON (status not captured), so the Retry state in M5 is needed.
- `docs/api-hosts.json` lists both hosts as `"ok"`, but its `RoomCraft` entry shows `hosts: 0`. The scanner does not see `Uri.https('host', …)` calls, so this app's hosts escape that gate today. Reported for the scanner owner.
- **Not used:** Supabase (no account or sync needed), any paid or keyed API, any product or price feed.
- New packages: `path_provider`, `share_plus`, `url_launcher` (all keyless). Fonts are bundled.

---

## 5. Store impact (proposals for store-compliance. I did not edit `store/apps/RoomCraft.json`, fastlane or docs.)

**Name.** "iRoomCraft" carries the 'i' prefix tell. Proposed App Store name: **"RoomCraft: Will It Fit?"**. Alternate: "RoomCraft Room Fit Planner". **Availability is not verified**: only App Store Connect can say, and it returned 409 for "RoomCraft". This needs a founder decision. Home-screen name: `RoomCraft`. Play title: "RoomCraft: Will It Fit?".

**Subtitle** (29 characters, counted): "Measure, place, check it fits".
**Play short description:** "Draw your room to scale and check every clearance before you buy furniture."
**Keywords:** `room planner,furniture fit,clearance,floor plan,measure,layout,bedroom,sofa size,rug size,paint` (100 characters or fewer; store-compliance must count).

**Description** (draft: no ALL-CAPS headings, does not open with the app name, no copied ads paragraph):
> Before the sofa arrives, find out whether you can still walk past it.
>
> Type in two wall lengths, where the doors and windows are, and the sizes of your furniture. RoomCraft draws the room to scale and lays the pieces out for that kind of room: the bed's headboard against a solid wall, the desk at right angles to the window, the sofa facing the fireplace.
>
> Then it checks every gap that matters, with real numbers: 14–18 inches between sofa and coffee table, 24 inches to get into bed, 36 inches to open a wardrobe, a door that can swing open, 42 inches of kitchen aisle. Each check shows the gap you have, the gap you need and how to fix it, down to the widest sofa that will work on that wall.
>
> Already furnished? Redesign re-arranges the pieces you own and shows before and after. The materials list works out paint, flooring, skirting and rug size from your room's measurements and finds hardware, paint, flooring and furniture shops near a place you choose, from OpenStreetMap.
>
> Your rooms stay on your phone, and there is no account. Everything except the shop search works offline. RoomCraft is free with Google AdMob ads, and where the law requires it you are asked for consent before any ad loads. Shop data © OpenStreetMap contributors.

**Screenshots to retake** (iPhone 6.9" and iPad 13", plus Play phone and tablet), all driven by the integration test through the real UI with values typed by the test. No seeded data and no stubbed network for shot 5:
1. Plan: a 12 ft × 14 ft bedroom, queen bed, two nightstands and a wardrobe, with the verdict "Tight".
2. Check list: "Left of bed 20 in / needs 24 in", with the fix "Move bed 4 in right".
3. Redesign before/after: "3 failing → 0".
4. Materials: paint litres and gallons, flooring, skirting and rug, each with its formula.
5. Shops for that list near a real place, live from OSM, with attribution.
6. Rooms home with 3 room cards and mini plans.

Delete every HEAD screenshot of an empty form.

**Play feature graphic:** replace the Flutter-logo graphic, whose tagline claims OCR, with the new icon on tracing paper, a slice of a plan with one hatched clash band, and the line "Will it fit? Measure, place, check."

**Review notes** (replace the numbered skeleton; write in plain prose):
- What it is: a to-scale room planner that checks furniture clearances. Who it is for: people furnishing or rearranging one room with a tape measure. **Do not paste the subtitle as the audience.**
- How to see the main feature in about 60 seconds: tap "Measure your first room" → Bedroom → 12 ft × 14 ft → add a door on the bottom wall → add Queen bed, 2 nightstands, wardrobe → open **Check**.
- **There is no camera, scanning or OCR**. The previous feature graphic wrongly said "OCR". No account, no sign-in, no remote configuration that changes features, and the same features in every region.
- Languages: **English only**. Correct the previous "12 locales" statement.
- Network: only the shop search, to OpenStreetMap Nominatim and Overpass. Ads: banner at the end of the Rooms list and at the end of shop results. Interstitial behaviour as decided in section 7. "Privacy choices" appears in Settings only where Google's UMP requires consent (EEA/UK), which is why a reviewer elsewhere will not see it.
- Devices: state only what was actually tested. If no physical-device run happened, do not claim one (section 7).
- Review contact: a real person's name, not "App Reviewer" (founder).

**Privacy label:** at present it is the shared 20-app label (Device ID, Advertising Data, Crash, Product Interaction, Performance), which matches `ios/Runner/PrivacyInfo.xcprivacy` today. M1–M5 add no new collection: rooms stay on the device. **Open question:** the typed place is sent to OpenStreetMap's servers. Whether that counts as "Coarse Location collected by a third party" is a founder/legal call (section 7). If S1 ships, Precise or Coarse Location becomes "App Functionality, not linked", and Info.plist needs `NSLocationWhenInUseUsageDescription`.

**Category:** keep LIFESTYLE. Productivity is an alternative only if the founder prefers it.

---

## 6. Out of scope
- 3D views, AR, LiDAR/RoomPlan scanning, photo upload, OCR, and AI-generated images or advice.
- Product catalogues, prices, retailer or affiliate links, "buy" buttons.
- Service-provider directories: trades, installers, cleaners (NearServe).
- Accounts, Supabase, cloud sync, sharing rooms between users.
- Non-rectangular rooms (SHOULD S3 only), multi-room floors, whole-house plans.
- Translation beyond English.
- Store submission, Resolution Center replies, and edits to `store/apps/*.json`, fastlane or docs (another workstream, or the founder).

---

## 7. Founder questions
1. **App Store name:** approve "RoomCraft: Will It Fit?" or the alternate. Only App Store Connect can confirm availability.
2. **Interstitials:** keep a capped interstitial (e.g. on returning from a saved room to Rooms), or banner only? Recommendation: banner only, for a drag-heavy editor and fewer surprises in review. It is a revenue decision (Charter §3).
3. **Privacy label:** does sending a typed place name to OpenStreetMap count as location data collected by a third party? This is a legal-text decision (Charter §6).
4. **Physical-device test:** Apple asked for physical devices. Will someone run the build on an iPhone and an iPad before resubmission, so the notes can say so truthfully?
5. **Resubmission** stays frozen under the 5.6 hold (MA-043, Charter §1). The office prepares notes and a reply draft, and the founder sends them.

---

## Note to the chief-of-staff (process incident, reported for the record)
While checking hosts, I ran `python3 scripts/verify_api_hosts.py --print` twice. The script always rewrites **`docs/api-hosts.json`** (`verify_api_hosts.py:175`), including with `--print`. That file is under `docs/`, which this task forbids editing. `git diff --stat` now shows 13 insertions and 15 deletions:
- PilotEnRoute's dead hosts are gone (other teams' code changes);
- `www.fts.tsa.dhs.gov` was added;
- `api.nal.usda.gov` flipped to "unverified: no address record", probably a transient DNS result.

I did **not** revert it. I cannot tell whether someone had uncommitted edits there before my run, and reverting could destroy theirs. The docs workstream owner should decide whether to keep or `git checkout` it.
