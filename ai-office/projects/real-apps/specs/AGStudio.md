# Spec: AGStudio, a prompt studio where you change the words but keep the picture

- **Author:** product-manager (AI office), 2026-10-12
- **Repo:** /Users/spatchava/agl/AGStudio (app in `mobile/`)
- **base_sha:** `49ac9589e6aa40f4fb2c556b155f4f9c1587bbc1`, branch `main`
- **Store state:** Apple rejected under 5.6 on 2026-10-08T14:19:51Z (`.dist/rejections.json` key `AGStudio`). The 5.6 hold is in `docs/store-holds.json:142`. Google Play: PRODUCTION_DRAFT_STAGED.
- **Baseline, measured at base_sha:** `flutter analyze` reports "No issues found!" and `flutter test` reports "+131: All tests passed!".
- **Others' uncommitted work in this repo (do not touch):** `mobile/fastlane/**` screenshots (modified and untracked), `mobile/ios/Podfile.lock`. Source: `git status --short`.

---

## 1. Problem

AGStudio does generate real images today, and it already does a number of things carefully. Prompts go to Pollinations.ai (`lib/services/pollinations_image_generation_service.dart:15,40`). The gallery stays on the device (`lib/services/history_repository.dart`). There are proper failure states, and save and share work. Even so, the app looks like the portfolio template and like every other "AI art" app:

| Tell | Evidence |
|---|---|
| Generated glyph icon | `scripts/generate_app_icons.py:63`: `"AGStudio": ("auto_awesome", "#4A148C", "#AB47BC")` |
| Neon-on-near-black look | `lib/core/brand.dart`: cyan `00F5FF`, purple `C724FF`, bg `0A0B14`, amber `F59E0B` (Tailwind amber-500). `lib/app/app.dart:26`: `themeMode: ThemeMode.dark` |
| No typeface of its own | No `fontFamily` or `fonts:` in `lib/` or `pubspec.yaml` (grep: no match) |
| Shared shell | `lib/app/app_shell.dart:124-125`: `if (showAd) const AglAdBanner()` directly above a 4-tab Material `NavigationBar` (Home / Studio / Gallery / Settings) |
| Shared splash | `ios/Runner/Base.lproj/LaunchScreen.storyboard`, shasum `3f6a9b27d8…` (the 37-app storyboard) |
| Leftover concepts that no longer exist | `AppMode.offline` and the cyan "on-device" accent (`lib/models/app_mode.dart`). A permanent **"ONLINE MODE"** badge on every image (`lib/widgets/backend_badge.dart`; visible in `fastlane/screenshots/en-US/iphone69-01.png`) although only one mode exists. "Offline"/"Preview" gallery filters (`gallery_screen.dart:28`). `PreviewNotice` for the "PREVIEW · NOT AI GENERATED" poster of old builds. Unused strings `genCreditsCost`, `creditsBalance`, `modeSwitchToOnline/Offline` (`app_en.arb:31,35,63,127`) |
| "This build" copy | `app_en.arb:237` `backendNotConfiguredBody`: "No AGStudio server is configured in this build…". `app_en.arb:439` `failureUnsupported`: "Image generation is not available in this build." |
| A build-time second backend that the reviewed binary never uses | `lib/core/app_config.dart:22-25` reads `AGSTUDIO_API_BASE_URL`/`AGSTUDIO_API_KEY`. `providers.dart:96-107` switches to `HttpImageGenerationService` when they are set. The file itself says the URL "is a placeholder that resolves to nothing" (`app_config.dart:15-16`). A dormant code path that switches backends is exactly the sort of thing a 5.6 reviewer reads as "hidden features". |
| Generic hero copy | `heroTitle` "Create Without Limits", `heroCta` "Start Creating", `heroCta2` "View Gallery" (`app_en.arb:111,119`) |
| Play feature graphic | `fastlane/metadata/android/en-US/images/featureGraphic.png`: purple "AG" monogram in the shared generated layout (inspected visually) |
| Store notes are the shared skeleton | `store/apps/AGStudio.json` `review_information.notes` starts "2. DEVICES AND OS VERSIONS TESTED" and says simulators/emulator. "Intended audience: Prompt to picture" is the subtitle pasted in. |
| Privacy label is the shared 20-app body, and it leaves out prompt text | `store/privacy/AGStudio.json` lists DEVICE_ID, ADVERTISING_DATA, CRASH_DATA, PRODUCT_INTERACTION, PERFORMANCE_DATA. It has no user-content entry, although every prompt is sent to Pollinations.ai. The listing's own `_blocker.requires` already flags this. |

Functionally the app is a thin "type → image" form, with eight style chips copied from a web app (`lib/models/style_preset.dart`). It offers nothing that the large incumbents lack. Apple's 4.3/4.2.6 wording ("indistinguishable from what's already widely available") applies to it even though it was rejected under 5.6.

## 2. User and honest product

**User:** someone who writes image prompts with care and iterates on them: an illustrator sketching ideas, a tabletop or game designer making concept art, a hobbyist writer picturing a scene. Their problem with typical generator apps: **when you change one word, you get a completely different picture.** You cannot tell whether "dawn" or "dusk" was the better word, because composition, subject and framing all changed as well.

**Core job (one thing, done well):** turn a written prompt, a style and an aspect into an image, and keep every image together with exactly what produced it, so it can be found again, reproduced, shared or refined.

**Signature feature: Seed Lock & Proof Sheets.** You lock the composition of a result (its seed). Then you edit the words, and the next render keeps that composition, so you see the effect of **only** the words you changed. Each locked series is a **Proof Sheet**, a thread of versions. The sheet shows:

1. an A/B compare with a drag divider between any two versions,
2. a word-level prompt diff (added words highlighted, removed words struck through),
3. an on-device export of the whole sheet as one PNG (thumbnails, prompts, diffs, seed), shared through the OS share sheet.

**Why this is real and buildable now (measured 2026-10-12 with curl against `image.pollinations.ai`):**
- `GET /models` returns `["sana"]`.
- The same prompt and the same `seed=12345` returned **byte-identical** JPEGs, including a request with an extra `nocache=1` query param. Both files have shasum `45a3ea1218e2…`. So locking a seed truly reproduces an image.
- Changing one word ("dusk" → "dawn") with the same seed returned a different image (`0ff53675…`) with the **same composition**: lighthouse left of centre, cliff on the right, beach in the foreground. I compared the two side by side in `/tmp/agstudio_probe/ac.jpg`; that comparison is my visual judgement.
- Real output sizes: 512×512 ✓, 768×768 ✓ (already in app), **576×1024 ✓ (9:16)** and **1024×576 ✓ (16:9)**, both returned at exactly that size. 1024×1024 was clamped: the error body's `requestParameters` shows `"width":768,"height":768`. So the cap appears to be about 768² pixels, and only these four sizes may be offered.
- Errors seen in that session: HTTP 402 with a 2-byte JSON body when requests are close together, and HTTP 500 with body `"Per-user limit of 300 RPM exceeded for model …"` (upstream overload). Both must surface as honest errors (see M5).

**Competitors (evidence limits stated):** web search is disabled in this environment (the WebSearch hook returned "Internet mode is not enabled"). Instead I queried Apple's keyless iTunes Search/Lookup API on 2026-10-12. These apps exist and are free to download: WOMBO Dream (id 1586366816, 143,704 ratings), AI Photo Generator: ARTA (1642969698), DaVinci – Image Generator AI (1630366866), starryai (1580512844), plus ChatGPT and Google Gemini. **None of the WOMBO, ARTA, DaVinci or starryai store descriptions contains the word "seed".** That shows only that they do not *advertise* seed locking or version comparison. **Whether the apps themselves lack the feature: competitor not verified.** The store copy must therefore not claim "only app that…". It describes what AGStudio does.

**Portfolio boundary:** AGStudio owns text-to-image (overlap.md G8). It must **not** add colour capture, palettes, photo grading or photo editing; those belong to Photriya, which drops its DALL-E playground. AGStudio has no camera and no photo-library *read*. It keeps add-only photo access (`media_saver.dart`, `Gal.putImageBytes`, `toAlbum: false`).

## 3. Acceptance criteria

### MUST (what Apple needs to see a real, distinct app)

**M1. One honest generation path; dead concepts removed.**
- Delete `HttpImageGenerationService`, `AppConfig`'s `AGSTUDIO_API_*` dart-defines and the provider switch (`providers.dart:96-107`). Pollinations.ai becomes the only generator, and it is the one the reviewer sees. Delete its tests (`test/services/http_image_generation_service_test.dart`) together with the code. Deleting a test is allowed only because the code it tests is deleted; say so in the commit message.
- Remove from all UI: `AppMode` offline/online, `BackendBadge` "ONLINE MODE", the Offline/Online gallery filters, `PreviewNotice`, the HD toggle (never shown on Pollinations), and the credits and mode-switch strings in all 12 ARBs.
- Legacy history rows from older builds (`backend == preview`) must still load. They show a small plain label, "Placeholder from an older version, not an AI image", in the image detail screen only. A fresh install never shows any preview/offline wording.
- *Test:* a widget test pumps the app on an empty store and asserts that none of these strings appear anywhere in the tree: "ONLINE MODE", "Offline", "this build", "not available", "coming soon", "Credits", "PREVIEW". A unit test loads a JSON history containing a legacy `preview`/`offline` row without throwing.

**M2. Core job end to end, with real sizes.**
- The composer offers prompt, optional "avoid" text (negative prompt), a style and an **aspect**: Square 512, Square 768, Portrait 9:16 (576×1024), Landscape 16:9 (1024×576). Only these four sizes; each was verified above. Rename `ResolutionPreset` labels to the aspect name plus real pixel size.
- Every visible control does something. Generate → image → auto-saved to the gallery with prompt, style, size, seed, timestamp and source URL (already in `GenerationRecord`).
- *Test:* contract test for `PollinationsImageGenerationService.uriFor` with each of the four sizes (asserting `width`/`height`/`seed`/`safe=true`/`private=true`). A studio flow test with a fake client: generate → record appears in gallery.

**M3. Signature feature: Seed Lock & Proof Sheets (implemented, not claimed).**
- **Data model:** add `threadId` (nullable), `parentId` (nullable) and `seedLocked` (bool) to `GenerationRecord`, with backward-compatible `fromJson` (missing → null/false).
- **Lock:** a "Lock composition" toggle on the result. When it is on, the next Generate reuses `record.seed` (via the existing `uriFor(request, seed)` seam; the Random draw is skipped). The new record gets the same `threadId` and `parentId` = previous record. The lock state shows in the composer as a visible chip with the seed in mono type ("Seed 0x1A2B…, locked"). Tapping the chip unlocks.
- **Proof Sheet screen:** opened from any record that has a thread. It shows a horizontal contact strip of versions (oldest → newest). Picking two versions (default: the latest and its parent) opens a **compare view** with a draggable vertical divider over the two images, plus a **word diff** of the two prompts (token diff on whitespace and commas; added = accent underline, removed = strikethrough). The same image under the same prompt is labelled "Identical render": same seed and same prompt is deterministic, as measured above.
- **Export:** "Export sheet" composes on the device, using `dart:ui` `PictureRecorder`, a single PNG: thumbnails in order, each with its prompt diff against the previous version, plus the seed and size. It is handed to `MediaSaver.share`. "Save to Photos" uses the existing add-only path.
- **Branching:** "Branch from here" on any version starts a new thread that keeps the seed and has the chosen version as parent.
- *Tests:* unit test, generation with `seedLocked` passes the parent's seed into `uriFor` (fake Random asserting it is **not** called). Unit test, prompt word diff (added, removed, unchanged, punctuation, empty). Unit test, record JSON round trip with and without thread fields. Widget test, lock → generate twice (fake client) → Proof Sheet shows 2 versions, compare view renders, diff shows the changed word. Widget test, export calls `MediaSaver.share` with a non-empty PNG (check the PNG magic bytes).

**M4. Depth: find, keep, share.**
- **Gallery:** text search over prompts (case-insensitive substring) and filter chips for **Style**, **Aspect**, **Proof Sheets only** and **Starred**. Add a star toggle on the detail screen: favourites are now real because the user sets them, which removes the reason `gallery_screen.dart:16-19` gave for dropping them. Filter chips appear only when they can match something (keep the existing `availableGalleryFilters` principle).
- **Detail screen:** "Copy prompt" and "Copy seed" (clipboard) alongside the existing Save / Share / Reuse / Delete.
- **Draft persistence:** the composer's prompt, avoid-text, style, aspect and lock state survive an app restart (key-value store, `ags_draft`).
- **Retention:** keep the 200-entry cap (`history_repository.dart` `maxEntries`). The oldest records are evicted, but never a record that is starred or belongs to a Proof Sheet. Show the count "N of 200 kept" in Settings.
- *Tests:* search/filter unit tests; draft round trip; eviction skips starred and thread records.

**M5. Honest empty, error and offline states.**
- **Offline:** a `SocketException`/`ClientException` from the request shows "You're offline. Your prompt is kept; the gallery and Proof Sheets still work." The gallery, detail, compare and export all work with no network (all on-device).
- **Rate limit (402/429):** the failure card says the free service needs a pause between images. It shows a **visible 30-second countdown** on the Retry button, and Retry is enabled when it ends. There is no automatic retry and no substitute image.
- **Upstream failure (5xx):** "Pollinations.ai is overloaded right now. Try again in a minute." Detect it by status code; the 500 body seen today contains "rate limit".
- **Content filter:** `safe=true` stays on.
- **Empty states:** an empty gallery shows "No images yet. Your first render will be kept here with its prompt and seed." An empty Proof Sheets filter explains how to lock a seed. These are explanations, not fake examples.
- Remove the `failureUnsupported` string ("not available in this build"); with one backend it cannot occur.
- *Tests:* fake client throwing `SocketException` → offline card, prompt preserved. 402 → countdown visible, Retry disabled then enabled (use `tester.pump(Duration(seconds: 30))`). 500 → overload copy.

**M6. Own identity (concrete; differs from every sibling).**
- **Theme: light "proof paper" by default, with its own dark variant.** This deliberately leaves the portfolio's near-black/neon look.
  - Seed colour **vermilion `#E4572E`**: primary, the lock chip, diff "added" underline.
  - Paper background **`#F4EFE6`**, ink text **`#1C1B19`**, secondary **ultramarine `#2B3A8C`**: compare divider, links.
  - Dark variant: background `#1C1B19`, surface `#2A2825`, text `#F4EFE6`, the same vermilion. It follows the system setting; remove `themeMode: ThemeMode.dark`.
  - Remove `00F5FF`, `C724FF`, `0A0B14` and Tailwind `F59E0B` from `lib/`.
  - grep across `/Users/spatchava/agl/*/` Dart found none of `E4572E`, `F4EFE6`, `1C1B19` or `2B3A8C` in any other app.
- **Typography:** bundle **Fraunces** (variable, display/headings; `google/fonts/ofl/fraunces`) and **IBM Plex Mono** (seed values, prompt diff, sizes; `google/fonts/ofl/ibmplexmono`) as assets with their `OFL.txt`. Both files and licences were fetched with HTTP 200, and both are SIL OFL 1.1 per the OFL.txt headers. Body text stays the platform font (SF / Roboto). No `google_fonts` runtime download. grep found neither family in any other app's `pubspec.yaml` or Dart.
- **Shape language:** "print" corners. Images and cards use radius **4**; chips are square-cornered with a 1 px ink outline. This replaces the portfolio-wide 12/14/16 radii in `theme.dart`.
- **Home layout: no 4-tab NavigationBar.**
  - The root screen *is* the studio. Your most recent image or Proof Sheet fills the top as a large print with a paper border. The composer is docked at the bottom like a message bar: prompt field, then a row with the style picker, aspect picker and lock chip, then Generate.
  - The gallery ("Prints") and Settings open from two app-bar actions.
  - On iOS, use `CupertinoIcons` and Cupertino-adaptive controls: `CupertinoSlidingSegmentedControl` for aspect, `Switch.adaptive`, `showCupertinoModalPopup` for the style picker. Material stays on Android.
  - Remove the Home tab and its feature cards (`home_screen.dart`). Tablet: the composer sits beside the print rather than under it (re-use the `Breakpoints` logic).
- **Ads placement (keeps agl_ads; this is not a money decision because no unit or budget changes):** the banner moves out of the shell. It sits **at the foot of the Prints (gallery) screen** and under the result on the studio screen when the keyboard is closed, in layout flow, never over the composer. It is never on Settings, detail or compare. `AglAds.onTransition()` fires when Prints opens. If the founder wants the current ad surface kept exactly, see founder questions.
- **Onboarding (first launch only, 3 short screens, skippable):**
  1. "Write it. See it." Prompt → image, and a statement that images come from Pollinations.ai, a free public model, with its small logo on each image.
  2. "Lock the composition": an animated diagram, not fake output, of the same seed with one changed word.
  3. "Everything stays on this phone": gallery, no account. Ends by focusing the prompt field.

  The flag is stored in `ags_onboarded`. Settings has "Show introduction again".
- **Settings copy is its own:** sections "Images" (source: Pollinations.ai, sizes, the pause between renders, the 200-print limit), "Language", "Your prints" (delete all), "About" (privacy policy, privacy choices). Replace the "Image backend / Configured / Pollinations.ai" status card and the `backendNotConfiguredBody` copy.
- **Name on the home screen:** see founder questions (the "AG" prefix). Until that is decided, keep "AGStudio" and replace the in-app "AG" monogram tile (`home_screen.dart:74-89`) with the new icon artwork.
- **Icon:** a new icon that does not come from `generate_app_icons.py`. Motif: a contact-sheet frame of 2×2 prints, one print marked by a vermilion lock tick, on paper `#F4EFE6`; no Material glyph and no diagonal gradient. Remove the `"AGStudio"` entry from the DESIGN table only if store-compliance/whoever owns that script agrees; the app repo's `AppIcon.appiconset` and Android mipmaps are replaced either way.
- **Splash:** replace the shared `LaunchScreen.storyboard` (shasum `3f6a9b27…`) with a paper `#F4EFE6` background and the new mark. After the change its shasum must differ from `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`. Set Android `launch_background.xml` to match.
- *Tests:* a theme test asserting `colorScheme.primary == Color(0xFFE4572E)`, the scaffold background `0xFFF4EFE6` in light, and that the text theme's display family is `Fraunces`. A shell test asserting there is no `NavigationBar` and that `AglAdBanner` is absent on Settings. An onboarding test: shown on first launch, not on second.

**M7. Proven.**
- `flutter analyze` is clean and `flutter test` passes, with all new tests above.
- Update `l10n_coverage_test.dart`: new keys are present in all 12 ARBs (machine translation is acceptable for non-English, as now; English is authoritative).
- Update `integration_test/store_screenshots_test.dart` for the new screens (see Store impact).
- Commit path-limited (never `git add -A`; `fastlane/**` and `ios/Podfile.lock` carry others' edits) and push to `main`.
- Launch on the iOS simulator and screenshot the studio, a Proof Sheet compare and the Prints screen. Green tests have missed a white screen before.

### SHOULD (do if time allows; not required for Apple)

- **S1.** "Try the other style": from a locked version, render the same prompt and seed in a second style and add it to the sheet as a sibling, so the style is the only variable.
- **S2.** A prompt-history picker in the composer: recent prompts from your own gallery, searchable.
- **S3.** Long-press a print in Prints → Cupertino context menu (iOS) or bottom sheet (Android) with Star / Share / Branch / Delete.
- **S4.** Export the sheet's prompts and seeds as plain text (for pasting into notes).
- **S5.** Haptic tick on lock/unlock (iOS `HapticFeedback.selectionClick`).

## 4. Data source

| Data | Source | Verified |
|---|---|---|
| Generated images | `https://image.pollinations.ai/prompt/{prompt}?width&height&seed&safe=true&private=true`, keyless | curl 2026-10-12: HTTP 200 `image/jpeg` for 512², 576×1024, 1024×576. Determinism for same seed+prompt (identical shasum). 402/500 behaviour captured above. |
| Available model | `https://image.pollinations.ai/models` | returns `["sana"]` (2026-10-12) |
| Gallery, threads, stars, drafts, settings | on-device (`shared_preferences` index + documents-dir files, existing `HistoryRepository`/`DocumentsImageFileStore`) | existing code, existing tests |
| Fonts | bundled assets from google/fonts (OFL) | HTTP 200 for both OFL.txt and the directory listings |
| Supabase | **not used**. No account is needed; adding one would recreate the shared sign-in tell. | n/a |

No fake prompts, images, ratings or user counts anywhere. Style names and onboarding diagrams are our own UI content, not data.

## 5. Store impact (proposed; store-compliance applies these, and this spec does not edit store files)

**Copy (`store/apps/AGStudio.json`, `copy.en`):**
- *subtitle:* "Lock the seed, change the words". Current: "Prompt to picture".
- *short_description (Play):* "Write a prompt, lock its composition, and compare versions word by word."
- *description (draft; does not open with the app name; no ALL-CAPS headings; no "only app" claims):*
  > Change one word in a prompt and most image generators hand you a completely different picture. Here you can lock the composition of an image you like, then edit the words and see what only those words changed.
  >
  > Write what you want to see, pick a style and a shape (square, 9:16 portrait for wallpapers and stories, or 16:9 landscape), and render it. Every image is kept on your phone with the exact prompt, style, size and seed that made it.
  >
  > Lock a result and keep refining. Each locked series becomes a proof sheet: drag a divider between any two versions, see the words you added and removed, branch from any step, and export the whole sheet as one image to share.
  >
  > Search your prints by what you wrote, filter by style or shape, star favourites, and copy any prompt or seed. No account, no sign-up; your gallery stays on this device.
  >
  > Images are made by Pollinations.ai, a free public image model, from your prompt. They carry a small Pollinations logo, and the free service needs a short pause between images.
  >
  > Ads by Google AdMob appear on the gallery and under results; where the law requires it you are asked for consent first, and you can change it in Settings. Google may use device identifiers to serve and measure ads; this app does not track you across other companies' apps or websites.
- *keywords:* "prompt,seed,text to image,compare,proof sheet,iterate,concept art,ai art,wallpaper"
- **Screenshots to retake (all 4 iPhone 6.9", 4 iPad 13", 4 Play phone, 4 Play tablet):**
  1. the studio with a real print and the docked composer,
  2. the lock chip with seed visible,
  3. compare view with the divider and the word diff (two real renders of the same seed),
  4. Prints with search and filters,
  5. an exported proof sheet.

  All images must be real Pollinations renders made at capture time (the existing `f47a493b` script approach). The current screenshot files under `mobile/fastlane/` carry someone else's uncommitted edits, so coordinate before overwriting them.
- **Play feature graphic:** replace the "AG" monogram graphic (`featureGraphic.png`) with paper background, the new mark, and a real two-version compare strip.
- **Review notes (rewrite, per app, no skeleton):** begin with what to try in 60 seconds:
  1. type "a lighthouse at dusk, watercolor", tap Generate;
  2. tap "Lock composition";
  3. change "dusk" to "dawn", Generate again (wait about 30 s, a Pollinations free-tier limit, stated plainly);
  4. open the Proof Sheet, drag the divider, tap Export.

  State: no login, no account, no feature flags, no remote configuration that changes features, the same features in every region. Every screen is reachable from the first screen via the app bar. Name Pollinations.ai, Firebase and AdMob as now. **Remove** the simulator/emulator testing paragraph unless a physical-device run actually happened; if one did, name the device and iOS version. "Intended audience": "People who iterate on image prompts (illustrators, game and tabletop designers, writers) and want to change wording without losing a composition they like."
- **Privacy label (`store/privacy/AGStudio.json`) and Play data safety:** add **Other User Content (prompt text)**, purpose App Functionality, not linked to you, sent to Pollinations.ai. Whether it counts as "collected" depends on Pollinations' retention; see founder questions. Keep the existing ads/crash/analytics/performance entries.
- **Category:** stays PHOTO_AND_VIDEO. Graphics & Design is the alternative; see founder questions.

## 6. Out of scope

- Any accounts, sign-in, Supabase, cloud sync or a community feed.
- Paid models, API keys, HD upscaling, sizes above the measured ~768² cap, image-to-image or inpainting (Pollinations' keyless endpoint was not verified for these).
- Colour capture, palettes, photo grading or editing, or reading the photo library (Photriya's job, overlap.md G8).
- Video generation.
- Editing `store/apps/*.json`, fastlane metadata or `docs/`, submitting builds or replying to Apple (Charter §1; 5.6 freeze MA-043).
- Changing ad units, frequency caps or AdMob configuration.

## 7. Founder questions

1. **Name.** The "AG" house prefix is a portfolio tell. Do you want a new display/store name? Candidates: "Proofsheet" (no app with that name in the US iTunes Search results on 2026-10-12; that is **not** a trademark search), or "Seedlock". A rename touches the store listing, bundle display name and privacy-policy URL slug.
2. **Ad surface.** M6 moves the banner off the shell onto Prints and under the studio result, with no unit changes. Is reducing banner presence on the studio screen acceptable?
3. **Privacy answer for prompt text.** Pollinations.ai receives every prompt (`private=true` keeps it out of its public feed, but its retention policy is unknown to us). Should the App Store label declare "Other User Content, collected, not linked" (the conservative answer), or "not collected"? This is legal text (Charter §6).
4. **Category.** Keep PHOTO_AND_VIDEO, or move to GRAPHICS_AND_DESIGN, where most text-to-image competitors found via iTunes Search are filed (Wonder, Monet, starryai, Neko AI)?
5. **Reliance on one free third-party service.** The whole app depends on Pollinations.ai's keyless tier. It changed models (now only `sana`) and showed upstream 429s during this session. Do you accept that risk for a store app, or fund a paid backend later (Charter §3)?
