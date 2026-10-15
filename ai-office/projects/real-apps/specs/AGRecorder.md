# Spec — AGRecorder: a lecture and meeting recorder you mark as you go

Author: product-manager (AI office) · Date: 2026-10-12 · Project: real-apps
Repo: `/Users/spatchava/agl/AGRecorder` · base_sha `a30512a9c88058d254c48cf2fcbe5025a8916b9e` · branch `main`
Apple: rejected under 5.6 on 2026-10-08T14:20:01Z (`.dist/rejections.json` key `AGRecorder`; the text is the same account-wide 5.6 message sent to 16 apps). Google Play: PRODUCTION_DRAFT_STAGED.

---

## 0. What the app is today (measured at base_sha)

Baseline: `flutter analyze` reports "No issues found! (ran in 71.8s)". `flutter test` reports "+128: All tests passed!". Both were run in this session.

| Area | What exists | Verdict |
|---|---|---|
| `lib/main.dart` (493 lines) | One screen: a header with the app name, the subtitle, a "Saved on this device only" badge, and the Privacy choices and language buttons; a preview box with an icon and status text; one `ChoiceChip` "Microphone"; Start/Stop button; foreground-only hint; a "Recordings" button. | Works, but it is a thin shell. The single chip is a fake choice: `CaptureSource` has one value (`lib/domain/recorder.dart:10`). The placeholder copy is desktop copy: "Select a source and click Record to start" (`app_en.arb` `previewPlaceholder`). |
| Recording (`lib/platform/record_backend.dart`) | `record` 7.1.1, AAC-LC to Documents/`AGRecorder YYYY-MM-DD HH-MM-SS.m4a`. Collisions are handled. | Works. **Foreground-only:** leaving the app stops the take (`main.dart:141-144`) and the screen says so (`foregroundOnlyHint`). There is no `UIBackgroundModes`. A locked phone ends a lecture recording, so the app cannot do the job its listing names. |
| Pause / resume | None. The plugin has `pause()`/`resume()` (`record-7.1.1/lib/src/record.dart:93,100`); the app does not use them. | Missing. |
| Level meter / waveform | None. The plugin has `onAmplitudeChanged` (`record.dart:128`). | Missing. |
| Recordings screen (`lib/screens/recordings_screen.dart`, 445 lines) | List (newest first), play/pause, seek slider, rename with validation, delete with confirmation, share via the system sheet, loading/empty/error states, `AglAdBanner` at :213. | Real and well built. It is a plain file list: no search, no grouping, no metadata beyond date and size. |
| Privacy choices (`lib/widgets/privacy_choices_button.dart`) | UMP privacy options, shown only where required. | Legally required. Keep. |
| Settings | None. Language and privacy sit in the header. | Missing. |
| Theme | Dark only: `0xFF121212`/`0xFF1E1E1E`, seed `0xFFEC4899` (Tailwind pink-500), `0xFF10B981` (emerald-500), `0xFFA1A1AA` (zinc-400), `0xFF374151` (gray-700) (`main.dart:45-50`). Platform default font. | A template tell. |
| Identity files | `CFBundleDisplayName` = `Agrecorder` (`ios/Runner/Info.plist:10`). Android `android:label="agrecorder"`. pubspec description is "A new Flutter project.". Icon comes from `scripts/generate_app_icons.py:62` (`"mic"`, `#B71C1C`→`#EF5350`). LaunchScreen.storyboard shasum starts `3f6a9b27d8` (the 37-app copy). | Template tells. |
| Store copy (`store/apps/AGRecorder.json`) | "AGRecorder is a simple audio recorder." The subtitle "Audio recorder, on-device" is pasted in as the audience. The `differentiation` block still contains "TODO" and "Screens unique to it: none". | Describes a category Voice Memos already covers (4.3(b)). |

Uncommitted changes by other people (do not touch, revert or commit): `fastlane/**` (descriptions, notes, screenshots) and `ios/Podfile.lock` (`git status --short` at base_sha). `lib/`, `test/`, `ios/Runner/`, `android/app/src/` and `pubspec.yaml` are clean, so every file this spec needs is free to edit.

---

## 1. Problem

Apple sees "a simple audio recorder" (store copy, line 1). That is exactly what Voice Memos, built into every iPhone, already does. Apple's own guide says it is for "personal notes, classroom lectures, musical ideas" and that it keeps recording while you use another app. Our app stops recording when the screen locks, so it is strictly worse than the built-in app at the one job it advertises. Its look (Tailwind dark, generated mic icon, white launch screen, 'Agrecorder' on the home screen) matches the rest of the portfolio's scaffold. Nothing in it gives a reviewer a reason for it to exist.

## 2. User and core job

**User:** a student recording a 50–90 minute lecture, or someone recording a meeting or interview. They do not want to listen to the whole thing again. They want the three moments that mattered: "this will be on the exam", "who owns this action", "I didn't follow this part".

**Core job (one sentence):** record a long lecture or meeting reliably with the phone locked in a pocket or on the desk, tap to mark the moments that matter while it happens, and jump straight back to those moments afterwards.

**Owns (portfolio boundary, `overlap.md` G10):** general voice recording of memos, lectures and meetings, kept on the device.
**Must not duplicate VirtuBand:** no instruments, no multitrack, no layering, no song arrangement, no metronome, no click track.

## 3. Competitors and the honest angle

- **Apple Voice Memos** (verified 2026-10-12 by fetching Apple's iOS 27 user-guide pages: `support.apple.com/guide/iphone/record-audio-iph4d2a39a3b/ios`, `…/play-it-back-iphebbd067ce/27/ios/27`, `…/view-a-transcription-iph00953a982/27/ios/27`). It records in the background, pauses and resumes, transcribes (iPhone 12 or later, selected languages), searches titles and transcripts, offers Skip Silence, Enhance Recording and speed control, and syncs through iCloud. **None of those three pages mentions marking or bookmarking a moment during a recording.** This is evidence from three pages, not a full audit of the app. "Voice Memos has no marks" is therefore *partially verified*. Do not put it in store copy as a comparison.
- **Google Recorder:** Apple-side not applicable. Google's help page is titled "Use the Recorder app on your **Pixel** device" (`support.google.com/pixelphone/answer/9516618`, fetched 2026-10-12), so it is a Pixel app. Feature details: competitor not verified.
- **Otter, Just Press Record and other third-party recorders:** competitor not verified. The web search tool is disabled in this session.

**Angle:** we do not compete on transcription. Voice Memos has it on-device, and we cannot match it without native speech code. We compete on **marking during capture, and the follow-up afterwards**. Marks have kinds. To-dos and questions from every recording collect in one place you can tick off. A marks sheet can be shared as text with timestamps. Everything stays on the device.

## 4. Signature feature: Live Marks

While recording, a row of four large buttons is always on screen: **Key point**, **Question**, **To-do** and **Note**. One tap stamps the elapsed recording time. Note opens a one-line text field and recording continues behind it. Key point, Question and To-do accept an optional text afterwards. A light haptic confirms each mark, and a counter shows how many marks this session has.

Afterwards:
1. **On the recording.** The recording screen shows the waveform with a coloured tick for each mark. Tapping a mark plays from its time minus a pre-roll (default 5 s, so you hear the lead-in). Marks can be added during playback, edited (kind, text) and deleted.
2. **Across recordings: the Marks tab.** Every To-do and Question from every recording, newest first, filterable by kind and searchable by text. A To-do has a checkbox that persists. Tapping a row opens its recording at that moment.
3. **Out of the app.** "Share marks" produces plain text, for example:
   ```
   Lecture 2026-10-12 09.14 — 52:07
   04:31  Key point  Krebs cycle net yield
   12:41  To-do      Send slides to Priya
   31:02  Question   Why NADH not FADH2 here?
   ```
   It can be shared alone, copied, or shared together with the .m4a.

All data is on-device. There is no network, no key and no API. The signature feature is the reason the app exists and is the first screenshot.

## 5. Acceptance criteria

### MUST (what Apple needs to see a real, distinct app)

**M1. A long session survives a locked phone, with pause, resume and a live meter.**
- iOS: `UIBackgroundModes` = `audio` in `ios/Runner/Info.plist`. Locking the screen or switching apps does not stop the take. The orange mic dot stays on.
- Android: a foreground service of type `microphone`, with permissions `FOREGROUND_SERVICE` and `FOREGROUND_SERVICE_MICROPHONE` and a persistent notification ("Recording · 00:12:41", with a Stop action). Use `flutter_foreground_task` (pub.dev latest 11.0.3, env sdk ^3.12.0, checked with `curl https://pub.dev/api/packages/flutter_foreground_task`). This is the route the `record` plugin itself recommends (`github.com/llfbandit/record/blob/main/doc/bg_recording.md`: "For both Android and iOS, the recommended way is to use an external package such as flutter_foreground_task").
- Pause/Resume button (`AudioRecorder.pause()/resume()`). A big elapsed timer that excludes paused time, and a live input level meter from `onAmplitudeChanged(100ms)`.
- A call, Siri or another recorder taking the mic **pauses** the take and shows "Paused — a call took the microphone" with a Resume button. Today it ends the take; it must not.
- Remove the foreground-only behaviour: the stop on `paused`/`hidden` lifecycle (`main.dart:141-144`) and the `foregroundOnlyHint` / `stoppedLeftApp` strings.
- An app killed mid-take: on next launch the file is listed. If it cannot be played it is labelled "Incomplete recording" and the app does not crash.

**M2. Live Marks (§4), persisted.**
- Marks are stored per recording in a sidecar JSON at `getApplicationSupportDirectory()/sessions/<file name>.json`. Application Support keeps them out of the Files-app listing that `UIFileSharingEnabled` exposes (`Info.plist:69-72`). Each sidecar holds `kind` (memo/lecture/meeting), the marks `[ {id, atMs, type, text, done} ]` and an amplitude envelope (about 10 samples/s, a quantised 0–255 byte list).
- Mark time = recorded elapsed time, not wall clock, so pauses do not shift marks.
- An in-app rename moves the sidecar and an in-app delete removes it. If a file is renamed outside the app (Files), the recording still lists, without marks. No crash.

**M3. Recording screen (replaces the inline slider row).** Waveform from the stored envelope, with mark ticks in each mark type's colour. Play/pause, skip −15/+15 s, scrub. Tap a mark to seek to `atMs − preRoll`, clamped at 0. Add a mark at the playhead. Edit or delete marks. Share audio, Share marks, Share both.

**M4. Library as the home screen, with depth.**
- The first screen is the library, not the record button. Recordings are grouped by day ("Today", "Yesterday", dates), each with kind, duration and mark counts by type.
- A search field matches recording names **and** mark text.
- Filter chips: All · Memo · Lecture · Meeting · Has open to-dos.
- A large Record button is docked at the bottom centre. A kind picker (Memo/Lecture/Meeting, defaulting to the last one used) sits beside it. New takes are named `<Kind> YYYY-MM-DD HH.MM` (localised kind word), replacing `AGRecorder …` in `defaultRecordingName`.
- Empty state: "Nothing recorded yet. Start a lecture or meeting, and tap Key point when something matters." with the Record button.
- Error state: "Couldn't read your recordings" with Retry (exists today; keep).
- Offline: the app never uses the network for its job, so there is no offline state to build. Only ads go missing offline, and the banner already collapses to zero height.
- Marks tab: see §4.2. Two destinations only (Library, Marks) plus Settings from an app-bar icon. **No Material bottom `NavigationBar` + `AglAdBanner` shell.** Use a segmented control in the app bar, or `CupertinoSlidingSegmentedControl` on iOS.

**M5. Its own identity (distinct from all 42 siblings).**
- *Palette ("paper and ink")*: paper `#F5EFE3` background, ink `#1C2541` text and seed, record/Key point vermilion `#C8402A`, Question ochre `#A8741A`, To-do green `#3C7A5A`, Note slate `#56657A`. Dark variant (follow the system): background `#14182B`, text `#F5EFE3`, same accents. `rg` across every app's `*.dart` for these seven hexes found 0 uses. No Tailwind default hex anywhere in `lib/`.
- *Typography* (revised 2026-10-14, issue #39: IBM Plex stays with AGCleaner only): **Radio Canada** for UI (a humanist sans drawn for a broadcaster, so it suits an audio app) and **Inconsolata** for every timestamp and the timer (monospaced, so the clock does not jitter). Bundled as assets under the SIL OFL 1.1, never fetched at runtime with `google_fonts`: `RadioCanada[wdth,wght].ttf` (one variable file; Flutter maps FontWeight onto its wght axis) and `Inconsolata-Regular/Medium/SemiBold.ttf`, from `github.com/google/fonts/tree/main/ofl/radiocanada` and `…/ofl/inconsolata/static`, with both copyright notices and the licence in `assets/fonts/OFL.txt`, which is also on the licences page (Settings → About). Every `pubspec.yaml` in the portfolio was checked on 2026-10-14: no other app bundles either family. Previously: IBM Plex Sans + Mono (commit 7cf8722).
- *Shape language*: "index card". Rectangular tiles with 4 dp radius (the portfolio's most common radius is 12), a 1 px ink-at-12% hairline instead of elevation, and mark ticks drawn as small flags on the waveform.
- *Home layout*: the library and docked Record button described in M4. The recording session is a full-screen sheet: timer on top in Inconsolata 56 pt, level meter, a 2×2 grid of mark buttons in their colours, and Pause and Stop at the bottom.
- *Onboarding*: one first-run screen, skippable, never shown again (stored in `shared_preferences`). Title "Mark it while you hear it". It has three lines (Record a lecture or meeting · Tap Key point, Question or To-do as it happens · Jump back to those moments later) and a "Start" button. The mic permission is requested at the first Record tap, not on this screen.
- *Settings screen* (new): default kind; mark pre-roll (3/5/10 s); Language (the shared `AglLanguageScreen` may stay; it is infrastructure); Privacy choices (the existing widget, moved here from the header); storage used (real sum of file sizes); an About line: "Recordings and marks stay on this device. Nothing is uploaded."
- *App icon*: drawn by hand, **not** from `generate_app_icons.py`. A paper-coloured square, an ink waveform line, and one vermilion flag marker standing on the waveform. No Material glyph and no diagonal gradient. Remove the `"AGRecorder"` entry from the generator's DESIGN table (`scripts/generate_app_icons.py:62`), or make it skip this app, so a re-run cannot overwrite the icon. The developer edits that one line in agl-manifest/scripts; it is not under docs/ or store/.
- *Launch screen*: background `#F5EFE3`, with the new mark centred at its own size, so the storyboard no longer hashes to `3f6a9b27d8…`. Android `launch_background.xml` uses the same colour.
- *Names*: `CFBundleDisplayName` and Android `android:label` equal the store name exactly. Today that is "AGRecorder", not "Agrecorder" / "agrecorder"; if the founder approves a rename (founder question 1), use the new name. The pubspec `description` becomes a real sentence.

**M6. Template tells and dead controls removed.**
- Remove the single-option "Microphone" `ChoiceChip` and the `CaptureSource` enum's UI.
- Remove the copy "Select a source and click Record to start".
- Remove the `_bg/_panel/_accent/_muted/_online/_border` Tailwind constants (`main.dart:45-50`).
- Replace the header-row language/privacy buttons with the Settings screen (M5).
- Replace the "Saved on this device only" pill (honest, but scaffold styling) with the Settings About line plus a small lock glyph next to the Library title.
- Every visible control does something real. No "coming soon", "not available", "in this build" or "simulator" strings in `lib/` or the ARBs (enforced by a test).

**M7. Honest, and 5.6-safe.**
- Real data only: everything comes from the device's own recordings and the marks the user made. No sample recordings, no seeded marks, and no fake durations in screenshots.
- No account, no login, no demo mode. No reviewer, region or date detection. No hidden gestures; every feature is reachable by a visible control from the library within two taps.
- `AglInsights.init` turns on Firebase Remote Config inside the shared package (`packages/agl_observability/lib/src/insights.dart:104-112`). AGRecorder must **read no Remote Config value** and gate nothing remotely, enforced by a test (M8). Ads remain where described in the store copy, and never on the recording session screen or during a take.

**M8. Proven.**
- `flutter analyze`: no issues. `flutter test`: all pass, with the count ≥ 128 (baseline). New tests cover at minimum:
  1. The controller's elapsed time excludes paused time (fake clock), and a mark at pause+resume gets the right `atMs`.
  2. An interruption pauses rather than stops, and Resume continues the same file.
  3. Sidecar round trip: write, read, rename moves the sidecar, delete removes it, an orphaned m4a lists without marks.
  4. Seeking to a mark uses `atMs − preRoll`, clamped at 0.
  5. Library search matches a mark's text; the "Has open to-dos" filter; ticking a to-do persists.
  6. The marks text export matches the §4 format exactly, including h:mm:ss past an hour.
  7. Day grouping and the `<Kind> YYYY-MM-DD HH.MM` naming.
  8. Onboarding shows once and Skip works.
  9. Tell guard: `lib/` contains none of `0xFFEC4899`, `0xFF10B981`, `0xFFA1A1AA`, `0xFF374151`, `0xFF121212`, nor "click", "coming soon", "in this build" or "not connected". `Info.plist` `CFBundleDisplayName` equals the store name. `UIBackgroundModes` contains `audio`. The manifest declares `FOREGROUND_SERVICE_MICROPHONE`. `lib/` contains no `RemoteConfig` or `getRemoteConfig` read.
  10. Layout tests (responsive, foldable, accessibility) are rewritten against the new screens. Same breakpoints, 2.0× text, 48 dp targets, contrast guideline.
- Tests that assert removed behaviour (`recordings_test.dart:252` "says plainly that recording is foreground-only", `:259` "leaving the app finalises the take", the "Microphone" chip assertions in `widget_test.dart:114`, `accessibility_test.dart:46-47,106` and `foldable_layout_test.dart:216-217`, and `agrecorder_test.dart:158`) are **replaced** by tests of the new behaviour. Each replacement is listed in the commit message. No test is deleted or skipped to go green.
- `integration_test/store_screenshots_test.dart` is updated to drive the new flow, with real takes recorded during the run (M7).
- Commits are path-limited (never `git add -A`; never touch `fastlane/` or `ios/Podfile.lock`) and pushed to `main`. Launch on an iPhone simulator and look at the result (white-screen lesson): screenshot the library, the recording session and the recording screen.

### SHOULD

- S1. Playback speed 1×/1.5×/2× (`AudioPlayer.setPlaybackRate`).
- S2. Collections: group recordings into a course or meeting series ("BIO 101", "Weekly sync"), with a page listing all marks in the series.
- S3. Skip silence during playback, using the stored amplitude envelope (on-device; no claim of "AI").
- S4. A home-screen quick action ("New lecture", "New meeting") through `quick_actions`.
- S5. iOS-native touches: `CupertinoIcons` for transport and marks, `CupertinoSlidingSegmentedControl`, swipe-to-delete on library rows.
- S6. Recording quality setting (Standard 64 kbps / High 128 kbps AAC), passed to `RecordConfig(bitRate:)`.
- S7. Trim the start or end of a recording (shifting marks), only if done with a real on-device method. Otherwise leave it out.

## 6. Data source

**On-device only.**
- Audio: AAC-LC `.m4a` in the app's Documents directory (unchanged, still visible in the Files app).
- Marks and metadata: JSON sidecars in Application Support.
- Preferences: `shared_preferences`.

No Supabase, no public API, no network for the core job. The only network traffic is the existing infrastructure: AdMob with UMP consent, and Firebase Crashlytics/Analytics/Performance through `agl_observability`.

New dependencies: `flutter_foreground_task` (Android background capture; checked on pub.dev), `shared_preferences`, and optionally `quick_actions`. All are keyless.

## 7. Store impact (proposals only; store-compliance applies them; this spec edits no store/ or fastlane file)

**Name:** the 'AG' prefix is a tell. Founder question 1. Until it is decided, keep "AGRecorder" in the store and fix the home-screen casing (M5).

**Subtitle (≤30):** "Mark moments as you record" (26 characters). It replaces "Audio recorder, on-device".

**Promotional text:** "Tap Key point, Question or To-do while a lecture or meeting is recording, then jump straight back to those moments."

**Description (draft).** It does not open with the app name, uses no ALL-CAPS headings, and makes no comparison claims.
> Lectures and meetings are long; the parts you need are short. Start recording, put the phone down — it keeps going with the screen locked — and tap a mark the moment something matters: Key point, Question, To-do, or a quick typed Note.
>
> Afterwards every mark sits on the recording's waveform. Tap one and playback starts a few seconds before it, so you hear the lead-in. To-dos and questions from all your recordings gather in the Marks tab, where you can search them and tick to-dos off.
>
> Share a recording, its marks as plain text with timestamps, or both. Organise takes as memos, lectures or meetings, and find any of them by name or by what you wrote in a mark.
>
> Recordings and marks stay on this device. There is no account and nothing is uploaded; audio leaves the phone only when you share it. On iPhone and iPad the audio files also appear in the Files app.
>
> The app is free and shows Google AdMob ads in the library, never while you record. Where the law requires it you are asked for consent first, and you can change it any time in Settings › Privacy choices.

**Keywords:** `lecture recorder,meeting recorder,bookmark,timestamps,class notes,voice memo,to-do,markers,interview` (re-check the 100-character limit when applying).

**Category:** keep UTILITIES, or consider PRODUCTIVITY. Store-compliance can decide; it is not a founder item.

**Screenshots to retake** (all from the updated `store_screenshots_test.dart`, with real takes recorded in the run; durations are whatever was really recorded):
1. Recording session: timer, level meter, mark grid, "3 marks" counter.
2. Recording screen: waveform with coloured mark flags, one mark selected.
3. Marks tab: open to-dos and questions across recordings, one ticked.
4. Library: day groups, search with a query, the Lecture filter.
5. The shared marks text in the system share sheet.

This replaces the current set, where screenshots 1 and 4 are near-duplicates. Do not reuse any frame from the current set. The Play feature graphic must be redrawn with the new icon and palette and without the Flutter logo.

**Review notes (written for this app; not the shared skeleton, not starting at "2.")**
- What it is for: recording lectures and meetings and marking moments during capture. Who: students, and people who record meetings or interviews.
- How to try it in 60 seconds: launch → Start on the one-screen intro (or Skip) → pick Lecture → tap Record → allow the microphone → tap Key point, then To-do → lock the phone for 10 seconds (recording continues; this is why the app declares the `audio` background mode) → unlock → Stop. The recording opens with its marks; tap one to play from just before it. Open the Marks tab to see the to-do. Settings holds language, pre-roll and Privacy choices.
- No account, no login, no server; every feature is visible from the library.
- External services: AdMob (library only, UMP consent), Firebase Crashlytics, Analytics and Performance. Remote Config is initialised by the shared library but the app reads no values from it.
- Testing: state only the devices it was actually tested on. Do not repeat the "simulators … a build that cannot start never ships" boilerplate. A physical-device screen recording is still required by Apple 2.1 (`docs/APPLE_REQUIREMENTS.md`, `recording_on_file`, HUMAN).
- Remove "Intended audience: Audio recorder, on-device".

**Privacy label:** no change in categories. Audio and marks never leave the device, so no Audio Data is collected. The label stays identical to the 20-app group because the same SDKs collect the same data, and that is truthful. Do not make it different artificially.

**Google Play:**
- Android 14+ requires the foreground-service declaration for type `microphone` in Play Console (App content → Foreground service permissions), with a short video of the recording notification. Not verified in Console by me.
- Update the data safety form only if dependencies change what is collected (they do not).

**Differentiation block** (`store/apps/AGRecorder.json` `differentiation`): replace the TODOs.
- "Screens unique to it": recording session with mark grid, recording waveform with marks, Marks inbox.
- "Gap": marking during capture plus a cross-recording to-do inbox, worded without a competitor claim we have not verified.

## 8. Out of scope

- Transcription, summaries, or anything "AI". Voice Memos does transcription and we would need native speech code; not claimed and not built.
- Cloud sync, accounts, Supabase.
- Music features (instruments, multitrack, layering, metronome; VirtuBand's job), video or screen capture, Apple Watch, widgets, Live Activities.
- Changing shared packages (`agl_ads`, `agl_i18n`, `agl_observability`).
- Editing `store/apps/*.json`, fastlane metadata or `docs/`.
- Submitting, replying to Apple, or uploading to any store. The 5.6 freeze (MA-043) holds.

## 9. Founder questions

1. **Name.** Replace "AGRecorder" (the 'AG' house prefix is a listed tell) with a product name, for example "Margin — Mark as You Record", "Waymark Recorder" or "Lecture Marks". App Store name availability is **not verified**; ASC answers 409 if a name is taken.
2. **Ads in a recording app (Charter §3, money).** Today an interstitial can show when opening Recordings (`main.dart:162`). Proposal: keep the library banner and allow at most a capped interstitial only when leaving a recording screen back to the library. Never during or right after a take. Or drop interstitials in this app.
3. **Play foreground-service declaration.** It needs a short screen video of the recording notification on a physical Android device. Who records it?
4. **Resubmission and the Apple reply** stay with you (Charter §1; 5.6 freeze MA-043). This spec does not touch them.

---

## 10. Implementation notes (software-developer, 2026-10-12)

AGRecorder commits 59fa79c (iOS build fix) and 7cf8722 (M1–M8, S1, S5 partial, S6). For store-compliance, store copy is unchanged. These facts affect §7:

- **Screenshots.** The rewritten `integration_test/store_screenshots_test.dart` produces `01_session`, `02_recording`, `03_marks` and `04_library` from real takes recorded during the run. The fifth (marks text in the system share sheet) is a native sheet outside Flutter's surface and is not captured by the test; it needs a manual capture.
- **Interstitial (founder question 2 still open).** It was kept where it was in effect: opening a recording from the library or the Marks tab. It is never shown during a take or when the app opens a take right after Stop. No new ad placement was added.
- **Review notes.** The "How to try it in 60 seconds" flow in §7 matches the build. Settings › Privacy choices appears only where UMP requires it.
- **Name.** Still "AGRecorder" (founder question 1 open); `CFBundleDisplayName`/`android:label` now match it exactly.
- **iOS build.** The simulator build had been failing since agl_ads (google_mobile_ads 9.1.0) was added: a non-modular include error. Fixed with `CLANG_ALLOW_NON_MODULAR_INCLUDES_IN_FRAMEWORK_MODULES` in `ios/Podfile` and `ios/Flutter/*.xcconfig`. A pod install also changes `ios/Podfile.lock` and adds a "[CP] Copy Pods Resources" phase to `project.pbxproj`; neither was committed (other people's working-tree files).
- **Not done:** S2 collections, S3 skip silence, S4 quick actions, S7 trim; swipe-to-delete (part of S5).
