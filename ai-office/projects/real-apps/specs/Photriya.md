# Spec: Photriya, a colour reader that corrects for the light you are standing in

- **Author:** product-manager (AI office), 2026-10-12
- **Repo:** /Users/spatchava/agl/Photriya (app at repo root)
- **base_sha:** `d1c7d49cfb14c2521137db5b315532ec9a48a313`, branch `main`
- **Store state:** Apple rejected it under 4.3/4.2.6 on 2026-10-05T21:25:38Z (`.dist/rejections.json` key `Photriya`, message 1). The same thread also has a **2.1(a) crash on launch** (iPhone 17 Pro Max, iOS 27.0, message 2, 2026-09-29T19:07Z). Google Play: PRODUCTION_DRAFT_STAGED.
- **Baseline, measured at base_sha on 2026-10-12** (run with `--no-pub`, so `pubspec.lock` stayed unchanged: shasum `efbac9f1…` before and after):
  - `flutter analyze` reports "No issues found!"
  - `flutter test` reports "+1072: All tests passed!"
- **Others' uncommitted work in this repo (do not touch):** `fastlane/**` (description, notes, screenshots modified, `05.png` untracked) and `ios/Runner.xcodeproj/project.pbxproj`. Source: `git status --short`. If removing plugins (M5) would need a pbxproj change, stop and report it. Do not commit that file.

---

## 1. Problem

Photriya has a good core buried inside a kitchen sink. The router has **24 routes** (`lib/core/router/app_router.dart:56-118`). They cover colour capture, palettes and grading, and also:
- a DALL-E playground,
- a GPT "AI Copilot",
- an "Academy" of hard-coded blog posts (including "Pricing Your First Client Shoot", `blogs_screen.dart:66`), quizzes and lessons,
- a collage builder, a watermark studio, frames,
- a portfolio and an analytics screen,
- a photo-library browser,
- a Supabase/Google/Apple sign-in wall.

To a reviewer this looks like a feature-list template and not a product, which is exactly 4.3(b). Several parts are also dishonest or broken.

### What works today (read in code; device behaviour not verified)

- **Live camera colour readout.** `capture_screen.dart:145-231` averages a centre window of each frame and shows HEX/RGB/HSL/CMYK. Harmony, Gradient and Palette modes are derived from the live colour.
- **History.** Search and date filters exist (`history_screen.dart:88-177`).
- **Palette Builder.** Harmonies, sort, CSS copy.
- **Pro tools on the user's own photo:**
  - Histogram, a real per-channel 256-bin histogram (`histogram_screen.dart`).
  - EXIF read with `package:exif` (`exif_viewer_screen.dart:216`).
  - Colour Grading: one 4×5 matrix shared by preview and export (`core/services/color_grade.dart`).
- **Shot Planner.** On-device NOAA-style sun maths (`core/services/sun_calculator.dart`) and optional device location.
- Saving uses `gal` add-only on iOS (`core/services/photo_io.dart:131-145`).

### What is broken, shallow, dishonest or template

| Finding | Evidence |
|---|---|
| **Live capture very likely never produces a colour on iPhone.** The camera is opened with `ImageFormatGroup.yuv420` (`capture_screen.dart:160`). On iOS the pinned `camera_avfoundation` 0.9.19 delivers that format as `kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange` (`~/.pub-cache/.../camera_avfoundation-0.9.19/ios/.../CameraProperties.m:55`), which has **2 planes** (`FLTCam.m:634` `CVPixelBufferGetPlaneCount`). `_centerColorYuv` then returns `null` at `if (image.planes.length < 3) return null;` (`capture_screen.dart:235`). The result: "Waiting for the camera…" forever, and Capture says "No color detected yet". | Source reading. **Not verified on a device**, because no iPhone run was possible here. The core job may be dead on the platform Apple reviews. |
| **Fake "ASE" export.** The "ASE Format" option copies plain text lines of the form `#RRGGBB Name` to the clipboard (`palette_builder_screen.dart:950-952, 997-1002`). Adobe Swatch Exchange is a binary file format. | code |
| **Made-up colour temperature.** `colorTemperature` is `4500 + ((r-b)/g) * -1200` (`core/services/color_utils.dart:73-84`) and is shown as a Kelvin figure for every captured colour. The comment calls it "McCamy's approximation", but it is not McCamy's formula, and correlated colour temperature means nothing for a saturated colour. | code |
| **"AI color naming" claimed; it is not AI.** Onboarding says "AI color naming" (`onboarding_screen.dart:32`). The name actually comes from a hue-bucket `if` chain (`color_utils.dart:88-140`). | code |
| **Mislabelled control.** The capture screen's "Color picker" button (`capture_screen.dart:1228-1232`) navigates to `/playground`, the DALL-E screen. | code |
| **DALL-E playground and GPT copilot need the user's own OpenAI key.** See `core/services/openai_service.dart:15-27` and the Settings "AI Configuration / OpenAI API Key" section (`settings_screen.dart:216-330`). Text-to-image is AGStudio's job (overlap.md G8). | code, `overlap.md:40` |
| **Onboarding is unreachable.** `/onboarding` exists, but nothing routes to it: there is no redirect, and `initialLocation: '/library'` (`app_router.dart:52`). So Settings' "Reset onboarding" (`settings_screen.dart:618-627`) has no effect. | grep: the only `'/onboarding'` reference is the route itself |
| **Sign-in wall that stores nothing.** Supabase/Google/Apple auth (`core/services/auth_service.dart`, 616 lines; `login_screen.dart:515,539,555`: "Sign in with Apple", "Continue with Google", "Continue as Guest") syncs no data: `grep "from('"` in `lib/` finds nothing. Its only effect is to unlock **Analytics** of *local* data behind "Sign in to unlock" (`discover_screen.dart:60-77`). The store notes say "The app opens on a sign-in screen", which the router contradicts. The listing requires the shared `qa@americangroup.ai` demo login. | code, `store/apps/Photriya.json` |
| **"PRO" badge with no purchase path.** `settings.isPremium` drives a PRO badge and ad suspension (`settings_screen.dart:98-110`, `main.dart:141-142`). `lib/` contains no `InAppPurchase` code (grep: no match), yet the Resolution Center reply listed "Apple In-App Purchase — paid features". | grep |
| **Photo-library browser with dead thumbnails.** The Library "Gallery" tab reads the whole photo library through `photo_manager`. Thumbnails have no tap handler: grep for `onTap` in `library_screen.dart:795-980` finds 0. | code |
| **Purpose strings that are not true.** `NSMotionUsageDescription`: "Detects device movement to reduce blur while the shutter is open." No code in `lib/` uses `sensors_plus`. `NSPhotoLibraryUsageDescription` mentions "AI Playground transformations" (`ios/Runner/Info.plist:67-68, 312-313`). Android requests `READ_MEDIA_VIDEO` (`AndroidManifest.xml:18`). | grep |
| Template tells | <ul><li>Supabase sign-in family.</li><li>`themeMode: ThemeMode.dark` (`main.dart:159`), obsidian `#050508` + violet `#7C5CFC` (26 uses) + cyan `#00D4FF` (18 uses) + gold neon look.</li><li>`fontFamily: 'Inter'` 65 times and `'JetBrainsMono'` twice, but `assets/fonts/` is **empty** and `pubspec.yaml` has no `fonts:` block, so these fall back to the system font.</li><li>Floating 5-tab bar with `AglAdBanner` directly above it (`core/shell/main_shell.dart:96-110`).</li><li>"AI Assistant" tile (`discover_screen.dart:47`), "Get Started" (`onboarding_screen.dart:281`), "Welcome back" (`discover_screen.dart:206`), "One app. Two experiences." hero.</li><li>Privacy label byte-identical to iMeasure's (`store/privacy/Photriya.json` and `iMeasure.json` both shasum `9f77afb4…`), declaring email, name, user ID and purchase history.</li><li>Review notes use the shared "2. DEVICES…" skeleton, with simulator-only testing claims.</li></ul> |

Measured non-tells: the iOS LaunchScreen.storyboard is **not** the shared one (shasum `005c63ab…`, not `3f6a9b27…`), and the icon is not from `generate_app_icons.py`. It is a custom aperture with colour wedges (`assets/icons/icon_1024.png`, identical to the iOS 1024 icon: shasum `1aa2e796…`). It is still drawn in the neon-on-near-black palette.

## 2. User and honest product

**User:** a designer or maker who needs the real colour of a physical thing: a fabric, a paint chip, a printed brand sample, a wall, a product, a flower they want in a palette. Photographers are the secondary user: they want the colour of the light and a palette from a scene.

**Their problem:** every camera colour picker reports the colour *as lit*. A white wall reads orange under a living-room bulb and blue in shade, so the HEX they copy is wrong, and the same object gives a different value in every room.

**Core job (one thing, done well):** point the camera at something, or open a photo, and get a trustworthy colour. Keep it in a swatchbook, build palettes from it, and export it in the formats design tools actually open.

**Signature feature: Paper-White Correction.**
1. Put any sheet of white paper (or a grey card) in the frame and tap it. Photriya samples the paper and the target **from the same camera frame**, so automatic white balance cannot drift between the two readings.
2. It estimates the light (an approximate colour temperature, with a "this isn't white under this light" check).
3. It shows the colour two ways: **as seen** and **corrected to neutral light**, plus the ΔE2000 distance between them ("the light shifted this colour by ΔE 7.4").
4. The same correction works on a photo: tap something white in it. Applied to the whole photo, the correction becomes the white-balance stage of the existing Colour Grading matrix.

**Why this is the honest angle (evidence and limits):** web search is disabled in this environment; the WebSearch hook returned "Internet mode is not enabled". On 2026-10-12 I queried Apple's keyless iTunes Search/Lookup API instead:
- **Adobe Capture** (id 1040200189, 24,310 ratings, Graphics & Design). Its description advertises colour themes from the camera **and "Looks"**: "Collect light and hue to turn into beautiful color grading profiles… transfer that feel to use in your photos". So a "match a look" signature would **not** be distinct. Its description has no mention of white balance, a reference or calibration (0 matches for "white balance", "grey/gray card", "calibrat").
- **Pantone Connect** (1491023737). It says it "calibrates your iOS device's camera for color measurement" **only "when paired with the Color Match Card from Pantone"**, a separate physical product. We do not know whether that card costs money; the description says "order one".
- **Coolors** (956480678, 10,611 ratings). Its description mentions palettes, with 0 matches for "reference", "white balance" or "calibrat".
- **Color Identifier: Color Picker** (1641085395). 0 matches for any of those terms.

These results show only what the competitors **advertise**. **Whether their apps lack a paper-reference correction: competitor not verified.** The store copy must not say "only app". It describes what Photriya does, with no card to buy.

**Honesty limits the app must state in the UI.** Correction is *relative to your reference*. The phone's tone curve, optical brighteners in paper and mixed light all limit accuracy. This is not a spectrophotometer, and Photriya does not match to Pantone or any proprietary colour system.

**Portfolio boundary:**
- Photriya owns colour capture, palettes, colour grading, histogram, EXIF and the shot planner.
- It drops text-to-image (AGStudio's job, overlap.md G8).
- It must **not** find duplicate photos or browse/clean the photo library (AGCleaner's job). The photo-library browser goes.
- The AI copilot goes (M5). It cannot be justified against the colour job: it needs a user-supplied paid key, and the signature feature needs no AI.

## 3. Acceptance criteria

### MUST (what Apple needs to see a real, distinct app)

**M1. Core capture works on an iPhone.**
- Fix the frame format. Either request `ImageFormatGroup.bgra8888` on iOS (keep `yuv420` on Android), or support 2-plane NV12 (interleaved CbCr in `planes[1]`) in the YUV sampler. Extract the samplers into a pure function, `sampleRgb(CameraImageLike, Offset centreNorm, double radiusNorm)`, so it can be unit tested without a camera.
- Add sampling at an **arbitrary** normalised point (needed for M2). The point mapping from preview coordinates to sensor coordinates must account for `sensorOrientation` (90/270) and front/back lens; put it in a pure function `previewToSensor(...)`.
- Capture saves a swatch to the Swatchbook (Hive `captures` box). The confirmation appears only after `saveCapture` completes.
- *Tests:*
  - 3-plane I420 and 2-plane NV12 fixtures of a known solid colour (e.g. Y/U/V for sRGB 200,80,40) return that colour within ±3 per channel.
  - A BGRA fixture does the same.
  - `previewToSensor` maps the four corners correctly for orientations 0/90/180/270.
  - A widget test with a fake camera stream shows the readout and saves one capture.
- *Device proof:* the developer launches a **release** build on a physical iPhone if one is attached to this Mac, and screenshots a live readout. If no device is available, write "not verified on device" in the commit/report. Never claim otherwise.

**M2. Signature feature: Paper-White Correction (implemented, not claimed).**
- **New pure module `lib/core/color/reference_correction.dart`:**
  - sRGB ⇄ linear (IEC 61966-2-1).
  - linear sRGB → XYZ (D65) → xy and CIELAB.
  - **Correction:** `corrected_lin[c] = clamp(target_lin[c] / ref_lin[c] × 0.9)`, so the paper maps to linear 0.9 (about L* 96) on every channel and the reading does not depend on exposure. If any channel exceeds 1 before the clamp, set `brighterThanReference = true`.
  - **Light estimate:** McCamy CCT from the reference's xy. Duv from the distance in CIE 1960 uv to the Planckian locus (Krystek 1985 approximation) at that CCT.
  - **Reference quality:** `tooBright` (any raw channel ≥ 250), `tooDark` (reference luminance Y < 0.05), `notNeutral` (|Duv| > 0.02), else `ok`.
  - **ΔE2000** (CIEDE2000) between as-seen and corrected.
- **Camera UI:**
  - A "Set paper white" chip. Tapping it, then tapping the paper in the preview, places a small **W** ring there; both points are then sampled every frame.
  - The readout shows two chips side by side, **As seen** and **Corrected**, with values in mono type, then "Light ≈ 3,100 K · warm" and "ΔE 7.4 from as-seen".
  - Reference warnings in plain words: "Paper is overexposed — tilt it out of direct light", "Too dark to use as white", "This doesn't look white under this light — is it white paper?", "This colour is brighter than your paper — correction can't go above white".
  - The W ring stays until it is cleared. Clearing returns the readout to as-seen only.
- **Photo UI (see M4):** a "Tap something white" mode does the same on a picked photo, with both samples taken from the decoded bitmap.
- **Data model** (Hive, backward compatible, new nullable fields with new `@HiveField` indices, regenerate `color_capture.g.dart`):
  - `seenValue` (int ARGB),
  - `referenceValue` (int?),
  - `lightKelvin` (double?),
  - `referenceQuality` (String?),
  - `deltaE` (double?).

  `colorValue` stores the corrected colour when a reference was used, and the as-seen colour otherwise. Old records load with the new fields null.
- **Replace the fake temperature.** Delete the `4500 + n * -1200` formula. Kelvin is shown **only for a reference (the light)**, never for a saturated object colour. Object colours instead show "warm / neutral / cool" from the sign of Lab b* and a*, plus their Lab values.
- *Tests* (pure unit tests, no device):
  - sRGB (255,255,255) → xy ≈ (0.3127, 0.3290) ± 0.001, and McCamy ≈ 6,500 K ± 100.
  - A warm reference, e.g. sRGB (255,197,143), gives CCT < 4,000 K.
  - A target equal to the reference gives a corrected value ≈ sRGB (243,243,243) (linear 0.9) ± 2.
  - A target brighter than the reference sets `brighterThanReference`.
  - The `tooBright` / `tooDark` / `notNeutral` classifications.
  - **ΔE2000 against Sharma, Wu & Dalal (2005) test pairs 1, 7, 17 and 34** (pair 1: Lab(50, 2.6772, −79.7751) vs (50, 0, −82.7485) gives 2.0425), within 1e-4.
  - Hive round trip: a legacy record without the new fields loads.
  - Widget test: with a fake frame source supplying a warm reference and a target, the screen shows both chips, a Kelvin estimate and a ΔE, and Capture persists `referenceValue` and `deltaE`.

**M3. Depth: Swatchbook, palettes from photos, real exports.**
- **Swatchbook** (replaces Library, History, Portfolio and Analytics as one screen):
  - every saved swatch and palette, newest first;
  - text search over name/HEX/notes (existing `searchQueryProvider` logic);
  - filter chips: **Corrected**, **Camera**, **Photo**, **Starred**, and palettes vs swatches; the date chips from History may stay as a sort/section header;
  - a star toggle, an editable note per swatch, swipe-to-delete with undo.
- **Palette from a photo, on-device:** k-means in CIELAB (k = 5 by default, 3–8 adjustable, k-means++ with a fixed seed so results are deterministic), on a ≤ 256 px downsample in an isolate. Each colour stores its **weight** (share of pixels): new nullable `weights` field on `PaletteModel`. Shown as a proportional strip. If the photo has a paper-white reference set, the palette is extracted from corrected pixels, and the palette records that.
- **Exports, as real files through the share sheet** (`share_plus` `XFile`):
  - **`.ase`**: real Adobe Swatch Exchange binary. Signature `ASEF`, version 1.0, a group start/end, colour entries in `RGB ` float32 big-endian, UTF-16BE names.
  - **`.gpl`**: GIMP palette text.
  - **CSS variables** and a **JSON** (hex, rgb, lab, weight, corrected flag).
  - **PNG swatch card**: a chip grid with HEX in mono, and "Corrected for ~3,100 K light" when that applies, rendered with the existing `PhotoIO.render`.

  Clipboard copy of HEX, CSS and the selected format stays. Remove the fake "ASE data copied!" text option.
- *Tests:*
  - ASE bytes: header `41 53 45 46 00 01 00 00`, block count, and one RGB entry decoded back to the same floats.
  - GPL text format.
  - k-means on a synthetic image of 3 solid colour regions (60/30/10 %) returns those 3 colours ± ΔE 2, with weights ± 0.02, and is deterministic across two runs.
  - Swatchbook search and each filter.
  - Note editing persists across a provider restart.
  - Legacy `PaletteModel` without `weights` loads.

**M4. One photo bench instead of scattered tools.**
- "Open photo" (system picker via `image_picker`; no library-read permission) opens a **Photo** screen for that one photo, with segments:
  1. **Colours**: tap to sample with a loupe, plus "Tap something white" (M2), the extracted palette (M3) and "Save palette".
  2. **Grade**: the existing `ColorGrade`, plus a new first stage, **Neutralise from paper white**. This is a diagonal gain matrix built from the reference, so preview and export stay one `ColorFilter.matrix`. Show a live histogram of the *graded* result under the photo, reusing `HistogramResult.fromImage` on a downsampled render.
  3. **Histogram**: the existing implementation.
  4. **Info**: the existing EXIF reader. Keep "Photo has no EXIF data" as an honest state.
- The standalone `/histogram`, `/exif` and `/color-grading` routes become this one screen. Keep their logic and tests, and adapt the tests to the new host widget rather than deleting them.
- **Shot Planner** stays as is, reachable from the home app bar ("Light"), restyled to M7. It is the only screen that may ask for location, and only after "Use my location" is tapped (current behaviour).
- *Tests:*
  - Neutralise: a photo fixture with a 3,000 K-tinted white patch gives that patch R≈G≈B (± 4) after the gain matrix.
  - Graded histogram changes when exposure changes.
  - Picking a photo with no EXIF shows the empty state.
  - The save path still reports success only after `SaveResult.saved` (the existing pattern in `photo_io.dart`).

**M5. Remove what isn't this app, and every dishonest line.**
- **Delete** (code, routes, providers, strings and their tests; deleting a test is allowed only together with the code it covers, and the commit must say so):
  - `features/playground`, `features/ai_assistant`, `core/services/openai_service.dart`, the Settings "AI Configuration" section, and the `openAiApiKey`/`preferredAiModel` settings;
  - `features/academy` (hub, blogs, quizzes, contact; support email stays in Settings) and `features/learn`;
  - `features/discover` (the "One app. Two experiences." hub), `features/portfolio`, `features/analytics`;
  - `features/collage`, `features/watermark`, `features/frames`;
  - the Library photo-browser tab and `GalleryNotifier`;
  - all sign-in: `features/auth/**`, `core/services/auth_service.dart`, `core/providers/auth_provider.dart`, `core/services/supabase_config.dart`, `app_env.dart`, `Supabase.initialize` and `AppEnv.validate` in `main.dart`;
  - the `isPremium` flag and PRO badge (and the `AglAds.setSuspended(isPremium)` call, since nobody can become premium);
  - the onboarding slides about DALL-E and "AI color naming".
- **Dependencies to drop** from `pubspec.yaml` once unused: `supabase_flutter`, `google_sign_in`, `sign_in_with_apple`, `firebase_auth`, `in_app_purchase`, `dio`, `video_player`, `chewie`, `sensors_plus`, `flutter_speed_dial`, `animated_text_kit`, `lottie`.
  - Do not remove `firebase_core`; agl_observability may need it, so verify with `flutter pub deps`.
  - If `flutter pub get` changes `ios/Podfile.lock` or the pbxproj, see the header note.
  - Remove `com.apple.developer.applesignin` from `Runner.entitlements`; signing tolerates an unused capability in the profile.
- **Purpose strings and permissions:**
  - Delete `NSMotionUsageDescription` and `NSPhotoLibraryUsageDescription` (the picker needs neither; saving uses add-only).
  - Reword `NSCameraUsageDescription`, e.g. "Photriya reads colours from the camera view. Nothing is recorded or uploaded."
  - Android: remove `READ_MEDIA_VIDEO`, `READ_MEDIA_IMAGES`, `READ_MEDIA_VISUAL_USER_SELECTED` and `READ_EXTERNAL_STORAGE`, and save via `gal` on Android too (gal supports it), so `photo_manager` can go.
  - Keep `CAMERA` and location.
- **Copy fixes:** the "Color picker" button is removed (Palette Builder is reached from a swatch's "Build palette" action). The colour name is labelled "approximate name", never "AI".
- *Tests:*
  - A "no residue" test greps `lib/` for `openai`, `dall`, `DALL`, `Sign in with Apple`, `Continue with Google`, `Continue as Guest`, `Welcome back`, `Get Started`, `AI Assistant`, `Academy`, `isPremium`, `this build`, `coming soon` and asserts no matches.
  - A router test asserts the route set is exactly: home, camera, photo, palette builder, shot planner, settings, onboarding.
  - A plist test asserts the motion and library-read keys are absent.

**M6. Honest states, end to end.**
- **Camera permission denied:** an explanation and an "Open Settings" button (existing), plus "Open a photo instead".
- **No camera** (simulator, some iPads): "This device has no camera. Open a photo to read colours." with an Open-photo button. Never a frozen grey readout.
- **First frame not yet arrived:** a spinner for at most 3 s, then "The camera isn't sending frames. Close and reopen." (with a retry).
- **Empty Swatchbook:** "Nothing saved yet. Read a colour with the camera or open a photo. Tip: bring a sheet of white paper." This is the only empty-state copy; no sample swatches are seeded.
- **Storage unavailable** (`StorageService.isInitialized == false`): a banner saying saving is unavailable this session. Reading colours still works.
- **Offline:** the app needs no network at all except for ads. Settings → About states "Works offline. Nothing you capture leaves this phone." Ads simply don't fill.
- *Tests:* a widget test for each state above, using fakes for the camera availability, storage and picker results.

**M7. Own identity (concrete; different from every sibling).**
- **Theme: a neutral "viewing booth" grey**, chosen because judging colour needs a neutral surround. It replaces obsidian, violet, cyan and gold. The theme follows the system setting; remove `themeMode: ThemeMode.dark`.

  | Role | Light | Dark |
  |---|---|---|
  | Background | `#ECECEA` | `#181817` |
  | Surface | `#F8F8F7` | `#252524` |
  | Ink (text) | `#1B1B1A` | `#ECECEA` |
  | Secondary text | `#5A5A5A` | `#9A9A98` |
  | Hairlines | `#767676` (≈ 18 % grey) | — |
  | Single accent | `#C8186E` ("loupe magenta": primary buttons, the W ring outline, the active filter) | `#E2509A` |

  Computed contrast ratios: ink on background 14.57:1. Secondary text 5.83:1. Accent `#C8186E` on background 4.66:1. White on accent 5.51:1. Dark accent `#E2509A` on `#181817` 4.95:1.

  No gradients and no glow; delete `GlassCard` and `GradientButton` usage. Remove `#050508`, `#7C5CFC`, `#00D4FF`, `#D4A843`, `#FF4D6D` and `#00E676` from `lib/`.

  Uniqueness: grep across every `*/lib/**/*.dart` under /Users/spatchava/agl and all files in `specs/` found none of `C8186E`, `E2509A`, `ECECEA`, `F8F8F7`, `181817`, `252524`, `1B1B1A`, `5A5A5A`, `767676` or `9A9A98`.
- **Typography:** bundle as assets, each with its `OFL.txt`. Both families were fetched from google/fonts with HTTP 200, and both OFL.txt headers say SIL OFL 1.1.
  - **Archivo** variable (`ofl/archivo/Archivo[wdth,wght].ttf`) for UI and headings. Display uses `FontVariation('wdth', 112)` with `wght` 700; body uses the default instance.
  - **Fragment Mono** (`ofl/fragmentmono/FragmentMono-Regular.ttf`) for every HEX/RGB/Lab/K/ΔE value.

  Delete every `fontFamily: 'Inter'`, `'JetBrainsMono'` and `'monospace'`, and drop `google_fonts` if unused. Neither family appears in any other spec in `specs/` (grep), nor in any other app's `pubspec.yaml`.
- **Shape language:** swatches are **paint chips**: rectangles with radius 2 and a 1 px `#767676` hairline. Buttons are pill-free rectangles with radius 6. The camera reticle is a thin circular loupe; the W reference marker is a ring with a "W". Replace the 12/16/24/xxl radii in `app_theme.dart`.
- **Home layout: no bottom NavigationBar and no floating tab bar.**
  - The root screen is the **Swatchbook**: a large title, then a search field, then filter chips, then a list of palettes as proportional chip strips mixed with single swatches.
  - Pinned at the bottom centre is a large circular **shutter** button ("Read colour") with an "Open photo" button beside it.
  - The app bar has "Light" (Shot Planner) and Settings.
  - On iOS use `CupertinoIcons`, `CupertinoSlidingSegmentedControl` for the Photo segments, `Switch.adaptive`, and `showCupertinoModalPopup` for export choices. Material stays on Android.
  - On tablet/foldable the Swatchbook list and the selected swatch/palette detail sit side by side (keep the foldable tests passing).
- **Ads** (keeps `agl_ads`, with no unit or frequency change): the banner moves out of the shell to the **foot of the Swatchbook list**, in layout flow, never over the shutter. It never appears on the camera, photo, palette builder, shot planner, onboarding or settings screens. `AglAds.onTransition()` fires when the user returns to the Swatchbook from the Photo screen; agl_ads applies its caps.
- **Onboarding** (first launch only, 3 screens, skippable, made reachable via a first-launch check of `ph_onboarded`, with "Show introduction again" in Settings working):
  1. "Colour changes with the light": a static diagram of one chip under warm and cool light.
  2. "Bring a sheet of white paper": tap it, and Photriya corrects for the light.
  3. "Everything stays on this phone": no account, works offline.

  The last button is "Read a colour", which opens the camera, and only then asks for camera permission. No "Get started".
- **Settings, in its own words:**
  - *Reading* (copy format HEX/RGB/HSL/Lab, show approximate names, haptics),
  - *Export* (default palette format),
  - *Language* (shared picker allowed),
  - *Your swatches* (count, delete all),
  - *About* (version, "Works offline…", support email, privacy policy, terms, **Privacy choices**: legally required for ads, stays).

  No account section.
- **Icon and splash** (the icon is not from `generate_app_icons.py`, but it uses the neon palette):
  - New icon: a single paint chip in `#C8186E` overlapping a paper-white card, with a thin loupe ring, on `#ECECEA`. No aperture wedges, no gradient, no Material glyph.
  - Splash background `#ECECEA` with the new mark: update `flutter_native_splash` colours in `pubspec.yaml` (currently `#0A0A0F`) and regenerate.
  - The storyboard background must no longer be white `1,1,1`.
- *Tests:*
  - Theme: `colorScheme.primary == Color(0xFFC8186E)` in light, background `0xFFECECEA`, display family `Archivo`, mono style family `FragmentMono`.
  - Shell: no `NavigationBar`, and `AglAdBanner` is present only on the Swatchbook.
  - Onboarding: shown on first launch, not on second, and shown again after "Show introduction again".
  - `pubspec.yaml` declares both font assets, and the files exist.

**M8. Proven.**
- `flutter analyze` is clean and `flutter test` passes, with every test named above. Existing tests that assert removed behaviour are updated where the behaviour changed (e.g. `color_utils_test` on temperature). They are deleted only together with deleted code, and never skipped.
- `l10n`/`i18n_test.dart` passes for new strings: English is authoritative, and other locales follow the current practice in `agl_i18n`.
- Update `integration_test/store_screenshots_test.dart` to the new screens. It must not sign in; the QA account is no longer used.
- Commit path-limited: never `git add -A`. `fastlane/**` and `project.pbxproj` carry others' edits. Push to `main`.
- Launch on the iOS simulator and screenshot onboarding, the empty Swatchbook, the Photo screen with a reference and a palette, and Settings. Green tests have missed a white screen before. Also launch a release build there to rule out the start-up path behind the 2.1(a) crash. **The crash log itself is not on this machine** (no Photriya crash file in `/Users/spatchava/agl/.dist`), so the root cause is **not verified**. Removing `Supabase.initialize`/`AppEnv.validate` shrinks the start-up path, but that is not proof the crash is fixed.

### SHOULD (do if time allows; not required for Apple)

- **S1. Match check:** pick any two swatches and see ΔE2000 with a plain verdict: < 1 "indistinguishable", 1–2 "very close", 2–5 "noticeable side by side", > 5 "different colour". This is for matching paint, yarn or a print to a sample.
- **S2.** Lock exposure while a reference is set (`CameraController.setExposureMode(ExposureMode.locked)`, unlocked on clear) to reduce flicker. The camera plugin exposes no white-balance lock, which is why sampling from the same frame is the core design.
- **S3.** A swatch's "Find in Shot Planner" tip: when the light estimate is below 3,500 K outdoors, show today's golden-hour window. Only show times computed by `SunCalculator`; no claims about colour of light beyond that.
- **S4.** Better colour names from a bundled, openly licensed name list (licence checked and shipped in the app), still labelled "approximate".
- **S5.** Haptic tick when the W reference is placed (iOS `HapticFeedback.selectionClick`).

## 4. Data source

| Data | Source | Verified |
|---|---|---|
| Live colour | camera frames on-device (`camera` plugin image stream) | existing code. iOS plane count read from the pinned plugin source (M1). Device run not verified. |
| Photo colours, palette, histogram, EXIF | the user's picked photo, decoded on-device (`image`, `exif` packages) | existing code and tests |
| Colour science | own pure Dart: IEC 61966-2-1 sRGB, McCamy CCT, Krystek locus, CIEDE2000 with Sharma 2005 test data | unit tests in M2 |
| Sun times | on-device `SunCalculator`; location only on request | existing tests `sun_calculator_test.dart`, `sun_times_test.dart` |
| Swatches, palettes, notes, settings | Hive + shared_preferences on-device (existing `StorageService`) | existing tests |
| Fonts | bundled assets from google/fonts (OFL 1.1) | HTTP 200 for both directories and OFL.txt (2026-10-12) |
| Supabase / any public API | **none**. No account and no network data; the signature feature is fully on-device. | n/a |

No sample swatches, fake palettes, fake ratings, counts or "community" content. Onboarding diagrams are UI artwork, not data.

## 5. Store impact (proposed; store-compliance applies these, and this spec does not edit store files)

**Copy (`store/apps/Photriya.json`, `copy.en`):**
- *subtitle:* "Colour corrected for the light" (30 characters, at Apple's 30-character limit). Current: "Capture & imagine colours".
- *short_description (Play):* "Read real colours with your camera. A sheet of paper corrects for the light."
- *description* (draft; does not open with the app name; no ALL-CAPS headings; no "only app" claim; no AI section):

  > A white wall looks orange under a lamp and blue in the shade, and so does every colour your camera reads. Hold a sheet of white paper in the frame, tap it, and the reading is corrected for the light you are standing in.
  >
  > You see each colour two ways — as the camera saw it and corrected to neutral light — with the difference measured in ΔE, plus an estimate of the light's colour temperature. If the paper is overexposed or the light is too coloured to trust, the app tells you instead of guessing.
  >
  > Open any photo to do the same: tap something white, sample any point, and pull a palette of its main colours with how much of the picture each one covers. Neutralise the photo from the same white, grade it, check its histogram and read its camera data.
  >
  > Everything you keep goes into a swatchbook on your phone. Search it, star favourites, add notes, and export palettes as Adobe Swatch Exchange (.ase), GIMP (.gpl), CSS, JSON or a swatch card image.
  >
  > Planning a shoot? The light planner shows sunrise, sunset, golden hour and blue hour for where you are or any coordinates.
  >
  > Corrections are relative to your reference; it is a careful camera reading, not a lab instrument. No account, works offline, and nothing you capture leaves your phone.
  >
  > Ads by Google AdMob appear at the foot of the swatchbook; where the law requires it you are asked for consent first, and you can change it in Settings › Privacy choices. Google may use device identifiers to serve and measure ads; this app does not track you across other companies' apps or websites.

- *keywords:* "colour picker,color picker,white balance,palette,hex,swatch,ase,paint match,colour temperature"
- *promotional_text:* "Put a sheet of paper in the frame and read the colour as it really is, not as the lamp makes it look."
- *release_notes:* list what changed for users: paper-white correction, the swatchbook, palettes from photos, real .ase/.gpl export, the new look. Also the removals: AI playground and assistant, academy, collage, watermark, frames, accounts.
- **Screenshots to retake** (iPhone 6.9", iPad 13", Play phone and tablet):
  1. the camera with W ring, As seen/Corrected chips and the Kelvin estimate,
  2. the same object without and with correction (two real captures),
  3. the Photo screen with an extracted palette and weights,
  4. the Swatchbook with search and filters,
  5. the export sheet with .ase/.gpl,
  6. the Shot Planner.

  All must come from real captures of real objects at capture time; the simulator has no camera, so shots 1–2 need a device or a photo-based capture. The current screenshot files under `fastlane/` carry someone else's uncommitted edits; coordinate before overwriting them.
- **Play feature graphic:** a new one on `#ECECEA` with the new mark and an as-seen/corrected chip pair.
- **Review notes** (rewrite for this app, no shared skeleton, no "2." numbering):
  - Start with "What to try in 60 seconds (you need a sheet of white paper and any coloured object)":
    1. Tap Read colour and allow the camera.
    2. Tap "Set paper white", then tap the paper in the view.
    3. Point the centre ring at the object and tap the shutter.
    4. Open the swatch to see As seen vs Corrected and ΔE.
    5. Tap Open photo, pick any photo with something white, tap it, and see the palette.
  - State: no account and no login (`demo_account_required: false`; remove `demo_account_name`); no in-app purchases; no feature flags or remote configuration that changes features; the same features in every region; the network is used only for ads and crash/analytics reporting.
  - External services: Firebase Crashlytics/Analytics/Performance and Google AdMob (UMP). **Remove** Supabase, Firebase Auth, Google Sign-In, Sign in with Apple, In-App Purchase and "the app's own endpoints".
  - Testing: **delete the simulator/emulator paragraph** unless a physical-device run actually happened; if it did, name the device and iOS version.
  - *Intended audience:* "Designers and makers who need the real colour of a physical object (fabric, paint, print, product) and photographers who want a scene's palette and the colour of the light. Typical users copy a HEX value into Figma, Procreate, Illustrator or a paint-shop app."
- **`differentiation` gap answer (item 3), proposed:** "Camera colour pickers report colour as lit. Photriya samples a white reference and the target in the same frame and reports both as-seen and light-corrected values with ΔE, with no purchased calibration card. Pantone Connect's camera calibration requires its Color Match Card (per its App Store description); Adobe Capture's description does not mention reference correction. Whether those apps lack it has not been verified."
- **Privacy label (`store/privacy/Photriya.json`) and Play data safety:**
  - Remove EMAIL_ADDRESS, NAME, USER_ID and PURCHASE_HISTORY (no account and no IAP after M5).
  - Keep DEVICE_ID/ADVERTISING_DATA (third-party advertising, not linked), CRASH_DATA, PRODUCT_INTERACTION and PERFORMANCE_DATA.
  - Photos, camera frames and location are processed on-device only and are not collected.
  - The label will then no longer match iMeasure's.
- **Category:** PHOTO_AND_VIDEO today. See founder questions (Graphics & Design is where Adobe Capture and Coolors are filed, per iTunes Search).

## 6. Out of scope

- Any account, sign-in, Supabase, cloud sync, sharing feed or social features.
- Pantone, RAL or any proprietary colour-system matching; spectrophotometer claims; paid calibration hardware.
- AI features of any kind (text-to-image is AGStudio's; no assistant).
- Photo-library browsing, duplicate finding or cleanup (AGCleaner's job); collage, watermark and frames.
- Video, RAW decoding, LUT file import/export.
- Changing ad units, frequency caps or AdMob configuration.
- Editing `store/apps/*.json`, fastlane metadata or `docs/`, uploading, submitting or replying to Apple (Charter §1; 5.6 freeze MA-043).

## 7. Founder questions

1. **Existing accounts.** Photriya has offered Supabase/Google/Apple sign-in. After M5 the app has no account, so in-app deletion goes with it. Any accounts already created through Photriya stay in the shared Supabase project. Keep the web deletion route on the support site for them? Should the office prepare (not run) a query counting Photriya-originated users? Production data is Charter §2.
2. **Privacy policy text.** The policy at `https://www.americangroup.ai/policy/photriya/` presumably describes accounts and OpenAI (not checked). It needs rewording to "no account, on-device processing, ads/crash SDKs only". That is legal text (Charter §6).
3. **Category.** Keep PHOTO_AND_VIDEO or move to GRAPHICS_AND_DESIGN, where Adobe Capture, Coolors and Color Identifier are filed (iTunes Search, 2026-10-12)?
4. **Removing working features.** Collage, watermark, frames and the lessons work today, and M5 removes them to focus the product. This is a scope decision inside one app, not a product removal under Charter §8. Do you want any of them kept?
5. **Crash log.** Apple attached a crash log to the 2026-09-29 2.1(a) message. It is not on this machine. Can you download it from App Store Connect (Resolution Center) so the developer can confirm the cause rather than infer it?

## 8. Implementation notes (software-developer, 2026-10-13)

What differs from the text above, and why, so QA and store-compliance can check it:

- **iOS camera permission (second blocker found).** Besides the NV12 plane count (M1), `permission_handler_apple` 9.4.10 compiles its camera strategy only when the Podfile defines `PERMISSION_CAMERA=1`, which this Podfile does not. Without it, `Permission.camera.request()` answers "permanently denied" on iOS and never shows the prompt (`UnknownPermissionStrategy.m:20`). The camera now lets the camera plugin show the prompt itself and maps its `CameraAccessDenied*` codes; `permission_handler` is only used for "Open Settings".
- **`NSPhotoLibraryUsageDescription` was kept, reworded, not deleted.** image_picker 1.1.2's README (lines 30-34) says App Store policy requires the key even when `requestFullMetadata` is false and no permission is requested. The app now passes `requestFullMetadata: false`, so no library permission is ever requested; the string says the app opens only the photo chosen in the system picker. `NSMotionUsageDescription` was deleted as specified.
- **Release build on the simulator:** Flutter cannot run release mode on an iOS simulator. The developer's proof is a simulator debug launch plus a release build compile (see the run report); a release launch needs a device.

Proposed store follow-ups (not applied here; store files belong to another workstream):

- `ios/Runner/PrivacyInfo.xcprivacy` still declares `NSPrivacyCollectedDataTypePhotosOrVideos` and `NSPrivacyCollectedDataTypeCoarseLocation` as collected. Photos and location are now processed on-device only and never leave the phone, so these two entries can go when the App Store privacy label is changed (section 5), keeping the manifest and the label consistent.
- The screenshot integration test now captures `01_intro_light`, `02_intro_paper_white`, `03_swatchbook_empty`, `04_light_planner` and `05_settings`, with no sign-in. Shots of the camera with a W reference and of the Photo screen with a palette still need real captures on a device (section 5).
- Review notes: there is no account; remove `demo_account_required` / `demo_account_name` as section 5 says.
