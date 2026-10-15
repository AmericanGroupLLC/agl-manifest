# Spec — AGrammarly: replies in your own voice

Author: product-manager (AI office) · Date: 2026-10-12 · Project: real-apps (plan.md)
Repo: `/Users/spatchava/agl/AGrammarly` (app in `mobile/`) · branch `main` · base_sha `b56e810bad4c4d99b988a117c32d920b0bc09760`
Store state: Apple rejected under 4.3 / 4.2.6, then 2.3.3 (outdated screenshots) · Google Play `PRODUCTION_DRAFT_STAGED`

---

## 0. What exists today (measured at base_sha)

What I read: all 17 files in `mobile/lib/` (3,024 lines), `pubspec.yaml`, `ios/Runner/Info.plist`,
`ios/Runner/Base.lproj/LaunchScreen.storyboard`, `assets/icon/app_icon.png`, the test list, and
`store/apps/AGrammarly.json`. I also read Apple's text in `.dist/rejections.json["AGrammarly"]`.

Baseline checks, run 2026-10-12 with `--no-pub` so `pubspec.lock` stayed unchanged:
- `flutter test` gave `+270: All tests passed!`
- `flutter analyze` gave `No issues found!`
- `git status` showed no new changes. The only edits that were already there are other people's: `mobile/fastlane/**` and `mobile/ios/Podfile.lock`.

| Area | File | State |
| --- | --- | --- |
| Entry / onboarding gate | `lib/main.dart` | Works. Material 3 only, `ThemeMode.system`, no font. |
| Onboarding | `features/onboarding/onboarding_screen.dart` | One screen: generic hero "Replies that sound like you", an `_InfoCard`, and a Start button. The Cloud `_ModeCard` choice (l.55-87) is unreachable because `kApiBase` is empty. |
| Shell | `features/shell/main_shell.dart:83` | The shared 3-tab `NavigationBar` (Home / Keyboard / Settings) with Material icons. This is a portfolio tell. |
| Home | `features/home/home_screen.dart` | A stats dashboard: 3 counter tiles, a "YOUR EMOJI" wrap, and a "How it works" card. Shows only counters, so you can't do anything from it. |
| Core flow | `features/keyboard/keyboard_screen.dart` | **This is the real job.** You type the incoming message into a TextField, and 3 tone chips appear (casual / professional / short). Tapping a chip fills the reply. You can edit the reply **only with the drawn QWERTY replica**. The system keyboard cannot edit it. Copy puts the reply on the clipboard and the reply is learned. "Earlier replies" lives only in memory and is lost on restart. |
| Keyboard | `widgets/native_keyboard.dart` | A QWERTY replica drawn in the app, with shift / 123 / #+= and a `SuggestionBar`. It is not a system keyboard (comment l.7-10). As a way to type, it is worse than the system keyboard: no autocorrect, no dictation, no other languages. |
| Engine | `core/engine/suggestion_engine.dart`, `response_patterns.dart` | Real and on-device. It matches 17 regex patterns, each with 3 replies written for the slot. When nothing matches, it falls back to the user's learned phrases (newest first, sorted by tone) and then to `kGenericReplies`. `generateCloud` (l.147-191) posts to `$apiBase/api/trpc/...`, but `kApiBase` defaults to `''` (`state/app_state.dart:36`), so this is **dead code** that still pulls in `package:http`. |
| Learning | `learnFromMessage` (engine l.206) | Keeps 2-8 word replies, at most 50, plus emoji counts. It also stores `avgMessageLength`, which **nothing reads**, and declares `preferredTone`, which **nothing ever sets**. |
| Storage | `core/storage/style_store.dart` | Uses shared_preferences under `@animus/*` keys. `isPremium`/`setPremium` are dead (the comment at l.94-101 says so). |
| Settings | `features/settings/settings_screen.dart` | Shows the On-device radio (the only option) and the copy "This build has no cloud suggestions service configured" (l.57-59), which is a template tell. Also About, Privacy policy, Support, and "Clear everything learned". |
| About | `features/about/about_screen.dart` | Hard-codes "Version 1.0.0" (l.37) while pubspec says `1.0.0+4`, and says "this build has no cloud suggestions service configured" (l.65-69). |
| Crash wiring | `core/services/error_reporter.dart` | An exact copy of the file shared by 13 apps (tell list). |
| Theme | `core/theme/app_theme.dart` | Green `0xFF0D6E4F` / `0xFF1DB87A`, `useMaterial3: true`, no font. 0.33 Jaccard twin of NewsBoard. |
| Brand | `Info.plist:10` `CFBundleDisplayName` = `Agrammarly`; `AndroidManifest.xml:3` `android:label="agrammarly"` | Still the `flutter create` casing, and it differs from the store name "AGrammarly: Reply Helper". |
| Icon | `assets/icon/app_icon.png` | Green text lines and a green check-mark badge on a dark-green gradient. My reading (not measured): it looks like a grammar or correction checker, which this app is not, and it echoes Grammarly. |
| Splash | `LaunchScreen.storyboard` | shasum `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`. That is the shared white storyboard found in 37 apps. |

Honest summary: the reply engine is real, but the app around it is shallow. Replies are lost on restart. Typing happens on a fake keyboard. The home screen is a counter dashboard. Cloud and premium code is dead. Identity comes from the shared scaffold, and the name, colour and icon all echo Grammarly.

## 1. Problem

Apple sees a reskinned scaffold ("indistinguishable from what's already widely available… opportunistic variant of an existing… popular app", 4.3(b) and 4.2.6). It sees a name that borrows a famous trademark, and screenshots that are out of date (2.3.3). The ASC screenshot audit in `docs/APPLE_REQUIREMENTS.md:34` found the first iPhone and iPad screenshots show an **iOS home screen, not this app**.

A user sees a toy. Nothing they write is kept, the reply has to be typed on a drawn keyboard, and the "learning" can't be seen and doesn't change much: it only offers back old phrases when no pattern matches.

## 2. User

People who answer a lot of short personal and semi-work messages every day: shift workers coordinating cover, parents in school group chats, small-business owners answering customer DMs. They answer the same kinds of message again and again ("are you free", "running late", "thanks!"). They want a reply that sounds like *them*, not like a generic assistant. They don't want their messages sent to a server.

The app is English only (`kSupportedLocales = [Locale('en')]`, `main.dart:40`).

**Core job:** *Paste the message you got. Get three replies that already sound like you. Send one in two taps.*

## 3. The honest angle and the signature feature

**Competitors: not verified.** WebSearch is disabled in this session ("Internet mode is not enabled"), so I can't name or describe Gboard Smart Reply, Apple's Smart Reply, Grammarly's keyboard or text-expander apps as fact. The comparison below names no competitor. Before any reply to Apple uses competitor claims, someone with web access must check them.

**Signature feature: Voice Match.** The app measures how *this* user writes from the replies they actually send. It rewrites every suggestion into that style, shows them which rules it applied, and brings back replies they wrote before to similar messages. All of this runs on the device, is visible and can be edited. There is no model, no server and no account.

It has two parts. Both are buildable now in Dart, on the device, with no key and no API.

**(a) Voice profile and rewrite.** Computed from the user's saved replies, which only grow through Copy / Share or onboarding input.

| Trait | Measured as | Applied to suggestions when |
| --- | --- | --- |
| Lowercase | share of replies with no capital letters | ≥ 0.6: casual and short replies are lower-cased |
| Full stops | share of replies ending in `.` | < 0.3: trailing `.` removed |
| Exclamations | share containing `!` | < 0.15: `!` becomes `.` (or is dropped if full stops are off). ≥ 0.5: kept. |
| Emoji | share containing emoji, plus the user's top emoji | < 0.15: emoji stripped. Otherwise the suggestion's emoji is replaced by the user's top emoji. |
| Short forms | fixed pair list: thanks/thx, you/u, your/ur, okay/ok, please/pls, tomorrow/tmrw, by the way/btw, see you/cya | the user's short form appears ≥ 2 times and more often than the long form: the substitution is applied |
| Opener | most frequent first word from {hey, hi, hello, hiya, yo} | ≥ 2 uses: replaces the suggestion's opener |

Rules:
- The **professional** slot keeps sentence case, full stops and long forms by definition. Only emoji stripping applies to it.
- Below **5 saved replies** no trait is applied. The UI says so honestly, for example "Learning your voice — 2 of 5 replies", with no invented profile.
- Each rewritten suggestion carries the list of rules applied, shown as small "why" tags (e.g. `lowercase · no full stop · thx`).

**(b) Reply memory ("You said before").** When the user copies or shares a reply, the pair *(message received, reply sent, tone, time)* is saved. A new incoming message is tokenised (lower-case, punctuation stripped, small stop-word list) and scored against stored incoming messages by token overlap (Jaccard). If the best score is ≥ 0.34, its stored reply is shown **as written** above the three tone replies, labelled "You said before · <date>". It is never rewritten and never invented.

## 4. Acceptance criteria

### MUST (what Apple needs to see a real, distinct app)

**M1. The reply desk is the home screen and does the core job end to end.**
- After onboarding the app opens on a single **Reply desk** screen. There is no bottom NavigationBar or NavigationRail shell.
- It has a "Message you got" field with a **Paste** button (`Clipboard.getData`, run only when the user taps it).
- Below that, a "You said before" card appears when there is a match (M2b), followed by three tone replies drawn as chat bubbles.
- Tapping a reply puts it into **"Your reply", a real `TextField` edited with the system keyboard** (autocorrect, dictation and every system language work).
- **Copy** puts the reply on the clipboard. **Share** opens the system share sheet (`share_plus`) so the reply can go straight to Messages, WhatsApp or Mail.
- A successful Copy or Share saves the *(incoming, reply, tone, timestamp)* pair (M3). A failure shows an error snackbar and saves nothing.
- Library, Voice and Settings are reached from app-bar actions with `Navigator.push`.
- Acceptance check: on a fresh install, after onboarding, entering "are you free later?" shows three labelled replies. Tapping one, editing it with the system keyboard and tapping Copy shows "Copied" and leaves one entry in Library after the app restarts.

**M2. Signature: Voice Match, as specified in §3.**
- (a) A pure-Dart `VoiceProfile.fromReplies(List<String>)` and `VoiceProfile.apply(Suggestion)`. `apply` returns the rewritten text plus the list of applied rules. It follows exactly the thresholds in the §3 table and the 5-reply minimum. Applied rules show as tags under each bubble.
- (b) `ReplyMemory.bestMatch(incoming)` with the ≥ 0.34 threshold. The match is shown verbatim with its saved date.
- A **Voice screen** shows the measured profile from the user's own data: each trait, its measured share, and "based on N replies". Below 5 replies it shows the "Learning your voice — N of 5" state instead. Each trait has a switch to turn it off, and the switch persists. "Erase my voice" lives here and in Settings.
- Nothing on this screen is a seeded or sample value.

**M3. Depth: persistence, library, search, export, and states.**
- Saved pairs persist across restarts (shared_preferences JSON or a JSON file; developer's choice), capped at 500 with the oldest dropped first.
- On first launch after the update, the existing `@animus/user_style` `commonPhrases` are migrated into the library as replies with an empty incoming message. Nothing learned is lost. Then `@animus/premium` and `@animus/llm_mode` are deleted.
- **Library screen:**
  - newest first;
  - search across incoming and reply text;
  - filter chips All / Pinned / Casual / Professional / Short;
  - pin and unpin;
  - edit the reply;
  - swipe to delete with an Undo snackbar;
  - **Export** as a plain-text file ("Message: … / Reply: … / Date: …") through the share sheet.
- Empty states have their own copy:
  - Library: "Replies you copy or share land here."
  - Search: "No saved reply contains '<q>'."
  - Clipboard has no text: "Nothing to paste — copy the message first."
- The app needs no network for any feature. There is no "offline" banner, because nothing goes offline.
- Storage write failures are caught, sent to `ErrorReporter.report`, and shown as an error snackbar.

**M4. Dead code and dishonest copy removed.**
- Delete: `LLMMode.cloud`, `kApiBase` / `kCloudSuggestionsAvailable`, `generateCloud`, `Suggestion.fromJson`/`toJson` wire code, the onboarding `_ModeCard` and `WHERE SHOULD SUGGESTIONS RUN?`, the Settings Cloud tile and its "This build has no cloud suggestions service configured" text, and the About "this build…" sentence.
- Remove the `http` dependency from `pubspec.yaml`.
- Delete `isPremium` / `setPremium` / `premiumKey` and `AppSettings.isPremium`.
- Delete the unread `avgMessageLength` and the never-set `preferredTone`, or give them a real use in VoiceProfile.
- Show the About version from `package_info_plus` (already in `pubspec.lock` through agl_observability) instead of the literal "Version 1.0.0".
- A test greps `lib/` and fails on `this build`, `coming soon`, `not connected`, `not available yet`, `cloud`, `premium`, `Simulator mode`.

**M5. Own identity, in code.**
- **Colour.** Seed `#E4572E` ("postbox vermilion").
  - Light: background `#FBF6EE` (paper), surface `#FFFDF8`, ink `#232838`, muted `#6E6A63`.
  - Dark: background `#15181F`, surface `#1F2430`, ink `#F3EDE2`, accent `#FF7A52`.
  - The green palette is removed.
  - Checked: `git grep -il 0xff<hex> -- '*.dart'` across every repo under `/Users/spatchava/agl` found **none** of these 9 hexes in any app. None is a Tailwind default.
- **Type.** Bundle the fonts as assets. No `google_fonts` runtime fetch, because the app has no network.
  - **Fraunces** (variable) for display and headings.
  - **Atkinson Hyperlegible** Regular and Bold for body, UI and reply bubbles.
  - Ship the OFL licence texts in `assets/fonts/` and register them with `LicenseRegistry`.
  - Sources resolve: `curl` HTTP 200 for `github.com/google/fonts/raw/main/ofl/fraunces/Fraunces%5BSOFT,WONK,opsz,wght%5D.ttf` (360,440 B), `.../atkinsonhyperlegible/AtkinsonHyperlegible-Regular.ttf` (54,348 B), `-Bold.ttf` (55,256 B) and `.../fraunces/OFL.txt`.
  - `git grep -il -e fraunces -e atkinson` across all repos found no other app using either font.
- **Shape language.**
  - Keycaps: radius 8 with a 1 px bottom shadow, carried over from `_Key`, on buttons and cards.
  - Chat bubbles: radius 18/18/18/4; incoming bubbles on the left in the surface colour, replies on the right in a tint of the accent.
  - No `BorderRadius.circular(12)` anywhere in `lib/`.
- **Icons.** `CupertinoIcons` everywhere; `cupertino_icons` is already a dependency. No other app of the 43 uses them (tell list).
- **Keyboard.** `widgets/native_keyboard.dart` becomes **ReplyPad**: a keycap grid of the user's **pinned replies and top emoji**. One tap inserts the item into "Your reply". It is docked under the editor while the system keyboard is hidden. `SuggestionBar` stays. The QWERTY / number / symbol letter layers are removed, because the system keyboard now does the typing.
- `useMaterial3` may stay. Dialogs and switches use `.adaptive` constructors (`showAdaptiveDialog`, `Switch.adaptive`).

**M6. Template tells removed: icon, splash, display name, crash panel.**
- **New launcher icon.** No green, no check mark, and not a Material glyph on a gradient: a vermilion speech bubble shaped like a keycap on a paper-coloured square, drawn by our own script or vector. Regenerate with `flutter_launcher_icons`, and set `adaptive_icon_background` to `#FBF6EE`.
- **New splash.** `LaunchScreen.storyboard` background `#FBF6EE` and the new mark, so its shasum is no longer `3f6a9b27…`. Android `launch_background` gets the same colour and mark.
- **Display name.** `CFBundleDisplayName`, `CFBundleName` and `android:label` all equal one `kAppName` constant used in the app (about, title). Whatever the founder decides (Q1), the casing has to be correct (`AGrammarly`, not `Agrammarly`).
- **Crash panel.** `error_reporter.dart` keeps its behaviour and tests, but its `_FriendlyErrorPanel` uses this app's palette and copy. That breaks the 13-app byte-identical file.

**M7. Own onboarding and settings copy.**
- **Onboarding is "Teach it your voice", 2 steps.** No "Get started" or `actionStart`/"Start".
  1. One sentence on what the app does. Up to three optional fields, "Paste a reply you sent recently". Entries are saved as library replies with an empty incoming message. A **Skip** button is always visible.
  2. The measured voice from what was entered, using the M2 screen component. If fewer than 5 replies were given, it shows the honest "Learning" state. The button reads "Open the reply desk".
- **Settings sections:**
  - "Your voice": trait switches, then "Erase my voice and saved replies…" with an adaptive confirm dialog.
  - "Library": Export replies.
  - "About": version, Privacy policy, Support, open-source licences.
- No shared Language screen. The app is English only.

**M8. Proven.**
- `flutter analyze` is clean and `flutter test` passes. No test is deleted or skipped to get green. Tests that check removed behaviour (the cloud mode, the QWERTY replica, the 3-tab shell) are **rewritten** to the new behaviour, and each rewrite is listed in the commit message.
- New tests, at least:
  - VoiceProfile: each trait threshold at its boundary, the 5-reply minimum, the professional slot untouched, the rules list.
  - ReplyMemory: match at ≥ 0.34, no match below it, the date shown, the stored reply returned verbatim.
  - Storage: round trip, the 500 cap, migration from `@animus/user_style`, deletion of `@animus/premium` / `llm_mode`.
  - Widgets:
    - the reply desk flow (paste, then 3 bubbles, then tap, then edit, then Copy, then Library has 1 entry after the container is rebuilt);
    - Library search, filter, pin, delete and undo;
    - Export text content;
    - onboarding Skip and Teach paths;
    - no `NavigationBar` in the tree.
  - File checks: `Info.plist` `CFBundleDisplayName == kAppName`; font assets present in `pubspec.yaml` and on disk; the storyboard shasum ≠ `3f6a9b27…`; `http` absent from pubspec; the banned-string grep from M4.
- Existing guards stay green: `privacy_test.dart`, `release_sanity_test.dart`, and the foldable / layout tests at 1.6× text.
- Update `integration_test/store_screenshots_test.dart` to drive the new flow (§6).
- Commit path-limited (`git add mobile/lib mobile/test mobile/integration_test mobile/assets mobile/pubspec.yaml mobile/pubspec.lock mobile/ios/Runner/Info.plist mobile/ios/Runner/Base.lproj mobile/ios/Runner/Assets.xcassets mobile/android/app/src/main`), then push to `main`.
- **Never stage** `mobile/fastlane/**` or `mobile/ios/Podfile.lock`. Both carry other people's uncommitted edits right now (`git status` above).
- **Known conflict:** adding `share_plus` will make CocoaPods rewrite `ios/Podfile.lock` on the next iOS build, and that file already has someone else's uncommitted `url_launcher_ios` lines. The developer must not commit or revert that file. Report it to chief-of-staff so its owner commits first.

### SHOULD (after the MUSTs are green)
- Import a previously exported library (a JSON export alongside the text export).
- Extend the pattern set beyond the 17 situations in `response_patterns.dart`: running late, can you cover my shift, school pick-up, order status, rescheduling. Each needs 3 slot-correct replies and a test like the existing slot tests.
- A home-screen quick action (iOS `UIApplicationShortcutItems` / Android shortcuts) called "Reply to copied message". It opens the desk with Paste pre-tapped. It must open the same visible screen: no hidden path.
- Theme the `SuggestionBar` chips with the same "why" tags as the bubbles.
- Count "Replies sent" on the Voice screen from real Copy and Share events. This replaces the old keystrokes-saved tile, which was counted on chip *tap* even when the reply was never used (`keyboard_screen.dart:53-56`).

## 5. Data source

- **On-device only.** The data is the pattern set shipped in the binary, the user's own saved replies and pairs, and the trait switches. It is stored in shared_preferences or an app-documents JSON file. The rewrite and the matching are pure Dart.
- **No Supabase. No public API.** Neither is needed. After M4 removes `http`, the only off-device traffic is Crashlytics crash reports (`AglCrash.init`, `main.dart:23`). That matches `store/privacy/AGrammarly.json` (CRASH_DATA, not linked, app functionality).
- No sample, seed or fallback user data. Generic pattern replies are app content, labelled by tone, and never presented as the user's.

## 6. Store impact (proposed; store-compliance applies it, and I edited none of these files)

**Name** (founder decision, Q1). Today: "AGrammarly: Reply Helper". I recommend moving off the Grammarly echo. Candidate names, **availability not verified** (ASC returns a 409 only at creation): "Rejoinder: Replies in Your Voice", "ReplyBook: Your Own Replies". If the founder keeps the name, at least fix the device name casing (M6).

**Subtitle (≤30):** "Replies in your own voice" (25 chars). Replaces the current subtitle, which was also pasted in as the "audience".

**Promotional text:** "Paste a message, get three replies rewritten in the way you actually text — lowercase, your emoji, your shorthand — and see the replies you sent before to the same kind of message."

**Description.** Rewrite it without the shared skeleton: don't open with the app name, no `—— Heading ——` blocks, no "this build ships with no suggestions service configured", and no closing negations section. Proposed opening: "Most suggested replies sound like nobody. This one learns how you text from the replies you actually send — whether you write in lowercase, skip full stops, say 'thx', reach for 😂 — and rewrites every suggestion to match. Each suggestion shows what it changed and why." Then, in prose:
- the reply desk and Share;
- "You said before";
- the Library with search and export;
- Voice switches;
- everything stays on the phone, and the only network use is crash reports.

It must not claim grammar checking, AI or a language model.

**Keywords:** `reply,replies,texting,voice,style,shorthand,emoji,messages,phrasebook,offline,private`

**Screenshots: retake all of them.** The ASC iPhone and iPad screenshot 1 is an iOS home screen (`docs/APPLE_REQUIREMENTS.md:34`). iPhone 1 and 2 are near-identical, and 4 is Settings (tell list). New set, iPhone 6.9" and iPad 13", each produced by the integration test driving the real UI:
1. Reply desk: a message pasted, three bubbles with "why" tags.
2. The "You said before" card on top of the replies.
3. The Voice screen with the profile measured from replies the test actually entered through onboarding and the desk. This is real app use in the test run, not seeded constants.
4. Library with a search term and a filter chip.

No Settings screen and no software keyboard on screenshot 1 (2.3.3 gate). Also replace the Play feature graphic and phone/tablet shots with the new icon and identity.

**Review notes.** Rewrite them from scratch:
- No "2. DEVICES…" skeleton.
- No simulator-only testing claim. State physical-device testing only if it actually happened.
- "Intended audience" is the §2 paragraph, not the subtitle.
- Reaching the feature: "Open the app, tap Skip or paste three replies you've sent, paste or type any message (e.g. 'are you free later?'), tap a reply, tap Copy or Share; open Library and Voice from the top bar."
- External services: Crashlytics crash reports only. The app has no network features.
- No account, so no deletion.

**Differentiation §3 (gap):** the Voice Match text from §3. Mark the competitor comparison as needing verification before it is sent.

**Privacy label:** unchanged (crash data only, not linked). Re-run the label derivation after `http` is removed to confirm.

**Category:** stays PRODUCTIVITY.

## 7. Out of scope

- A real system keyboard: an iOS custom keyboard extension or an Android InputMethodService. It needs new native targets, a new App ID, an App Group and provisioning profiles, and Apple 4.4.1 keyboard rules. That is founder question Q2.
- Grammar or spelling correction, LLM or cloud suggestions, and accounts or sync.
- Translation and language practice, which belong to Verba. Other UI languages: the app stays English only.
- Editing `store/apps/AGrammarly.json`, fastlane metadata, or `docs/`. Uploading, submitting or replying to Apple (5.6 freeze, MA-043).
- Ads. The app has no ad SDK and stays that way.

## 8. Founder questions

1. **Rename (strongly recommended).** "AGrammarly" pairs the house "AG" prefix with the Grammarly trademark. Apple named "opportunistic variant of an existing … popular app" in this rejection (4.3(b)). Approve a new name (candidates in §6, availability not verified), or keep it?
2. **System keyboard v2.** Should we build a real iOS keyboard extension and Android IME that insert Voice-Matched replies in any app? It needs a new bundle ID, an App Group and provisioning (Charter §4 accounts), and it is a multi-day native job.
3. **Review contact.** Can a real person's name replace "App Reviewer" in review information?
4. **Resubmission and reply.** After this ships to TestFlight, do you approve a resubmission and a new answer to Apple's 9 questions (Charter §1, 5.6 freeze MA-043)?
5. **Play.** The Play build is `PRODUCTION_DRAFT_STAGED` with the old name, icon and copy. Should it be held instead of promoted until this version is built?
