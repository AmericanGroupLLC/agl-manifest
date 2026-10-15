# Spec: Verba, the phrasebook you speak

Author: product-manager (AI office) · Date: 2026-10-12 · Project: real-apps (plan.md)
Repo: `/Users/spatchava/agl/Verba` · branch `main` · base_sha `ef8be2c41ceae4c550a6261218cc24379e3693b2`
Store state:
- Apple: rejected under 4.3 / 4.2.6 (2026-10-05T21:25Z). Before that it got 2.1(a) "crashed on launch" on an iPhone 17 Pro Max with iOS 27, and 2.3.3 "screenshots do not show the current version" (2026-09-29T18:43Z).
- `docs/store-holds.json:117` records the 4.2.6 hold.
- Google Play: `PRODUCTION_DRAFT_STAGED`.

---

## 0. What exists today (measured at base_sha)

**What I read:**
- `lib/main.dart`, the shell, and every screen under `lib/features/`: translate, practice, phrasebook, flashcards, talk, buddy, me, model manager, kid-safe, notifications, affiliate, onboarding, splash, legal.
- `core/llm/*`, `core/services/{ai_service,speech_recognition_service,saved_phrases_store,notification_service,connectivity_service,monetization_service*}.dart`, `core/theme/app_theme.dart`.
- `pubspec.yaml`, `native/verba_llama/README.md`, `ios/VerbaKeyboard/README.md`, `android/app/src/main/AndroidManifest.xml`, `android/app/build.gradle.kts`, and the Android keyboard Kotlin.
- `store/apps/Verba.json`, `store/privacy/Verba.json`, `.dist/rejections.json["Verba"]`, and the Verba entries in `docs/apple-requirements.json`, `docs/store-holds.json` and `docs/MANUAL_ACTIONS.md`.
- `lib/` totals 16,881 lines in 66 Dart files (`wc -l`).

**Baseline checks, run 2026-10-12 with `--no-pub`** so `pubspec.lock` stayed unchanged:
- `flutter analyze --no-pub` gave `No issues found! (ran in 16.3s)`.
- `flutter test --no-pub` gave `+688: All tests passed!`.
- `git status` was the same before and after. Every uncommitted change belongs to someone else:
  - `fastlane/**`: 11 modified files and 16 new screenshots;
  - `ios/Flutter/Generated.xcconfig` and `ios/Flutter/flutter_export_environment.sh`;
  - `ios/Podfile.lock`;
  - `ios/Runner.xcodeproj/project.pbxproj`.

| Area | File | State |
| --- | --- | --- |
| Translate (core) | `features/translate/screens/translate_screen.dart` (1,117 l.) | **Works.** It has three modes: Text, Voice (OS recogniser, then translate) and Convo (two mics, one per language). It reads results aloud (`flutter_tts`), copies them, saves them to the phrasebook, and has "Practice this phrase". Errors are honest (`TranslationUnavailableException`, no sample text). **Nothing is kept except bookmarks:** there is no translation history. |
| Translation backend | `core/services/ai_service.dart:290-376` | MyMemory `GET https://api.mymemory.translated.net/get`. It is keyless. I ran curl on 2026-10-12: `en→es` "Where is the train station?" returned HTTP 200, `responseStatus 200`, `match 1`, `quotaFinished:false`, plus a `matches[]` array of alternatives. `en→ja` "Thank you" returned 200 too. |
| Fake model manager | `ai_service.dart:28-126` `ModelManager` | **Dead and dishonest.** It lists Whisper / Phi-3 / Piper as "Cloud … available". `checkModelStatus` waits 400 ms and then marks every model available. Nothing references it (grep: the only hit is its own file). |
| Practice | `features/practice/screens/practice_screen.dart` (1,232 l.) | **Works.** You pick a scenario deck (airport, restaurant, hotel, …), TTS plays the phrase, the OS recogniser listens, and the screen shows "Words recognised: x of y". Spanish is written by hand. Other languages are machine-translated through MyMemory. The scoring (`ai_service.dart:384-410`) splits on whitespace, so **Chinese and Japanese sentences count as one "word"** and score 0 % or 100 %. |
| Flashcards | `features/practice/screens/flashcard_screen.dart` (795 l.) | **Works.** Built-in Spanish, French and Mandarin decks. SM-2 scheduling at l.50-69, progress stored in `flashcard_progress_v1`. Saved translations **never become cards**. |
| Phrasebook | `features/practice/screens/phrasebook_screen.dart` | Two tabs: Phrase Decks and Saved Phrases (`saved_phrases_v1`). Saved Phrases can be spoken and removed. No search, no export. |
| Talk | `features/talk/screens/talk_screen.dart` (834 l.) | **Hidden.** It is an LLM conversation partner. `main_shell.dart:41-45` hides it when `OnDeviceAi.isAvailable` is false, and it is false on both platforms (rows below). This is the 5.6 risk the brief names. |
| Buddy | `features/buddy/**`, `core/services/buddy_engine.dart`, `core/domain/{buddy_mode,quota_tracker,content_policy,prompt_templates,profile}.dart` | **Hidden** the same way. The modes are Chat / **Roast** / Daily Challenge / **Party Questions** / **Game Coach** (`buddy_mode.dart:31-35`), carried over from the LocalBuddy merge. They have nothing to do with translation. Kid-safe profiles (`kid_safe_screen.dart`, `profile_store.dart`) exist only for Buddy. |
| On-device LLM | `core/llm/*`, `native/verba_llama/` | **Cannot run on either platform today.** `native/llama.cpp` is absent and there is no `.gitmodules`, so the shim builds as the stub (`README.md`: "absent (default) → `verba_llama_is_real()` 0"). On iOS the shim is not in the Runner target (`grep verba_llama ios/Runner.xcodeproj/project.pbxproj` gives 0 hits). The catalogue models are 398 MB to 2.39 GB (`model_catalog.dart`). |
| **Android keyboard** | `AndroidManifest.xml:54-69`, `kotlin/.../keyboard/*.kt`, `res/xml/method.xml`, `build.gradle.kts:118` `keyboard_label "Verba Keyboard"` | **It ships in the prod Play build.** A system input method called "Verba Keyboard" shows up in Android settings. It suggests replies through the stub llama shim, so it can never produce a suggestion (`VerbaLlamaBridge.kt:77` returns null unless `nativeIsReal()`). It is also a **reply-suggestion keyboard, which is AGrammarly's job** (brief: MUST NOT DUPLICATE). |
| iOS keyboard | `ios/VerbaKeyboard/` | Swift sources that are not in any Xcode target (its README says so). Dead files. |
| Me / settings | `features/me/screens/me_screen.dart` (861 l.) | Shows stats, Weekly progress and Language progress from real `ActivityStats`. Has a haptics toggle, Notifications, Privacy Policy and Terms (URLs) and Privacy choices (UMP). The On-device AI and Profiles rows are hidden (l.484). Language Partners (affiliates) is hidden because its URLs contain `YOUR_…_CODE` placeholders (`verba_config.dart:115-131,172`). Template copy at l.767 "Speak. Understand. Connect." and the "Privacy-First" / "No Account Needed" badges. |
| Onboarding | `features/onboarding/onboarding_screen.dart` (1,018 l.) | 4 pages (5 when AI is available): Welcome with **"Get Started"** (l.320), Permissions, Languages, (On-device AI), "You're all set!". The languages it stores (`native_language`, `learning_language`) are read only by the Me screen (`me_screen.dart:85`). Translate and Practice always start on English→Spanish. |
| Splash | `features/splash/splash_screen.dart` | A hard-coded **2.2 s delay** (l.57), the tagline "AI Language Companion" (l.141), and **"Offline AI Ready"** (l.175), which is false. |
| Offline | `connectivity_service.dart:92-120` | A global banner, "No internet connection — some features unavailable". It does not say which features. |
| Notifications | `notification_service.dart` | Real local reminders. Practice copy says "Your pronunciation coach is ready. Let's work on your accent today." That claims an acoustic coach the app does not have (it only matches words). |
| Ads | `main.dart:75` `initializeAdMob` | The SDK and UMP consent are initialised, but **no ad is ever placed**: no `AdBanner(` use, and no interstitial `show` call in `lib/`. `MANUAL_ACTIONS.md:615` lists 4 Verba ad units still missing. |
| i18n table | `core/i18n/app_localizations.dart` (551 l.) | A 12-language table that no screen reads (`main.dart` comment: "The screens … do not read [AppLocalizations] yet"). It holds template strings: **"Get Started"** (l.389), **"Unlock with Pro"** (l.511), "Upgrade to Verba Pro" (l.358). The app has no Pro tier. |
| Unused legal screen | `features/legal/privacy_policy_screen.dart` | Nothing references it (grep). The text describes Talk, Buddy's server fallback and affiliates. |
| Theme | `core/theme/app_theme.dart` | A near-black `#0A0E1A` background with neon cyan `#00D4FF` and violet `#7C3AED`, and Tailwind `F59E0B`, `10B981`, `F43F5E`, `94A3B8`, `475569`, `334155`, `1E293B`, `111827`. Dark only. This is the "near-black + neon" tell. |
| Font | `fontFamily: 'Satoshi'` | **189 uses**, but the `fonts:` block is commented out (`pubspec.yaml:141-151`) and `assets/fonts/` holds only `.gitkeep`. Everything renders in the system font. |
| Shared widgets | `core/widgets/glass_card.dart` | A glassmorphism card used on 6 screens. The store description even advertises "glassmorphic cards". |
| Brand | `Info.plist` `CFBundleDisplayName` = `Verba`, `CFBundleName` = `verba`; Android `app_name` "Verba" | Display names are fine. |
| Icon | `assets/icon/app_icon.png` (1248²) | A neon violet globe with a chat bubble, a waveform and a small neural-network graph on navy. The corners are rounded inside the image. My reading (not measured): a generic "AI" icon. |
| Splash (native) | `ios/Runner/Base.lproj/LaunchScreen.storyboard` | shasum `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`: the shared white storyboard. `LaunchImage@3x.png` is 540×540. |
| Launch | `docs/apple-requirements.json` "Verba" | `FAIL — Apple 2.1(a): Launches on iOS 27, iPhone and iPad — iPad simulator: simulator_unresponsive`. **Root cause not verified.** |
| Dependencies | `pubspec.yaml` | `web_socket_channel` and `path` have 0 imports in `lib/`. `flutter_riverpod` is used only for `ProviderScope`. `ffi` is used only by the LLM bindings. There is a long commented "Phase 2+" block, and the description says "Powered by cloud AI." |

**Honest summary.** The translator, the speech practice and the SM-2 flashcards are real and honest. But they are three separate islands:
- Nothing you translate is remembered except a bookmark.
- Bookmarks never turn into practice.
- Chinese and Japanese practice can't score properly.

Around them sit roughly 4,000 lines of features that cannot run in any shipped build: Talk, Buddy, the model manager, kid-safe profiles, and the Android and iOS keyboards. One of them, the Android keyboard, is installed on users' phones today. On top of that, the identity is the portfolio's "dark + neon + glass" look in a font that isn't bundled.

## 1. Problem

Apple sees a template: the shared splash, a neon "AI" icon, glass cards, "Get Started", and a 3-mode translator that does the same thing every built-in translator does (4.3(b)). The binary contains whole features that the UI hides (Talk, Buddy), and that is exactly what 5.6 punishes on this account. The 2026-09-29 Resolution Center reply even listed "Apple In-App Purchase — paid features", and Verba has no IAP.

A user gets a translator that forgets everything, a practice tab that can't tell whether they said "谢谢" correctly, and an Android keyboard they never asked for.

## 2. User

**Who it is for.** Someone preparing for, or in the middle of, a stay in a country whose language they don't speak, in one of the 12 supported languages: es, fr, de, it, pt, ru, zh, ja, ko, hi, ar, en. Examples:
- a week in Lisbon or Osaka;
- a parent visiting a child who moved abroad;
- a newly arrived expat in their first months.

**What they need.** In the moment, they have to say a specific thing: order without pork, ask for the 7:40 train, tell the pharmacist about an allergy. They want to be able to say those few dozen phrases **without holding the phone up** by the end of the trip. They are not signing up for a language course. UI language: English (`VerbaApp.appLocales = [Locale('en')]`, `main.dart`).

**Core job:** *Translate what I need to say, by typing or speaking. Keep it. Then practise saying it out loud until I can say it on my own.*

## 3. The honest angle and the signature feature

**Competitors: not verified.** WebSearch is disabled in this session ("Internet mode is not enabled"). I therefore name no competitor and make no claim about what Google Translate, Apple Translate, Duolingo or any other app does. Before any of this reaches Apple, someone with web access must check the comparison.

**The angle, as a product claim about Verba only:** a translator usually ends when you get the answer, and a course teaches you its own sentences. Verba turns *the sentences you actually needed* into a speaking drill that comes back on a spaced schedule and checks that you said them.

**Signature feature: the Say-it-back deck.**

1. **Every saved translation becomes a card.** Saving (the bookmark in Translate, or "Add to deck" from History) creates a card: *(your text, translation, from, to, created, SM-2 state)*.
   - Starter phrases are optional. They come from the existing scenario decks (`practice_screen.dart`) and the Spanish/French/Mandarin flashcard decks (`flashcard_screen.dart`), are added only when the user picks them, and are labelled "Starter".
2. **A review is spoken, not flipped.** For each due card:
   - The card shows your text.
   - **Hear it** plays the translation through `flutter_tts` in the target language. Normal and slow speeds.
   - **Say it** opens the OS recogniser in the target locale (`SpeechRecognitionService.start(languageCode:)`). The heard text is aligned with the translation, and the matched words or characters are highlighted.
   - The grade is proposed from the match, and the user can override it with one tap:

     | Match | Grade | SM-2 quality |
     | --- | --- | --- |
     | ≥ 80 % | Good | 4 |
     | 50-79 % | Hard | 3 |
     | < 50 % | Again | 1 |

     The user can also pick **Easy** (5).
   - The next due date comes from the existing `updateSM2` (`flashcard_screen.dart:50-69`), moved to a pure-Dart `core/domain/srs.dart`.
3. **Scoring that works for every script.**
   - For `zh` and `ja`, matching is **per character**, after removing punctuation and whitespace.
   - For every other language it is per word, using the existing Unicode-aware normaliser.
   - The result is shown as "Heard 6 of 7 words" or "Heard 9 of 10 characters". It is **never** called a pronunciation or accent score.
4. **When the recogniser can't help, the review still works.**
   - No recogniser or permission for that language: the card says so ("Your phone has no speech recogniser for Korean"). The user grades themselves with Again / Hard / Good / Easy, and it is recorded as self-graded.
   - Nothing heard: "Nothing was heard. Tap Say it and try again." Nothing is scored.
5. **Show it.** Any card or translation can open full-screen large type of the target text for the other person to read, with Hear it. No network needed.
6. **Due reminders tell the truth.** The local notification fires only when cards are due, at the time the user picks. The text is real, e.g. "7 phrases are due — say them back." No streak guilt and no coach claims.

All of this is on-device: saved data, SRS, matching, TTS and the OS recogniser. The only network call in the app is the translation itself. One developer can build it in this session from code that already exists (SM-2, the word matcher, TTS, the recogniser, the saved-phrase store).

## 4. Acceptance criteria

### MUST (what Apple needs to see a real, distinct app)

**M1. A Phrase desk home that does the core job end to end, and keeps history.**
- After onboarding the app opens on **one Phrase desk screen**. There is no bottom NavigationBar and no 3-mode TabBar.
- From top to bottom:
  - a **language pair bar** (two pills, *from* ⇄ *to*, swap button) that defaults to the onboarding choice and is persisted;
  - a multi-line input with a **mic** (dictate, then translate on the final result) and a Translate button;
  - the result card with **Hear it**, **Copy**, **Save to deck** and **Show it**;
  - a **"Due today · N"** strip that opens the review;
  - **Recent**: the last 5 history items, plus "All history".
- App-bar actions: **Deck**, **History**, **Face to face**, **Settings**. Each opens with `Navigator.push`.
- **Face to face** replaces "Convo". It is a full-screen split. The top half is rotated 180° for the person opposite and shows the *to* language with its own mic. The bottom half shows the *from* language with its mic. Each finished utterance is translated into the other half and spoken there with TTS (the existing `_toggleRecording` / `_toggleReplyRecording` logic). Each turn is written to history.
- **History:** every successful translation, typed, dictated or face-to-face, is stored as *(source, translation, from, to, at, mode)*. It persists across restarts in shared_preferences JSON under a new key `verba.history.v1`, capped at 500 with the oldest dropped first.
- Acceptance check: on a fresh install, choose English→Portuguese in onboarding. Type "Where is the pharmacy?", tap Translate, and a translation shows with the MyMemory attribution. Tap Save to deck, and the snackbar says "Added to your deck". Kill and relaunch the app. Recent shows the item, the Deck has 1 card, and "Due today · 1" is shown.

**M2. Signature: the Say-it-back deck, exactly as in §3.**
- Pure Dart `core/domain/phrase_match.dart`: `PhraseMatch.score(heard, expected, languageCode)` gives *(matched, total, unit: words|characters, spans)*. Per-character for `zh` and `ja`, per-word for the rest.
- `core/domain/srs.dart` holds the SM-2 moved out of the widget file, plus `gradeFor(percent)` with the §3 thresholds.
- The **Review screen** has Hear it (normal and slow), Say it, highlighted heard spans, the proposed grade with a one-tap override, the self-grade path when there is no recogniser, and a **Show it** button.
- The **Deck** combines the user's saved cards and the Starter cards the user added, in a single store `verba.deck.v1`.
- One-time **migration** on first launch after the update:
  - every `saved_phrases_v1` entry becomes a deck card that is due now;
  - existing `flashcard_progress_v1` SM-2 state is carried over to the matching Starter cards, so no progress is lost;
  - the old keys are removed only after the new key has been written.
- **Reminders:** the Settings switch "Remind me when phrases are due" plus a time picker. The notification is scheduled only when at least 1 card is due at that time, and its text contains the real count.

**M3. Depth: search, filter, export, and states.**
- **History screen:**
  - newest first;
  - search across source and translation;
  - filter by language pair;
  - tap to reload the pair into the desk;
  - "Add to deck";
  - swipe to delete with Undo;
  - "Clear history…" with an adaptive confirm dialog.
- **Deck screen:**
  - search;
  - filter chips All / Due now / Struggling (last 2 grades Again) / Starter / Mine;
  - language filter;
  - each card shows its next due date;
  - swipe to delete with Undo.
- **Export:** the deck as CSV (`your_text,translation,from,to,created,next_due,reviews`, RFC 4180 quoting, UTF-8 with BOM so spreadsheets read CJK) through the share sheet (`share_plus`).
- **Offline:**
  - Remove the global `OfflineBanner`.
  - While offline, the desk shows inline: "You're offline. Translating needs a connection — your deck, history, reviews and Show it all work offline." Translate and the dictate-to-translate path are disabled.
  - History, Deck, Review (TTS and recogniser permitting) and Show it work in airplane mode.
- **Errors:**
  - MyMemory `quotaFinished == true`, or a quota-type `responseDetails`, shows "Today's free MyMemory translation allowance is used up on this connection. Saved phrases still work." (This is a new distinct message; the field is in the live response.)
  - Network and timeout errors keep the existing `TranslationUnavailableException` message.
  - More than 500 characters keeps the existing message.
- **Empty states:**
  - Deck: "Save a translation and it becomes a card you practise saying."
  - History: "Translations you make appear here."
  - Search: "Nothing matches '<q>'."
  - Due: "Nothing due. Next card: <date>." (from real data).
- Storage write failures are caught, reported through `AglCrash` / `ErrorReporter`, and shown as a snackbar.

**M4. Hidden, dead and dishonest features removed from the binary (5.6).**
- **Delete:**
  - `features/talk/`, `features/buddy/`, `core/services/buddy_engine.dart`;
  - `core/domain/{buddy_mode,quota_tracker,content_policy,prompt_templates,profile}.dart`, `core/services/profile_store.dart`;
  - `features/me/screens/{model_manager_screen,kid_safe_screen,affiliate_screen}.dart`;
  - all of `core/llm/` and `native/verba_llama/`;
  - `ios/VerbaKeyboard/`;
  - the Android `keyboard/` Kotlin package, `res/xml/method.xml`, the `<service …VerbaInputMethodService>` block in `AndroidManifest.xml`, the three `keyboard_label` `resValue`s, and the `externalNativeBuild` / cmake blocks in `android/app/build.gradle.kts`;
  - `core/services/affiliate_tracker.dart`, plus the affiliate constants and `YOUR_…` URLs in `verba_config.dart` and `monetization_service_interface.dart`;
  - the `ModelManager` class in `ai_service.dart`;
  - `features/legal/privacy_policy_screen.dart` (unreferenced);
  - `core/i18n/app_localizations.dart` and its delegate (unread, carries Pro / Get Started);
  - `app_env.dart`, whose only consumer was `CloudEngine`;
  - the `OnDeviceAi` gating in the shell, onboarding and Me.
  - Founder decision Q1/Q2 covers this.
- **Remove dependencies** that have zero imports in `lib/` afterwards. Today that is `ffi`, `web_socket_channel` and `path`. `flutter_riverpod` goes if `ProviderScope` is the only use; `crypto` and `convert` go if they become unused. Also remove the commented "Phase 2+" block and the Satoshi comment. Set `description:` to a true sentence with no "cloud AI".
- Rewrite the splash copy ("Offline AI Ready", "AI Language Companion") by deleting the Dart splash screen (M6). Rewrite the notification copy to the M2 due-count text.
- **Tests that test only deleted code are deleted in the same commit as that code, and each file is listed in the commit message.** Today that is `test/features/buddy_screen_test.dart`, `test/services/{buddy_engine,profile_store}_test.dart`, `test/domain/{content_policy,quota_tracker,prompt_templates,profile}_test.dart`, `test/llm/*`, `test/app_env_test.dart` and the AppLocalizations parts of `test/i18n_test.dart`. Tests that mix live and deleted behaviour are **rewritten** to the new behaviour (`no_invented_data_test.dart`, `main_shell_navigation_test.dart`, `release_fixes_test.dart`, `monetization_test.dart`, `verba_config_test.dart`, `services_test.dart`, `foldable_layout_test.dart`, `integration_test/app_test.dart`). They are not skipped.
- A **removal test** fails if `lib/` contains any of these, or if the Android manifest declares `android.view.InputMethod`:
  - `Roast`, `Party Questions`, `Game Coach`, `Buddy`, `On-device AI`, `GGUF`, `llama`;
  - `this build`, `coming soon`, `Coming soon`, `not connected`, `not available yet`, `Simulator mode`;
  - `Get Started`, `Unlock with Pro`, `Verba Pro`, `YOUR_`, `Offline AI`;
  - `pronunciation coach`, `accent`.

**M5. Own identity, in code.**
- **Colour.** "Linen and ink, with a saffron stamp." Light is the default and dark follows the system (`ThemeMode.system`); today the app is forced dark.
  - Light:

    | Role | Hex |
    | --- | --- |
    | Seed / primary (saffron) | `#C7820A` |
    | Ink, text and "your side" | `#1B2541` |
    | Background (linen) | `#F2EEE3` |
    | Surface | `#FCFAF4` (was #FBF9F3, which AeroSwift already used; changed 2026-10-14) |
    | Muted | `#5B6275` |
    | Error | `#B0413E` |

  - Dark:

    | Role | Hex |
    | --- | --- |
    | Background | `#10141F` |
    | Surface | `#1A2030` |
    | Primary | `#F0B341` |
    | Text | `#EEE8DA` |

  - The neon cyan/violet palette, the Tailwind hexes and `primaryGradient` are deleted.
  - Checked: `grep -rliE "0x(FF)?<hex>|#<hex>"` over `*.dart`, `*.md` and `*.json` across `/Users/spatchava/agl` found **0 files** for all ten hexes. (`#A8322D` was my first error colour; it is already in the NearServe and EventSpark specs, so I replaced it.) None is a Tailwind default.
- **Type.** Bundle the fonts as assets. No `google_fonts` runtime fetch, because the deck must work offline.
  - **Gloock** Regular for the wordmark, screen titles and the large phrase on cards and in Show it (Latin).
  - **Golos Text** (variable `wght`) for body and UI. It covers Latin-extended and Cyrillic, so es, fr, de, it, pt and ru translations render in the brand font. I checked this with fontTools against the downloaded file: Latin-ext True, Cyrillic True. Arabic, Devanagari and CJK fall back to the platform font.
  - Sources: `curl` returned HTTP 200 for `github.com/google/fonts/raw/main/ofl/gloock/Gloock-Regular.ttf` (98,096 B), `ofl/gloock/OFL.txt`, `ofl/golostext/GolosText%5Bwght%5D.ttf` (184,292 B) and `ofl/golostext/OFL.txt`.
  - `grep -rliE "gloock|golos"` across all repos and the other specs found no other app using either font.
  - Remove all 189 `fontFamily: 'Satoshi'` literals and drive text from `TextTheme`.
  - Register the OFL texts with `LicenseRegistry`.
- **Shape language: "phrase card".**
  - Cards have radius 6 and a 1 px ink hairline border, with no blur or glass.
  - A translation card has two halves split by a dashed "perforation" line: *your side* in ink on surface, *their side* on a 12 % saffron tint.
  - Delete `glass_card.dart`. No `BorderRadius.circular(12)` in `lib/`.
- **Icons.** `CupertinoIcons` throughout. `cupertino_icons` is already a dependency.
- Dialogs and switches use adaptive constructors (`showAdaptiveDialog`, `Switch.adaptive`).

**M6. This app's template tells removed: icon, launch, onboarding, settings.**
- **Launcher icon:** a linen `#F2EEE3` square with an ink `#1B2541` phrase card turned slightly, a saffron `#C7820A` corner tab, and a quotation-mark cut-out.
  - No globe, waveform, neural graph, neon glow or gradient.
  - The corners are **not** pre-rounded in the image.
  - Drawn by our own script or vector, then regenerated with `flutter_launcher_icons` and `adaptive_icon_background: "#F2EEE3"`.
  - `flutter_native_splash` colours change from `#0A0E1A` to `#F2EEE3` / dark `#10141F`.
- **Launch:**
  - `LaunchScreen.storyboard` gets background `#F2EEE3` and the new mark, so its shasum is no longer `3f6a9b27…`. `LaunchImage` is regenerated. Android `launch_background` matches.
  - **Delete the Dart `SplashScreen` and its 2.2 s delay.** `main` routes straight to onboarding or the desk based on `onboarding_complete`.
- **Onboarding is 2 steps.** No "Get Started", no "You're all set!", no permission page.
  1. **"Where are you headed?"** Pick the language you need from the 12, with the native name and flag, and the language you speak. Both are saved and used as the desk pair (fixing today's ignored `learning_language`). The button reads "Next".
  2. **"Add some starter phrases?"** Optional scenario chips (Airport, Restaurant, Hotel, Getting around, Shopping, Pharmacy & doctor) add the matching Starter cards to the deck. They are machine-translated through MyMemory for languages with no written deck, which needs a connection; offline it says so and lets you skip. **Skip** is always visible. The button reads "Open my phrase desk".
  - Microphone and notification permissions are asked **in context**: the first tap on a mic, and the first time reminders are switched on.
- **Settings copy and sections:**
  - "Languages" (the desk pair);
  - "Practice" (reminder switch and time, speech speed, haptics);
  - "Your data" (Export deck…, Clear history…, Erase deck…);
  - "About" (version from `package_info_plus`, which is already in `pubspec.lock` l.745; Privacy policy; Terms; Support; Open-source licences);
  - "Privacy choices" only while the AdMob SDK is still in the app (Q3).
- The stats dashboard ("Language Learner", Weekly / Language progress) moves into the Deck header as real counts: cards, due, reviewed this week.
- Delete "Speak. Understand. Connect.", "Privacy-First" and "No Account Needed".

**M7. It launches on iOS 27, iPhone and iPad.**
- `docs/apple-requirements.json` records `simulator_unresponsive` on the iPad simulator, and Apple reported a launch crash on iPhone 17 Pro Max with iOS 27. The cause is **not verified**.
- The developer builds Release for the iOS 27 iPhone 17 Pro Max and iPad Pro 13" simulators, launches each from a fresh install, and saves a screenshot of the first interactive frame. The onboarding screen must be reached in ≤ 5 s, and the desk after onboarding.
- If either hangs or crashes, find the root cause from the simulator log (`xcrun simctl spawn … log`) before anything else. Quote it in the commit or report.
- A physical-device run is a human step (Q6). Do not claim it.

**M8. Proven.**
- `flutter analyze` is clean and `flutter test` passes, with no test skipped (M4 lists what is deleted with its code).
- **New tests, at least:**
  - `PhraseMatch`:
    - word mode with accents (`"¿Dónde está la farmacia?"` vs `"donde esta la farmacia"` → 4/4);
    - per-character mode (`"谢谢你"` vs `"谢谢"` → 2/3);
    - empty heard text → 0, flagged as not scored.
  - `srs`: each SM-2 branch, and `gradeFor` at 49 / 50 / 79 / 80.
  - Stores:
    - history round trip, the 500 cap, search and pair filter;
    - deck round trip;
    - migration from `saved_phrases_v1` and `flashcard_progress_v1` that keeps SM-2 state and removes the old keys only after the write;
    - CSV export content, including commas, quotes and CJK.
  - `TranslationService`: `quotaFinished:true` → the quota message (with a fake `Dio`).
  - Widgets:
    - the desk flow: type, translate (fake service), Save, then the Deck has 1 card and "Due today · 1" after the store is rebuilt;
    - offline state disables Translate and keeps Deck reachable;
    - Review: fake recogniser returns text → proposed grade → override → next due date;
    - Review without a recogniser → self-grade path;
    - Face to face: the top half is rotated (`Transform.rotate` π) and a reply lands in history;
    - onboarding: both steps, Skip, the chosen pair reaches the desk;
    - no `NavigationBar` or `BottomNavigationBar` in the tree.
  - File checks:
    - fonts declared in `pubspec.yaml` and present on disk;
    - storyboard shasum ≠ `3f6a9b27…`;
    - no `android.view.InputMethod` in the manifest;
    - no `ios/VerbaKeyboard` or `native/verba_llama` directory;
    - the M4 banned-string grep.
- Existing guards stay green: `release_sanity_test.dart`, `ads_consent_test.dart` (while ads remain), `privacy_choices_test.dart`, `translate_bookmark_test.dart` (adapted to Save to deck), and the foldable / large-text layout tests at 1.6×.
- `integration_test/store_screenshots_test.dart` drives the new flow (§6).
- **Commit path-limited:** `git add lib test integration_test assets pubspec.yaml pubspec.lock ios/Runner/Info.plist ios/Runner/Base.lproj ios/Runner/Assets.xcassets android/app/src/main android/app/build.gradle.kts`, plus the `git rm` of `native/verba_llama` and `ios/VerbaKeyboard`. Then push to `main`.
- **Never stage** `fastlane/**`, `ios/Podfile.lock`, `ios/Runner.xcodeproj/project.pbxproj`, `ios/Flutter/Generated.xcconfig` or `ios/Flutter/flutter_export_environment.sh`. All of them carry other people's uncommitted edits.
- **Known conflict:** adding `share_plus` and removing plugins will make CocoaPods rewrite `ios/Podfile.lock` on the next iOS build, and that file already has someone else's uncommitted changes. Do not commit or revert it. Report it to chief-of-staff so its owner commits first. No change to `project.pbxproj` is needed for anything in this spec: fonts are Flutter assets, and the deleted keyboard and shim were never in the Runner target.

### SHOULD (after the MUSTs are green)
- **"Other ways to say it"**: show up to 3 distinct `matches[].translation` values from the same MyMemory response, each with its `match` percentage and the label "MyMemory translation memory". Real data, already in the response; no extra request.
- Prefer on-device speech recognition (`SpeechListenOptions(onDevice: true)`) where the platform supports it for the language. Fall back to the standard recogniser, and state in Settings which one is used.
- Edit a card's translation, with a "edited by you" tag, for a local who corrected you.
- Import a CSV that was exported earlier.
- A home-screen quick action called "Review due phrases" that opens the same visible Review screen. It is not a hidden path.

## 5. Data source

- **Translation:** MyMemory public API, `https://api.mymemory.translated.net/get`. Keyless. Verified 2026-10-12 with curl (HTTP 200, `responseStatus 200`, real translations en→es and en→ja). It is the app's only functional network call. Anonymous daily allowance: when MyMemory says the quota is finished (the `quotaFinished` field in the live response), the M3 message is shown. No fallback text.
- **Speech:** the OS recogniser through `speech_to_text`, and the system TTS voices through `flutter_tts`. No server of ours.
- **On-device, in shared_preferences:** history `verba.history.v1`, deck and SRS state `verba.deck.v1`, the language pair, reminder settings, and the existing `ActivityStats` keys.
- **App content shipped in the binary:** Starter phrases (existing scenario and flashcard decks, written by hand). They are always labelled "Starter" and never shown as the user's.
- **No Supabase**, no account, no sample or seeded user data. Crash, analytics and performance data go through Firebase as today.

## 6. Store impact (proposed; store-compliance applies it, and I edited none of these files)

**Name:** keep "Verba". I recommend changing the store title from "Verba: Voice Translator" to **"Verba: Say It Back"** (18 characters). Availability is **not verified**: ASC returns a 409 only at creation. If the title stays, change the subtitle only.

**Subtitle (≤30):** "Translate it. Then say it." (26 characters). This replaces "Translate, talk & learn", which was also pasted in as the "audience".

**Promotional text:** "Translate what you need to say abroad, keep it, and practise saying it out loud — Verba listens and brings each phrase back right before you'd forget it."

**Description.** Rewrite it without the shared skeleton:
- Don't open with "Verba is…", and don't use `—— Heading ——` blocks.
- Drop "Material 3 interface with glassmorphic cards" and every mention of Talk, conversation AI or "AI".

Proposed opening: "You don't need a whole language for a trip. You need the forty sentences you'll actually say — and to be able to say them without holding up your phone." Then cover, in prose:
- typed and spoken translation in 12 languages;
- Face to face;
- Save to deck;
- spoken review with words heard highlighted (per character for Chinese and Japanese);
- reminders only when phrases are due;
- Show it;
- history and search;
- CSV export;
- what works offline.

Keep the existing translation-quality disclaimer paragraph, which is honest and useful. Keep the ads sentence only if Q3 keeps AdMob. Keywords: `phrasebook,translate,speak,travel,spaced repetition,flashcards,pronounce,offline,phrases,voice`.

**Category:** keep primary EDUCATION. Add secondary TRAVEL.

**Screenshots: retake every one.**
- The current ASC records disagree. `docs/apple-requirements.json` says the iPhone 6.7" and iPad first screenshot **shows another app (Photriya)**, while `docs/screenshot-audit.json` OCRs a Verba Translate screen. Apple also issued 2.3.3. Either way, they don't show the new app.
- New set for iPhone 6.9" and iPad 13", produced by the integration test driving the real UI from a fresh install, with live MyMemory translations entered by the test:
  1. the Phrase desk with a translation and its phrase card;
  2. a Review card after Say it, with heard words highlighted and the proposed grade;
  3. the Deck with search and the "Due now" filter;
  4. Face to face, split and rotated;
  5. Show it, in large type.
- No settings screen, no software keyboard on shot 1. Replace the Play feature graphic and phone/tablet shots with the new icon and identity.

**Review notes.** Rewrite them from scratch:
- No "2. DEVICES…" skeleton, and no "simulators… a build that cannot start never ships" claim. Testing is stated only as actually done; physical-device testing only if it happened (Q6).
- **Audience:** the §2 paragraph, not the subtitle.
- **Steps:** "Open the app → pick the language you need (e.g. Portuguese) → optionally add Restaurant starter phrases → type 'Where is the pharmacy?' → Translate → Save to deck → tap 'Due today' → Hear it → Say it (allow the microphone when asked) → see words heard and the proposed grade. Face to face, Deck and History are in the top bar."
- **External services:**
  - MyMemory (translation text);
  - the device speech recogniser (Apple / Google);
  - Firebase Crashlytics, Analytics and Performance;
  - Google AdMob, only if Q3 keeps it.
- **Remove "Apple In-App Purchase — paid features"** from anything sent to Apple. Verba has none, and the 2026-09-29 reply was wrong to list it.
- **5.6 statement:** "Every feature in this binary is visible from the first screen. The earlier Talk and Buddy screens and the Android keyboard were removed from the code, not hidden."
- No account, so no deletion.

**Differentiation (`differentiation` in Verba.json):**
- §1 "Screens it contains": desk, history, deck, review, face to face, show it, settings, onboarding. Drop the "hidden in this build" sentence.
- §3 gap: the §3 angle, with competitor statements marked as needing verification.
- §5: re-measure the similarity after the build (the "iMaps at 49%" figure was measured before the removal).
- §7: shared code is only agl_observability, plus agl_ads if Q3 keeps it.
- §8 framework list: drop flutter_riverpod if removed, add share_plus.

**Privacy label.** Today Verba shares the 20-app label. Proposed for Verba alone:
- Keep: CRASH_DATA, PRODUCT_INTERACTION and PERFORMANCE_DATA (not linked).
- Add **OTHER_USER_CONTENT** (text sent to MyMemory for translation; not linked; App Functionality).
- Keep DEVICE_ID and ADVERTISING_DATA only if Q3 keeps AdMob.

Whether audio handled by Apple's or Google's recogniser must be declared is for store-compliance to confirm (**not verified**).

**Release notes:** "Verba now remembers: every translation goes to History, and anything you save becomes a card you practise by saying it out loud. Chinese and Japanese practice now checks each character. New Face to face mode, new look."

## 7. Out of scope

- An on-device LLM conversation partner, LLM translation, and the reply-suggestion keyboard. The keyboard is AGrammarly's job and Verba must not duplicate it. The LLM is founder question Q1.
- On-device or offline machine translation (ML Kit, Apple Translation framework). Both need new native dependencies or Swift in the Runner target, and `project.pbxproj` carries someone else's uncommitted edits.
- Accounts, sync, Supabase, other UI languages, and new paid features.
- Editing `store/apps/Verba.json`, `store/privacy/Verba.json`, fastlane metadata or `docs/`. Uploading, submitting or replying to Apple (5.6 freeze, MA-043).
- Placing new ads or changing ad configuration (Q3).
- The live website privacy policy text (Q4).

## 8. Founder questions

1. **On-device LLM (Talk) and keyboards.** The portfolio brief says Verba owns "an on-device LLM". No shipped build can run one (§0: llama.cpp not vendored; shim not in the iOS target), and enabling it means vendoring llama.cpp, adding the shim to the Runner target in `project.pbxproj`, and 0.4-2.4 GB model downloads. I recommend removing Talk, the model manager and both keyboards from this release (M4) and treating an LLM speaking partner as a separate later project. Approve?
2. **Buddy (from the LocalBuddy merge).** Removing Buddy (Chat / Roast / Daily Challenge / Party Questions / Game Coach, plus kid-safe profiles) retires what is left of LocalBuddy's features. That may count as "removing products" (Charter §8). Approve removing it from Verba? If not, it can't stay hidden: it would need the Q1 LLM work before Verba can be resubmitted.
3. **AdMob in Verba.** The SDK and consent run, but no ad is ever shown and 4 real ad units are missing (`MANUAL_ACTIONS.md:615`). Should we remove AdMob from Verba (simpler privacy label, no "Privacy choices"), or keep it for future placements (a money decision)?
4. **Legal text.** The website policy at `americangroup.ai/policy/verba/` probably still describes Talk, Buddy and affiliates (the unused in-app copy did; the live page was **not verified**). Approve an update that describes history and deck storage on the device and MyMemory?
5. **Resubmission and reply.** After this ships to TestFlight, do you approve a resubmission and answers to Apple's 9 questions? Those answers would correct the earlier false IAP line (Charter §1, 5.6 freeze MA-043).
6. **Physical device.** Apple asked for a screen recording on a physical device with the latest iOS (`store/recordings/Verba.mov`). Only a person with a device can make it.
7. **Review contact.** Can a real person's name replace "App Reviewer"?
8. **Play.** The Play prod draft is staged with the old build, which includes the "Verba Keyboard" input method. Should it be held, not promoted, until this version is built?
