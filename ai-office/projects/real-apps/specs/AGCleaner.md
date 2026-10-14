# Spec: AGCleaner becomes a contact-dedup product people can trust

- Author: product-manager (AI office), 2026-10-12
- Repo: `/Users/spatchava/agl/AGCleaner`, branch `main`, base_sha `3cd3cafff0b76f136754b30dc83d0b5d61fc21ef`
- Apple: rejected under **5.6** (2026-10-08T14:19:48Z, `/Users/spatchava/agl/.dist/rejections.json` key `AGCleaner`, the same 5.6 message sent to 16 apps within the same minute). Google Play: PRODUCTION_DRAFT_STAGED.
- Plan: `projects/real-apps/plan.md` (seven acceptance criteria). Overlap: `projects/real-apps/overlap.md:54` (AGCleaner owns duplicate contacts and identical photos on the device. No overlap with any sibling).
- Baseline, measured today: `flutter analyze` gives "No issues found! (ran in 65.4s)". `flutter test` gives "+120: All tests passed!".

**Uncommitted work by other people is in this repo. Do not touch it:** `fastlane/**` (13 modified, 8 untracked screenshots, `fastlane/metadata/review_information/notes.txt`) and `ios/Podfile.lock`. No file this spec asks you to change (lib/, test/, pubspec.yaml, ios/Runner/Info.plist, ios/Runner/Base.lproj/LaunchScreen.storyboard, ios/Runner/Assets.xcassets, android/app/src/main/AndroidManifest.xml, android/app/src/main/res) has uncommitted edits right now (`git status --short`). If that changes before you start, stop and report it.

---

## 1. Problem

### What the app is today (read in full: all of `lib/`, 1225-line `lib/main.dart`)

| Area | State | Evidence |
|---|---|---|
| Contacts duplicate finder | **Real.** It reads the address book (read-only), groups entries with union-find on normalised phone (last 9 digits), email and sorted-token name, and shows which signal matched. | `lib/domain/contact_duplicates.dart:104-260`, `lib/data/device_sources.dart:31-65` |
| Contacts action | **Dead end.** The app finds groups, then the user can do nothing with them: no merge, no open-in-Contacts, no dismiss, no export. The copy says so: "AGCleaner only finds duplicates. It never edits or deletes a contact." | `lib/l10n/app_en.arb` `contactsReadOnly`, `lib/main.dart:879-940` (cards have no actions) |
| Identical photos | **Real.** Bucket by size, SHA-256 the candidates, keep-one rule enforced twice, system-confirmed delete, honest freed total. Photos only, no videos. | `lib/domain/photo_duplicates.dart`, `lib/domain/photo_scan.dart`, `lib/main.dart:342-412` |
| Cache tab | Real, but trivial. It measures and clears **this app's own** temp dir. A full tab for it is "cleaner"-category filler. | `lib/main.dart:743-801`, `lib/data/device_sources.dart:184-224` |
| Persistence | **None.** Every result is lost on relaunch. No history, no "not a duplicate" memory. | no storage code in `lib/` |
| Search / filter / export | **None.** | - |
| Onboarding / settings | None. A language pill and a region-conditional "Privacy choices" pill sit in the header. | `lib/main.dart:469-556` |
| Identity | Template. `class C` palette monolith (`lib/main.dart:44-54`) with Tailwind hexes A855F7/10B981/F59E0B/A1A1AA/71717A/3F3F46. Dark-only `ThemeData` (`lib/main.dart:103-111`). System font. Three equal painted tabs. Generated glyph icon (`scripts/generate_app_icons.py`, `cleaning_services`). Shared splash storyboard (sha1 `3f6a9b27d8...`, re-measured today). Home-screen name `Agcleaner` (`ios/Runner/Info.plist:10`), Android label `agcleaner` (`AndroidManifest.xml:37`). pubspec description is "A new Flutter project." |
| Ads | AglAdBanner below content (`lib/main.dart:462`). Interstitial on tab switch (`lib/main.dart:430-436`). |

### Why Apple would see a template or hidden features
1. **4.3(b) generic cleaner, already built into the OS.** I checked Apple's own guides with curl today. iOS Photos already "identifies duplicate photos and videos in your photo library in the Duplicates collection" and merges them (support.apple.com/guide/iphone/iph1978d9c23). iOS Contacts already merges duplicates, **but only "if you have more than one contact card with the same first and last name"** (support.apple.com/guide/iphone/iph2ab28320d). Google Contacts merges duplicates, **but "You can't merge contacts that are saved in different Google Accounts"** (support.google.com/contacts/answer/7078226). Today AGCleaner finds what the OS finds and then does less than the OS does, because it cannot act.
2. **5.6 candidates in this binary.** Anything a reviewer could read as behaviour that changes outside review:
   - `AglInsights.init` starts Firebase **Remote Config** and calls `fetchAndActivate()` (`packages/agl_observability/lib/src/insights.dart:104-125`). AGCleaner reads no flag (grep of `lib/` for `AglInsights.flag`/`setting` finds nothing), but the SDK and the fetch are in the binary.
   - The "Privacy choices" control **appears only in some regions** (`lib/main.dart:513`). This is legally required, but it is region-dependent UI in the header.
   - Store screenshots come from `--dart-define=SCREENSHOT=true` builds, which never load ads (`packages/agl_ads/lib/src/ads.dart:38-41`). The listing therefore shows a different screen from the one users get.
   - Git history says the app shipped invented contacts, "RAM" gauges and stock photos until 2026-09-15 (`test/no_demo_data_test.dart:1-9`, commit `7f7c254` mentions screenshots "signed in with the QA account" for an app that has no sign-in). Apple may still be judging the earlier build. **Not verified.** The rejection text names no feature.
3. **Its own copy says it does not do its job.** 45% of the description's sentences are negations ("It does not claim to do anything else", "WHAT IT CANNOT DO").

## 2. User and product decision

**User:** someone whose phone has gathered the same people several times over from iCloud, Gmail, a work Exchange account, an old SIM import and WhatsApp/CRM syncs. Typically this is a small-business owner, a salesperson or a family "IT person" with 500 to 5,000 contacts. Their real problem: the "Jane Smith" card in Gmail and the "Mom" card in iCloud share a number, so caller ID shows the wrong card and edits never reach both.

**Core job (one, done well):** find every set of cards that describe the same person, **even when the names differ or the cards live in different accounts**, show the evidence for each match, and fix the set safely in place.

**Signature feature: "Cross-account match + Merge with a restore point."**
- Finds duplicates by shared phone/email across **every contacts account on the device**, and labels each card with the account it lives in (iCloud / Gmail address / Exchange / On this phone). `flutter_contacts` 2.5.0 exposes this as `Contact.metadata.accounts` (`~/.pub-cache/hosted/pub.dev/flutter_contacts-2.5.0/lib/models/contact/contact_metadata.dart`: "Accounts this contact belongs to", `Account.name` e.g. "user@gmail.com", `Account.type` e.g. "com.google").
- **Merge** writes one complete card (the union of numbers, emails, addresses, dates and organisation, with the user's choice of name and photo). **Before anything is changed**, it saves every original card as a vCard 3.0 file on the device (`FlutterContacts.vCard.export`, `api/vcard_api.dart:22`). Each merge appears under **Restore points**, and one tap restores the original cards (`vCard.import` + `FlutterContacts.create(contact, account:)`, `api/crud_api.dart:66`).
- Why it is distinct (sources verified today, quoted in section 1): Apple Contacts matches on same first+last name only, and Google Contacts cannot merge across Google accounts. A fix you can undo is AGCleaner's honest angle. Paid third-party cleaners: **competitor not verified** (web search was unavailable in this session, so no claim is made about them anywhere, including the store copy).
- Data: 100% on-device. No network, no Supabase, no API.

**Photos stay a secondary tab:** byte-identical photos (and, per SHOULD, videos). Never a gallery and never editing (that is Photriya's).

---

## 3. Acceptance criteria

### MUST (what Apple needs to see a real, distinct app). Each one is testable.

**M1. Core job end to end (plan criterion 1).** On a fresh install: Home → "Review contacts" → permission primer → system prompt → scan → a list of match groups → open a group → **Merge** or **Not the same person** or **Open in Contacts** (`FlutterContacts.native.showViewer(id)`, `api/native_api.dart:39`). Every visible control does something real. The Contacts screen never ends in a dead card.
- Contacts permission changes from read to **readWrite** (`lib/data/device_sources.dart:38-39`). Android gets `WRITE_CONTACTS` (and the comment at `AndroidManifest.xml:4` is replaced). The iOS `NSContactsUsageDescription` (`Info.plist:32-33`) is rewritten to: "AGCleaner reads your contacts to find cards for the same person, and changes them only when you tap Merge. Originals are saved on this iPhone first so you can restore them."
- The test assertion of the old read-only sentence (`test/agcleaner_test.dart:83-84`) is **replaced** with an assertion of the new merge/restore copy. Say in the commit message that this is an intended behaviour change. It is not a deleted test.

**M2. Signature feature: cross-account match + merge with restore point (criterion 2).**
- `ContactRecord` carries `accounts` (name and type). Each card in a group shows a source badge (`iCloud`, the Gmail address, `Exchange`, `On this phone`, or `Unknown source` when the platform returns none, which must never be guessed). A group whose cards span 2 or more accounts is flagged "Across accounts".
- The merge preview shows the exact resulting card field by field, lets the user pick the name and photo from the originals, and states which account the merged card will live in (the account of the card kept).
- Order of operations: (1) export all originals to `ApplicationSupport/restore_points/<timestamp>.vcf` and write an index entry, and **abort the merge if this write fails**; (2) `update` the kept card; (3) `delete` the others; (4) record the result. If step 2 or 3 throws, the restore point stays and the UI says what was and was not changed.
- Restore: re-create each original from the vCard into its original account when that account still exists. If it does not, use the default account **and say so**. Then delete the merged card only if the user confirms.
- iOS honesty: notes cannot be read without Apple's contacts-notes entitlement (`contact_property.dart:82-83`). The merge preview on iOS must say: "Notes on the cards being removed can't be read by apps and will be lost." Do not fetch `ContactProperty.note` on iOS.

**M3. Depth (criterion 3).**
- **Persistence** (JSON in `getApplicationSupportDirectory()`, no new backend): (a) scan history (date, contacts read, groups found, merges done, photo bytes freed); (b) "Not the same person" decisions, keyed by the sorted set of contact ids, excluded from later scans and listed in Settings → "Kept apart" with undo; (c) the restore-point index.
- **Search and filter** on the contact groups: a text search over name/number/email, and filter chips **Across accounts / Same number / Same email / Same name**.
- **Share/export:** share any restore point as a `.vcf` through the system share sheet (`share_plus`, a keyless package), so the user can keep a backup off the phone.
- **States:** a first-run empty state (never scanned), a "no duplicates" state that shows the count actually scanned ("Checked 1,284 cards: no duplicates"), denied/limited-access states (iOS limited access says only the shared cards were checked), a scan error with retry, and a merge partial-failure state. There is no offline state because the app makes no network calls for its job. State that in the code comment, not on screen.

**M4. Own identity, not the shared scaffold (criterion 4).** Name these exactly in code:
- **Palette: "index card".** Light (default, follows the system setting): background paper `#F6F3EE`, surface `#FFFFFF`, ink text `#1E2328`, primary copper `#B4532A` (Merge, primary buttons), evidence green `#2F6F5E` (match badges, "restored"), hairline `#D9D3C7`. Dark: background `#16191C`, surface `#20252A`, text `#ECE7DF`, primary `#E0875E`, evidence `#6FB59E`. `ColorScheme` built from these explicit values, not `fromSeed(purple)`. I grepped all repos under `/Users/spatchava/agl` today and none uses these hexes.
- **Typography:** bundle **IBM Plex Sans** (`IBMPlexSans[wdth,wght].ttf`) for UI and **IBM Plex Mono** (Regular, Medium) for phone numbers, email addresses, byte figures and hash prefixes. OFL files from github.com/google/fonts `ofl/ibmplexsans` and `ofl/ibmplexmono` (I listed both directories with the GitHub API today). Ship `OFL.txt` and add a font licence entry via `LicenseRegistry`. No sibling app uses Plex. The fonts used across the portfolio today are Inter, Orbitron, Nunito, Satoshi, Roboto, Space Grotesk, JetBrains Mono and Poppins (grep across `/Users/spatchava/agl`).
- **Shape language:** cards with a 6 px radius and a 1 px hairline border instead of filled 12 px blobs. Contact cards are drawn like stacked index cards: the duplicates in a group overlap with a 4 px offset until opened.
- **Home layout:** no bottom NavigationBar and no three equal tabs. A large-title scroll view "AGCleaner" with a gear (Settings) and a clock (History) in the bar. Then two section cards. **Contacts**: last scan date, groups waiting, "Across accounts: n", and a primary "Review contacts" button. **Identical photos**: last result and a "Scan photos" button. Then a **Restore points** list (most recent 3, "See all"). On iOS use `CupertinoSliverNavigationBar`, `CupertinoIcons`, `showAdaptiveDialog` and `CupertinoActionSheet` for destructive confirmations. Android keeps Material 3 equivalents.
- **Code structure:** split `lib/main.dart` into `lib/app/` (theme, routes), `lib/features/home|contacts|photos|history|settings/`. **No `class C`.**
- **Onboarding:** one first-run screen specific to this job. Title: "Your contacts, one card per person". Three lines: what is read, what changes only when you tap Merge, and that originals are saved on the phone first. Then the user goes straight to Home. A just-in-time primer sheet appears before each system permission prompt. No "Get started" or "Welcome" copy.
- **Settings** (its own screen, its own copy): Kept apart · Restore points · Storage used by AGCleaner (the old Cache tab, moved here: measure and clear) · Language (`AglLanguageScreen` may stay as shared infrastructure, opened from this row and no longer from a header pill) · Privacy choices · Privacy policy · About (version, font licences).

**M5. Remove this app's template tells (criterion 4).**
- New app icon **not** from `scripts/generate_app_icons.py`: two offset index cards in copper `#B4532A` and ink `#1E2328` merging into one, on paper `#F6F3EE`, drawn as vector geometry (no Material glyph, no diagonal gradient). Regenerate every size in `ios/Runner/Assets.xcassets/AppIcon.appiconset` and every `android/app/src/main/res/mipmap-*` size (plus an adaptive icon foreground/background). Remove `AGCleaner` from the DESIGN table in `scripts/generate_app_icons.py:61` so a re-run cannot overwrite it (agl-manifest/scripts is not on the do-not-edit list).
- Own launch screen: `LaunchScreen.storyboard` background `#F6F3EE` with the card mark in the centre (dark variant `#16191C`). Its sha1 must differ from `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`.
- `CFBundleDisplayName` becomes `AGCleaner` (or the founder's new name, see founder questions), and so does `android:label`. pubspec `description:` describes the app.
- No Tailwind default hexes left in `lib/` (`A855F7, C084FC, 10B981, F59E0B, A1A1AA, 71717A, 3F3F46`), and no dark-only theme.
- The header language/privacy pills are gone (moved to Settings).

**M6. Honest, and nothing that could read as hidden (criterion 5, Apple 5.6).**
- Real data only. All of it comes from the device. No sample contacts, no sample photos, no "estimated" sizes. `test/no_demo_data_test.dart` keeps passing with its banned list intact.
- **No region-conditional UI:** the Settings → Privacy choices row is **always visible**. Where Google's form applies it opens it (`AglConsent.showPrivacyOptions`). Elsewhere it opens a short sheet: "Google's consent form doesn't apply in your region. Ads here are not personalised across other companies' apps." (Ads copy must match what agl_ads actually does. Check `packages/agl_ads` before finalising the wording.)
- **No remote switches:** AGCleaner reads no Remote Config key. Add a test that greps `lib/` for `AglInsights.flag(` / `AglInsights.setting(` / `FirebaseRemoteConfig` and fails on any hit. (Stopping Remote Config from starting at all needs an option in the shared `agl_observability`. See SHOULD S4.)
- No hidden gestures, no long-press-only actions, no debug menus, no demo login, no date/region/reviewer checks. Every feature is reachable from Home in at most 2 taps.
- In-app copy says what the app does in positive terms. Constraints are stated where they matter (e.g. "One copy is always kept", "Originals are saved first"), not as a list of disclaimers.

**M7. Proven (criterion 6).** `flutter analyze` clean. All tests pass. No test deleted or skipped (the single replaced assertion is in M1). New tests, at least:
- `test/contact_accounts_test.dart`: cross-account grouping. Cards in 2 accounts that share a number form one group flagged across-accounts. Source labels map `com.google`/`iCloud`/`com.apple.exchange`/empty to the right badge, and an empty account gives `Unknown source`.
- `test/merge_plan_test.dart`: the union of fields is de-duplicated with the normalisers in `contact_duplicates.dart`. The chosen name/photo is respected. The kept card's account is used.
- `test/restore_point_test.dart`: a vCard round trip of originals. **The merge aborts when the restore-point write fails** (fake store throws, then no update/delete is called). Restore re-creates into the original account and falls back to the default with a flag.
- `test/persistence_test.dart`: history, kept-apart and restore index survive a reload. Kept-apart groups are excluded from the next scan.
- Widget tests: Home shows the persisted last scan. Search and each filter chip narrow the list. The merge flow calls update then delete in that order on the fake source. The Privacy choices row is present in both consent states. First-run onboarding shows once.
- `test/identity_test.dart`: no `class C`, none of the listed Tailwind hexes, Plex fonts declared in pubspec and present on disk, a light and a dark theme both defined, LaunchScreen sha differs from the shared one, and `CFBundleDisplayName` equals the store name.
- Fakes extend `test/fakes.dart`. `ContactsSource` gains `update/delete/create/exportVCard/importVCard/openViewer`.
- Commit path-limited (`git add lib test pubspec.yaml pubspec.lock ios/Runner/Info.plist ios/Runner/Base.lproj ios/Runner/Assets.xcassets android/app/src/main assets scripts/...` only, never `fastlane/` or `ios/Podfile.lock`), then push to `main`.
- **Launch it and look at it.** Build for the iOS simulator and screenshot Home, a group, the merge preview and Restore points. Green tests are not proof the screens render.

**M8. Store impact written down (criterion 7).** See section 5. store-compliance applies it. The office does not submit (5.6 freeze, MA-043).

### SHOULD (valuable, not required for the resubmission)
- **S1. Identical videos:** run the same size-bucket + SHA-256 pipeline on `RequestType.video` and show results in a "Videos" segment. These free the most space. Videos stay preview-only, with no player beyond the system one.
- **S2. Contact health:** in the same scan, list cards with no number and no email, and numbers stored without a country code. Present them as information only.
- **S3. Photos history:** persist the last photo result (groups, bytes) so Home shows it without rescanning, and mark it stale when the library changes (`PhotoManager.addChangeCallback`).
- **S4. Infrastructure (needs the agl_observability owner):** add `AglInsights.init(remoteConfig: false)` and use it here, so no Remote Config SDK fetch runs in an app that reads no flags.
- **S5.** Translate all new strings into the 12 locales. Today only shared labels are translated (`store/apps/AGCleaner.json` notes §6 says so), and the new screens must not make that worse.

---

## 4. Data source
- Contacts: device address book via `flutter_contacts` 2.5.0 (`getAll` with `phone, email, name, address, organization, event, website, photoThumbnail`, and `accounts` from `metadata`). Writes only on Merge or Restore.
- Photos: device library via `photo_manager` (unchanged pipeline).
- Restore points, history, kept-apart: local files in the app's Application Support directory. They are never uploaded. They are deleted with the app, and the Settings → Restore points screen says so.
- No Supabase, no public API, no keys. Nothing new leaves the device. Firebase diagnostics and AdMob are unchanged and already disclosed.

## 5. Store impact (proposals only. I edited no file under `store/apps/`, `fastlane/` or `docs/`)

**Name / subtitle:** keep `AGCleaner` unless the founder renames it (see founder questions). Subtitle (30 chars max): **"Merge contacts across accounts"** (30).

**Promotional / short description (Play, 80 chars max):** "Find one person across iCloud, Gmail and work contacts. Merge, and undo anytime." (80)

**Description (proposed, replaces the current one):**
> Your phone has the same people in it two, three, four times: once from iCloud, once from Gmail, once from your work account, once from an old SIM. AGCleaner finds every set of cards that belong to one person, even when the names don't match, and fixes them with a merge you can undo.
>
> FINDS WHAT NAME-MATCHING MISSES
> Cards are matched on a shared phone number, a shared email address or the same name, and each match shows its evidence. A card saved as "Mom" in iCloud and "Jane Smith" in Gmail with the same number shows up as one person. Every card is labelled with the account it lives in.
>
> MERGE WITH A RESTORE POINT
> Before a merge changes anything, AGCleaner saves the original cards on your phone as a vCard file. Restore points keep every merge, so one tap puts the originals back. You can also share a restore point to keep a copy wherever you like.
>
> YOU DECIDE
> Review groups one at a time, search them, filter to cross-account matches, or mark a pair "Not the same person" so it never comes back.
>
> IDENTICAL PHOTOS
> A second scan lists photos that are byte-for-byte identical, confirmed by a SHA-256 fingerprint, keeps one copy of each, and deletes the rest only after your device confirms.
>
> PRIVATE BY DESIGN
> Contacts and photos are processed on your phone and never uploaded. No account, no sign-in. Anonymous crash and performance diagnostics go to Google Firebase. AGCleaner is free and shows Google AdMob ads; where the law requires consent, Google asks first, and Settings → Privacy choices is always there.

(Do not open with the app name. It must not share the portfolio's "ADS" heading or its shared ad paragraph word for word. store-compliance must check the ads sentence against what agl_ads actually does before using it.)

**Keywords (100 chars max):** `merge contacts,duplicate contacts,contact cleanup,gmail icloud contacts,vcard backup,same photos` (96)

**Screenshots (retake all 5 from the release build of the new app, iPhone 6.9" + iPad 13" + Play phone/tablet):**
1. Home: Contacts card "Across accounts: n" + Restore points list.
2. A group with source badges (iCloud / Gmail / On this phone) and "Matched on phone number".
3. Merge preview with field-by-field result and the "Originals saved first" line.
4. Restore points with a Restore button and share sheet.
5. Identical photos group with the keep-one indicator.
Remove: the Language picker screenshot and the near-duplicate pairs (current 1/5 and 2/3). Use a QA device address book made of the tester's own real test entries. Never fabricate names in a screenshot meant to imply real users. Founder question 4 covers whether showing ads in screenshots is required.

**Play feature graphic:** rebuild from the new icon and palette. The current one shows the Flutter logo.

**Review notes (proposed, bespoke. Do not use the shared "2. DEVICES…" skeleton):**
> AGCleaner merges duplicate contacts, including cards for the same person stored in different accounts (iCloud, Gmail, Exchange), and keeps a restore point for every merge.
> To try it: open the app → Review contacts → allow Contacts. Any two cards that share a phone number appear as a group. Open the group → Merge → confirm. Then Home → Restore points → Restore puts the originals back. Identical photos: Home → Scan photos → allow Photos.
> No account or login. Every feature is on the home screen. Nothing is region-, date- or server-controlled. The only regional difference is Google's ads consent form (EEA/UK/CH), reachable at any time from Settings → Privacy choices.
> Tested on: [QA must fill in the actual physical iPhone/iPad models and iOS versions used. Do not list simulators as devices and do not claim a device that was not used.]
> Contact for review: [a real named person. Founder decision, see founder questions.]

**Privacy (App Store label):** the data collected does not change (contacts and photos never leave the device). store-compliance should still answer the label for this app on its own rather than reuse the 20-app identical label. Any privacy-policy wording change is a founder decision (Charter §6).

**Permissions declared in the listing:** Contacts is now read **and write**. Play's data safety form and the iOS usage string (M1) must match.

## 6. Out of scope
- Photo editing, galleries, albums, similar/"98% alike" photo scoring (Photriya owns photos. Similarity scoring cannot be stated honestly).
- Device storage/RAM "boost" gauges, other apps' caches, any system-wide cleaning (not permitted on iOS/Android, and it was the old demo).
- Any backend, account, sign-in, cloud backup of contacts, paid tier.
- Calendar, SMS, call-log or WhatsApp dedup.
- Editing `store/apps/AGCleaner.json`, fastlane metadata or docs. Uploading, submitting or replying to Apple.

## 7. Founder questions
1. **Name:** keep "AGCleaner" (house prefix, generic "cleaner" category) or rename to something that says the job (e.g. "Samecard" or "Mergeback"; availability on the App Store **not verified**)? A rename changes the bundle display name, icon wordmark and listing.
2. **Contacts write access:** this spec turns a read-only finder into an app that merges and deletes contacts (with restore points). It reverses the "never edits a contact" promise in the current listing. Approve the scope change?
3. **Interstitial ads:** removing the between-tab interstitial (`lib/main.dart:430-436`) simplifies the app, and the new layout has no tabs to trigger it. It also changes ad revenue, which is a money decision (Charter §3). Remove it, or move it to after a completed merge or scan?
4. **Screenshots and ads:** store screenshots come from SCREENSHOT builds with no ads. Is that acceptable, or should the listing show the banner placement?
5. **5.6 is account-wide** (16 identical messages within one minute). Who replies to Apple, and when (Charter §1, MA-043 freeze)? An app-level fix alone may not lift it.
6. **App Review contact:** replace "App Reviewer" with a real person's name for this app?

---

## 8. Implementation notes (software-developer, 2026-10-12)

Appended by the software-developer; sections 1-7 above are unchanged. Repo state and commit hash are in the run report.

**For store-compliance (nothing here was applied to store/, fastlane/ or docs/):**
- Permissions in the binary now: iOS `NSContactsUsageDescription` = the M1 sentence verbatim; Android adds `WRITE_CONTACTS`. Play data safety and the listing must say contacts are read **and written** (written only on Merge and Restore).
- **The live privacy policy contradicts the new binary.** `https://www.americangroup.ai/policy/agcleaner/` (fetched with curl today, HTTP 200) still quotes the old usage string "It never edits, deletes or uploads a contact." and lists Android permissions without `WRITE_CONTACTS`. Updating it is legal text (Charter §6, founder decision) and must happen before any resubmission.
- Settings › Privacy choices sheet text (shown where Google's form does not apply): "Google's consent form for ads isn't required where you are, so there's nothing to change here." / "AGCleaner is free and shows Google AdMob ads. Where the law requires consent, Google asks first and this row opens its form." Checked against agl_ads: every request uses `const AdRequest()` and is gated by `AglConsent.canRequestAds()`; the copy makes no personalisation claim.
- Interstitial (founder question 3, still open): the tab-switch trigger is gone with the tabs. The same capped `AglAds.onTransition()` now fires after the user returns to Home from a pushed page (never on dialogs, never mid-merge). Removing it entirely remains a founder money decision.
- `integration_test/store_screenshots_test.dart` now captures first run, Home, Settings, Storage and History (no permission prompts). The five store screenshots in section 5 (group with badges, merge preview, Restore points) need a QA device with the tester's own test cards; they cannot be driven past the system permission alert.
- Feature graphic: the icon and launch mark are vector geometry in `AGCleaner/scripts/generate_card_mark_icons.py` (palette constants at the top); reuse it rather than the old glyph icon.

**Not done in this pass:** `scripts/generate_app_icons.py` in agl-manifest still lists AGCleaner (line 61) because that file has another workstream's uncommitted edit (the AGRecorder entry); a re-run of that script for AGCleaner would overwrite the new icon until the line is removed. S1 (videos), S2 (contact health), S3 stale-marking and S4 (`AglInsights.init(remoteConfig: false)`) are not done; S3's "persist last photo result" is done; S5 (all new strings in the 12 locales) is done.
- iOS account badges: flutter_contacts 2.5.0 returns no accounts on iOS (`ContactConverter.swift` builds `accounts: []`). The app now lists each container's cards (`getAll(account:)`) to fill them in (AGCleaner commit 6453793). Verified on a simulator (local container shows "On this phone"); a real device with iCloud + Gmail + Exchange containers is **not verified** and is the first thing QA should check before store screenshots.

**Repair round (software-developer, 2026-10-13), after QA:**
- Fixed: double restore duplicated contacts. AGCleaner commit `18abcbe` (pushed to origin/main). Restore points now record which originals were re-created (`restoredIds`). A fully restored point refuses another restore (`RestorePointAlreadyRestored`) and its Restore button is disabled. A card whose create failed can be retried without duplicating the others. Tests are in `test/restore_point_test.dart` and `test/contacts_flow_test.dart`. Removing the guard makes four of them fail.
- Still open (M5): `agl-manifest/scripts/generate_app_icons.py:61` still lists AGCleaner. The AGRecorder edit QA saw is now committed, but the file has another workstream's uncommitted edit again (the WiFiTrail entry, `git status` shows ` M`). Under the do-not-touch rule I did not edit it. The owner of that edit, or whoever commits it, should also replace line 61 with: `# AGCleaner is not listed: its card-merge icon is drawn by AGCleaner/scripts/generate_card_mark_icons.py, and a run of this script must not replace it.`
- Founder decision, blocks resubmission (Charter §6): re-fetched today. `https://www.americangroup.ai/policy/agcleaner/` (HTTP 200) still says "never edits, deletes or uploads a contact." and does not mention `WRITE_CONTACTS`.
- Not verified, needs a real device: source badges for real iCloud, Gmail and Exchange containers on iOS, and what deleting an iOS unified (linked) contact does to the linked cards in other containers.

**Repair round 2 (software-developer, 2026-10-14), after QA:**
- M5 done: the WiFiTrail edit is now committed (`9f7854c`). The working tree was clean, so I replaced the AGCleaner row in `scripts/generate_app_icons.py:61` with the comment above. agl-manifest commit `3c1595a` is pushed. `DESIGN` no longer has an AGCleaner key, so a plain run cannot redraw its icon.
- M4 font collision: not changed in the app. Four apps bundle IBM Plex Sans + Mono: AGCleaner `fd4091c` (10-12 17:29), AGRecorder `7cf8722` (17:33), ApexMarketWatch `74801e7` (17:39) and yourtube `f761bbf` (10-13). Picking the keeper is a chief-of-staff/portfolio-director decision, raised in agl-manifest issue #39. If AGCleaner loses Plex, update the typography line in M4 and `test/identity_test.dart`.
- Policy text: the approval request is `reports/approvals/2026-10-14-agcleaner-privacy-policy.md`, issue #38 (needs-founder). The live page still says "never edits, deletes or uploads a contact." (curl, HTTP 200, byte-identical to the website source). It also says there are no ads and no diagnostics, both of which are wrong.
- Still not verified (needs a real device): iCloud/Gmail/Exchange source badges on iOS, and what deleting an iOS unified contact does to the linked cards.
