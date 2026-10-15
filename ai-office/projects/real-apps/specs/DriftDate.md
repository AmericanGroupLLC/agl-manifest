# Spec: DriftDate, dating that starts in your ZIP area, never shows miles, and keeps you safe on the day

- **Author:** product-manager (AI office), 2026-10-12
- **Repo:** /Users/spatchava/agl/DriftDate, branch `main`, base `995bc6903e14d799442ab2bc188c5dcb2aceb4d1`
- **Plan:** projects/real-apps/plan.md (acceptance criteria 1–7)
- **Store state:**
  - Apple: rejected under 4.3 / 4.2.6. This is the shared message, the same text sent to 26 apps. Review then raised 2.1(a), a crash on launch on an iPhone 17 Pro Max running iOS 27.0, and 2.3.3, "The screenshots only display a login screen" (`.dist/rejections.json` key `DriftDate`).
  - Google Play: PRODUCTION_DRAFT_STAGED.
- **Overlap ruling followed:** overlap.md line 58. DriftDate owns location-layered dating with the trust passport and the safety centre. It must not do event discovery or hosting, which belong to EventSpark.
- **Dirty at base:** these files have other people's uncommitted work: `fastlane/metadata/**` (7 files), `ios/Runner.xcodeproj/project.pbxproj` (`git status --short`). The developer must not touch them.

---

## 1. Problem

### The blocker under everything: today nobody can use DriftDate

1. **The backend is not in production.** Sign-in works, but the profile read fails with `PGRST205 Could not find the table 'public.profiles'`. That error is quoted in `reports/approvals/2026-10-12-driftdate-schema.md`; I did not run it myself.
   - The fix is Backend PR #1, branch `driftdate-schema`, commit 3749de6. It adds 2 migrations, 776 lines, creating the `driftdate.*` schema.
   - It waits on founder approval (issue #19, Charter §2). The app already reads that schema (`supabase_drift_backend.dart:57` `_client.schema(schema)`, commit 355d9b5).
   - I tried a read-only REST probe of production to confirm the table state. The office judge refused it as a credentials and production-data action. **Production schema state: not verified by me.**
2. **Even with the schema deployed, no two people could ever message each other.**
   - `driftdate.can_send_message` requires `a.verified_at is not null and b.verified_at is not null` (PR branch `20261012_driftdate_1_schema.sql:372-389`).
   - Only the `verify-selfie` edge function sets `verified_at`, and it was never deployed. The 2026-10-09 backend note says DriftDate's edge functions return 404 (`AmericanGroupLLC-Backend/supabase/migrations/20261009_delete_user.sql:8`).
   - So every chat ends at the notice `chat_locked_verification`: "Identity verification is not available in this version of DriftDate yet, so messages cannot be sent in this chat" (`l10n/app_strings_extra.dart:25-26`, shown at `chat_screen.dart:281` and `date_planner_screen.dart:90`).
   - The current review notes (§8) tell Apple this is intended. **For Apple, that is a dating app whose core job cannot complete.**
3. **Signing up depends on SMS.**
   - "Get started" leads to onboarding, whose step 1 is phone OTP (`onboarding_screen.dart:316`, which calls `auth.signInWithOtp(phone:)` at `supabase_drift_backend.dart:104-105`).
   - Whether an SMS provider is configured on Supabase project `smvvjivvlprjhzhoizym` is **not verified**. I found no record of one in agl-manifest (grep for twilio, sms provider and phone auth: no hits).
   - There is no email sign-up path anywhere (grep for `signUp` in `lib/`: no hits). Only Apple and Google create accounts from the login screen.

### What the app is today (read from `lib/`, 18,397 lines in 70+ files)

| Screen / module | What works | What is shallow, dead or dishonest |
|---|---|---|
| Splash `splash_screen.dart` | Animated mark. "Get started" and "Log in" | Generic copy: "Find Real People / Not Just Profiles" (`app_strings.dart:238-239`) and "Get started" (`:188`). Both store screenshots are this screen (`fastlane/screenshots/en-US/iphone69-01.png`, which I viewed, plus `-02`). |
| Login `login_screen.dart` | Email+password sign-in, Sign in with Apple, Google | The portfolio sign-in family: "Welcome back" (`:193`), "Continue with Google" (`:244`). There is no way to *create* an email account. |
| Onboarding `onboarding_screen.dart` (679 lines) | 3 steps: phone OTP, then photos with an on-device photo-quality review, then name, date of birth (18+ gate), gender, intent and layers | Step 1 needs SMS (see above). |
| Discover `discover_screen.dart` (696 lines) | Swipe deck by layer, wave and pass, a pool count per layer, "Use my location" (coarse ZIP-3 and state), report and block on the card | **County never works.** `LocationService` always passes `countyFips: null` (`location_service.dart:75-77`), so the picker hides County (`discover_screen.dart:245-255`) and shows "County matching isn't available yet". The fourth layer is labelled "Server" (`app_strings.dart:233`), which is developer jargon. The home is the generic card deck. |
| Matches / Chats `matches_screen.dart`, `chat_list_screen.dart`, `chat_screen.dart` (648 lines) | Lists, realtime message stream, tone-aware reply openers built on-device by `ReplySuggestionGenerator`, mute, screenshot disclosure | **Sending is impossible** (blocker 2). Every chat open first calls the undeployed `reply-suggest` edge function (`supabase_drift_backend.dart:684-708`), reports the failure, then falls back. |
| Match `match_screen.dart` | "It's a Match!" (`app_strings.dart:247`), then the compatibility view | Stock copy. |
| Compatibility `ai_compatibility_screen.dart` + `core/domain/compatibility.dart` | Deterministic, computed from profile tags | **Inflated numbers.** Each facet is `curve(x) = 0.55 + x*0.45` (`compatibility.dart:81`), so any two strangers score at least 55%. Six dials named "Personality" and "Chemistry" are derived from interest-tag overlap and from how much each person filled in. The file name says "ai" although no AI is involved (overlap.md:85-87). |
| Date planner `date_planner_screen.dart` | Activity ideas from shared interests (`core/domain/date_ideas.dart`) | Real, but its only action ("send to chat") is blocked by blocker 2. |
| Trust Passport `trust_passport_screen.dart` (416 lines) + Trust Score `trust_score_screen.dart` (398 lines) | Email and phone confirmation through Supabase Auth | **Two screens for one thing**, a 5-star ladder of which only star 1 is reachable, and "Not available yet" on 4 of the 6 rows: Identity (ID+selfie), Identity+ (SSN), Background, Financial (`trust_score.dart:28-36`, `app_strings_extra.dart:120-122`). A weighted "Overall trust" out of 5 (`trust_score.dart:125-132, 172-182`) cannot exceed 0.9 (phone 0.10 + email 0.08 = 0.18 × 5). |
| Safety Centre `safety_center_screen.dart` (213 lines) | Block or report each match, a link to the block list, 4 static tips | Thin. Nothing helps on the day of a date, which is when users need safety most. |
| Profile / Settings | Photos (upload to storage), prompts, vibes, coarse location, reduce motion, language, Privacy choices (UMP), sign out, delete account (`rpc('delete_user')`, which needs MA-044) | A debug-only "DriftDate+" switch (`settings_screen.dart:85-113`) and the string "Premium (demo)" in 12 locales (`app_strings.dart:220` and others). |
| Dead code and permissions | n/a | `widgets/voice_prompt_recorder.dart` is not referenced anywhere (grep), yet `record`, `audioplayers` and `NSMicrophoneUsageDescription` are present. `NSCameraUsageDescription` says "to take a verification selfie" (`ios/Runner/Info.plist:34-35`), and no selfie feature exists. |

### Why Apple called it a template (this app's measured tells)
- The Supabase sign-in family: `login_screen.dart`, plus `auth_service.dart` at 0.43 Jaccard with Uscis-Case.
- `lib/app_env.dart` is byte-identical to 4 other apps, including the "test credentials are present in a production release" guard.
- `error_reporter.dart` is a 13-app duplicate.
- The shell: `AglAdBanner` directly above a Material `NavigationBar` (`main_tabs.dart:51-52`). Material on iOS, no Cupertino. No typeface of its own (`drift_theme.dart` `DriftType` sets no `fontFamily`).
- "Get started" / "Welcome back".
- Store packaging:
  - the shared `qa@americangroup.ai` demo login
  - '——' description headings
  - review notes on the "2. DEVICES…" skeleton with the simulator boilerplate, and "Intended audience: Dating that widens slowly", which is the subtitle pasted in
  - the 13-app privacy label, which is also **wrong for this app**: it omits photos, coarse location, messages and phone number (`store/privacy/DriftDate.json`)
- The 23-app identical Resolution Center reply.
- Fewer tells than most: own splash storyboard (shasum `5a0a93b5…`, not the shared `3f6a9b27…`) and own gold double-heart icon. I viewed both. The asset `assets/logo/driftdate_icon_1024.png` is a *different* blue heart-and-orbit, so the brand is inconsistent.

Apple also names this category outright. Guideline 4.3(b), which I fetched live today with `curl https://developer.apple.com/app-store/review/guidelines/`, says: *"Certain kinds of apps, such as dating, flashlight, sound effects, wallpaper, simple timers, and fortune telling, are well established on the App Store and we will not accept new submissions unless they offer a meaningfully different or improved experience."* DriftDate therefore needs a difference Apple can see in the first minute, and that difference has to work with zero other members nearby.

## 2. User

**An adult in the U.S. who wants to date locally and safely: someone who would rather see the few real people in their own ZIP area than a nationwide feed, and who will not share an exact position with strangers.** It skews towards people who have had a bad or unsafe date before and want the app to help on the day itself, not only in the chat.

The app's own constraints set the scope: an 18+ gate (`core/domain/age_gate.dart`) and U.S. ZIP and state layers (`location_service.dart` `_stateCodes`), so the market is the United States.

Not for: casual "hookup" positioning (guideline 1.1.4), event-goers (EventSpark), or anyone outside the U.S. until the layers support other postal systems.

## 3. Product

### Core job
**Meet a real person near you, one ring at a time, and get to a first message.** Set your area (ZIP-3, county, state; never coordinates). See who is in your ring, wave, and match when you both wave. Then chat, without a verification wall nobody can pass.

### Signature feature: Safe Meet, a date plan with a timed check-in, tied to the other person's real trust facts
Before a first date you make a plan: who (a match, or a typed first name for someone met elsewhere), where (a free-text place), when you start, and when you expect to be done. The plan shows the other person's **real** trust facts: email confirmed, phone confirmed, signed in with Apple or Google, member since, and which DriftDate ring you matched in.

One tap opens Messages, or the share sheet, with the plan pre-filled for a trusted contact you chose. DriftDate does not send texts itself, and the copy says so.

At the end time the app fires a **local notification**: "Are you home safe?"
- **"I'm safe"** closes the plan.
- **"Need help"** opens a full-screen sheet with:
  - one-tap *Call 911* (`tel:911`)
  - *Text my contact*, which opens Messages pre-filled with the plan and "I haven't checked in"
  - *Share my plan again*
- If the user ignores the notification, a second notification fires 15 minutes later. After that, the Safe Meet tab shows the plan as **"Not checked in"** until the user resolves it.

Everything stays on the device: the plan, the trusted contact and the check-in.

Why this, and not something bigger: it is buildable now by one developer with no keys and no new server data. It uses `flutter_local_notifications`, `url_launcher` and `share_plus` (free pub.dev packages) plus local storage.

It also works **on a fresh account with no matches**, because a plan can be made for a typed name. App Review can therefore exercise the signature feature even when nobody else is in their ring.

### Supporting distinctions (already half-built, finished by this spec)
- **Rings, never miles.** Location is reduced to ZIP-3, county and state on the device. Raw latitude and longitude are discarded (`location_service.dart:41-88`). No distance number is ever shown, only "Same ZIP area", "Same county", "Same state" or "Elsewhere".
- **Facts, not scores.** The Passport lists only checks the app can actually perform. Compatibility becomes a list of real shared facts instead of percentages.

### Competitors
Web search is disabled in this session: the WebSearch tool returned "Internet mode is not enabled". I checked existence, age rating, rating and description with Apple's keyless iTunes Lookup API today (`curl itunes.apple.com/lookup?id=…&country=us`). I have not installed or used any of these apps, so each gap below rests on the store description only.

| App (iTunes id) | Rating, age, genre | What its description says about safety and location | Gap DriftDate fills |
|---|---|---|---|
| Tinder (547702041) | 4.20, 17+, Lifestyle | "Match with people nearby or around the world"; "multiple ways to verify profiles, added safety tools" | The description mentions no date plan and no timed check-in. |
| Hinge (595287172) | 4.41, 17+, Lifestyle | "Selfie Verification" | The description mentions no date plan, no check-in and no location privacy. |
| Bumble (930441707) | 4.32, 17+, Lifestyle | "Get ID Verified"; "Share Date to drop location details with the group chat" | Bumble shares date details. Its description mentions **no timed check-in after the date** and nothing about coarse-only location. |

**Honest angle:** the big three describe verification and, in Bumble's case, sharing a date. None of the three descriptions describes a check-in that asks you, at the time you set, whether you got home. None describes storing only a coarse area instead of a position.

DriftDate combines (1) rings instead of a distance radius, (2) a Safe Meet check-in tied to the match's real trust facts, and (3) a Passport that never claims a check it cannot perform. Whether any of these apps has an in-app check-in that is absent from its description is **competitor not verified**.

---

## 4. Acceptance criteria

### MUST (what Apple has to see for a real, distinct app)

**M1. A new adult can get in without SMS and without a demo account.**
- "Get started" offers Sign in with Apple, Continue with Google, and **Create an account with email**.
  - The email option is new: `auth.signUp`, then Supabase's confirmation email, then a "Check your inbox" state with *Resend* and *I've confirmed*. The latter calls `reloadUser`.
  - The existing "Log in" stays for returning email users.
- The profile builder keeps its real parts: photos with the on-device quality review, name, date of birth with the 18+ gate (`AppState.finishOnboarding` keeps the belt-and-braces check), gender, intent, and which rings you are visible in.
- **The phone OTP step leaves onboarding.** Phone confirmation moves to the Passport (M5), shown only if founder question F3 enables SMS. That is a build-time decision, not a remote switch.
- Test: a widget test drives a fresh install through Get started → email sign-up (fake `AuthService`) → profile builder → Nearby, and no step asks for a phone number.

**M2. Two matched members can actually message each other.**
- **Backend.** Amend PR #1 *before* it is approved: `driftdate.can_send_message` requires both profiles to have a **confirmed email or confirmed phone** (from `auth.users.email_confirmed_at` / `phone_confirmed_at`, read inside the security-definer function) and no block. `verified_at` is dropped from the condition.
  - Update the PR's RLS evidence (PGlite run) to cover: unconfirmed sender refused, confirmed pair allowed, blocked pair refused.
  - Deploying it remains the founder's decision (#19, Charter §2). The office does not run production SQL.
- **App.**
  - Delete `chat_locked_verification` in all 12 locales.
  - When the *viewer* is unconfirmed, the composer shows "Confirm your email to send messages", with a button that opens the Passport row.
  - When the *other person* is unconfirmed, it shows "{name} hasn't confirmed their email yet. Your message will send once they do", and the draft is kept.
  - The date planner's "send to chat" works for a confirmed pair.
- Remove the `functions.invoke('reply-suggest')` call. The on-device `ReplySuggestionGenerator` becomes the only path, so a chat open no longer reports an error.
- Test: an in-memory backend test asserts that a confirmed pair can send, an unconfirmed sender gets the confirm prompt rather than the locked text, and a draft survives the refusal.

**M3. Four real rings that widen one step at a time, with no distance shown.**
- **County works.** At build time a script under `tool/` downloads the Census 2020 ZCTA-to-county relationship file and writes a compact ZIP5→county-FIPS map as a bundled asset (largest land-area part wins). The file is `https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt`; I fetched it today and it answered HTTP 200, keyless, with header `OID_ZCTA5_20|GEOID_ZCTA5_20|…|GEOID_COUNTY_20|NAMELSAD_COUNTY_20|…`.
  - `LocationService.currentFuzzed` looks up the county **on the device** from the full ZIP5 *before* truncating it. The ZIP5 is never stored or sent.
  - Delete the "County matching isn't available yet" strings and the picker workaround (`discover_screen.dart:245-255`).
- **Home is the Ring view** (see M8): ZIP area, then county, then state, then everywhere. Each ring is labelled with its real count of people you have not yet waved at or passed, from `poolCounts`.
  - The current ring is highlighted. One button, "Widen to {next ring} (+N people)", moves out exactly one ring, and "Come back in" narrows.
  - The chosen ring is persisted per user.
  - The layer formerly named "Server" is renamed **"Everywhere"**.
- **No distance anywhere.** The proximity label is one of "Same ZIP area", "Same county", "Same state" or "Elsewhere". A test greps `lib/` and the rendered Nearby screen for `miles`, `mi away` and `km`, and finds none.
- Tests:
  - the ZIP→county lookup: a known ZIP maps to its county, an unknown ZIP gives null, and the ZIP5 is not present in the `FuzzedLocation` JSON
  - widen and narrow move exactly one ring
  - the ring counts come from the backend, never from a constant

**M4. Signature: Safe Meet (new tab, `lib/safe_meet/`).**
- **Plan editor:**
  - fields: with whom (pick a match, or type a first name), where (free text), start time, expected end time (default start + 2h), and an optional note
  - when the person is a match, a read-only card with their real trust facts (M5) and "Matched in {ring}"
  - validation: end time after start, start no more than 30 days ahead
- **Trusted contact:** a name and phone number the user types in, or picks with the system contact picker if that is simple. Stored **on the device only** (`flutter_secure_storage` or `shared_preferences`). It is never uploaded.
- **Share:**
  - "Text {contact}" opens `sms:` with the plan text pre-filled.
  - "Share…" opens the system share sheet (`share_plus`).
  - The plan text holds only what the user typed, plus the match's first name and "met on DriftDate". It never contains a photo or a location beyond the typed place.
- **Check-in:** `flutter_local_notifications` schedules "Are you home safe?" at the end time and a second reminder 15 minutes later, with *I'm safe* and *Need help* actions.
  - *Need help* opens a full-screen sheet: Call 911 (`tel:911`), Text my contact (pre-filled "I haven't checked in. Here's my plan: …"), and Share plan.
  - Notification permission is requested **when the first plan is saved**, with an explanation, not at launch. If it is denied, the plan screen says plainly that DriftDate can't remind you, and an in-app banner on Nearby carries the check-in instead.
- **State and history:** Upcoming → Active → Checked in / Not checked in. The plans persist across restarts, and the list filters by Upcoming, Active and Past. Editing or cancelling a plan reschedules or cancels its notifications.
- An "Active plan" strip appears at the top of every tab while a plan is running, with *I'm safe* on it.
- **No interstitial ad** is shown on any Safe Meet screen, on the Need-help sheet, or within 5 minutes of a check-in.
- Tests:
  - the pure state machine: transitions, the reminder schedule, a cancelled plan
  - notification scheduling through a fake notifier
  - a widget test: save plan → kill and restart → plan still Active → I'm safe → Past
  - the plan text contains no coordinates
  - Need help shows the three actions

**M5. One honest Trust Passport, visible to others.**
- Merge `trust_passport_screen.dart` and `trust_score_screen.dart` into one Passport.
- **Rows are only checks the app performs:**
  - Email confirmed
  - Phone confirmed (only if F3 enables SMS; otherwise the row is absent, not "not available")
  - Signed in with Apple / Google (from the auth identities)
  - Member since {month year}
  - Profile complete: at least 1 photo, at least 2 prompts, area set
- **Delete:**
  - `TrustCheck.identity`, `identityPlus`, `background` and `financial`
  - the 5-star `TrustLevel` ladder
  - the weighted "Overall trust" number
  - "Build trust. Get more matches." (`app_strings.dart:254`)
  - `trust_status_unavailable` / `trust_unavailable_note`
  - their tests, deleted in the same commit, with the commit message listing each test removed and why. No test is deleted for any other reason.
- **Others see your facts:** add to PR #1 a security-definer `driftdate.trust_facts(profile_id)` that returns only booleans plus the created-month. The query must be refused when either side has blocked the other. The facts render as small chips on the Nearby card, in Matches, and in Safe Meet.
- **Remove unused permissions and dead code:**
  - `NSCameraUsageDescription` (the "verification selfie" string), but only if no `ImageSource.camera` path remains. Grep, then decide. If camera photo-taking is kept, reword the string to "to take a profile photo".
  - `NSMicrophoneUsageDescription`
  - `widgets/voice_prompt_recorder.dart`
  - the `record` and `audioplayers` dependencies, after grep shows no other use
  - `Info.plist` has no uncommitted changes at base (`git status --short ios/Runner/Info.plist` is empty), so it may be edited.

**M6. Honesty and 5.6 cleanup.**
- **Compatibility becomes "Shared ground".**
  - Rename `ai_compatibility_screen.dart` to `shared_ground_screen.dart` and remove every dial and percentage.
  - Show a list of true statements: "You both like {vibe}" (one per shared vibe), "You're both looking for {intent}", "You're both in {ring}", "{name} answered '{prompt}'".
  - If nothing is shared: "Nothing in common on your profiles yet. Their prompts might give you an opener."
  - Delete the 0.55 floor (`compatibility.dart:81`).
  - "It's a Match!" becomes "You both waved", with the Shared-ground list underneath.
- **Remove:**
  - the debug "DriftDate+" switch and the `settings_premium` key in all locales
  - `adsRemoved` if nothing else sets it
- **Rules:**
  - No demo login, no remote switches (the AglInsights Remote Config must not gate any DriftDate feature; the developer greps to prove it), no reviewer, region or date detection, no hidden gestures.
  - The Safe Meet check-in fires only at a time the user set.
- **Nothing invented:** no sample profiles, no "people nearby" estimate, no counts that are not query results. The existing `test/no_invented_data_test.dart` must keep passing.

**M7. User-generated content safeguards (guideline 1.2, which I fetched live today).**
- **On-device filter.** Display name, prompts, vibes and messages pass a word-list check (`lib/core/domain/content_filter.dart`, with a bundled list under `assets/`) before they are submitted.
  - A blocked submission keeps the text and explains what to change.
  - The filter is also applied when rendering another member's text, as a defence against older rows.
- **Report and block** already exist on the card, the match and the chat (`widgets/safety_actions.dart`). Keep them. Add "Report a message" (long-press on a message → Report), which stores the message id in `reports`. PR #1 may need a `message_id` column.
- **Published contact:** the Safety Centre and Settings show "Contact DriftDate safety: contact@americangroup.ai", a `mailto:` link, plus the support URL from the listing.
- Tests: the filter blocks the list and allows normal text; a submission refused by the filter keeps the draft.

**M8. Own identity: not black-and-gold Material, and not the portfolio shell.**
- **Concept: "tide rings".** Concentric contour rings spreading out from a point, which is the widening. The rings are the visual motif everywhere: the home, the icon, the splash and the empty states.
- **Colour** (light by default, with a dark variant):

  | Role | Colour |
  |---|---|
  | Background "mist" | `#F3F5F2` |
  | Ink | `#1B2A2F` |
  | Primary "lagoon" (`ColorScheme.fromSeed` seed) | `#134E5E` |
  | Accent "apricot" (CTAs, active ring) | `#F2A65A` |
  | Ring: ZIP | `#F2A65A` |
  | Ring: county | `#E07A5F` |
  | Ring: state | `#3D8C95` |
  | Ring: everywhere | `#6C7A89` |

  - The dark variant uses ink `#1B2A2F` as the background, never pure black and never neon.
  - I grepped each of these 7 hexes over the 42 `lib/` and `mobile/lib/` trees under `~/agl` and over the other specs in `specs/`, and found no match (the AeroSwift, AGCleaner, AGrammarly, AGRecorder, AGStudio, ApexMarketWatch, BodyQuest and BuddyPlay specs existed at the time). The 43rd app keeps its code outside those paths and was not searched.
  - None of the 7 is a Tailwind default from the diagnosis list.
  - The current gold palette (`theme/drift_colors.dart`, `onyx #050506`, `gold #E8C78A`) goes.
- **Typography:** **Instrument Serif** (OFL) for headings and names, and **Figtree** (OFL) for body and UI.
  - Bundle both as font assets in `pubspec.yaml`. Do not fetch them at runtime.
  - My grep for "instrument serif", "figtree" and "bricolage" over the same 42 trees, every `pubspec.yaml` and the specs folder found no match. Fraunces was already taken by 3 specs, so it was avoided.
- **Shape language:** ring arcs and 1.5 px contour strokes, pill buttons, and card radius 20 (not the portfolio's 12). Photos are cropped as rounded squares with a ring-coloured edge showing which ring the person is in.
- **Shell:** four destinations: **Nearby** (the Ring view, then the deck for the current ring), **Matches** (matches with their chats inside), **Safe Meet** and **You** (profile, Passport, settings).
  - On iOS use `CupertinoTabBar`, CupertinoIcons or custom ring glyphs, and Cupertino page transitions. On Android use a Material `NavigationBar`.
  - The `AglAdBanner` no longer sits in the shell above the tab bar. If F7 keeps ads, a single banner is allowed only as a row at the end of the Matches list, never on Nearby cards, chat, Safe Meet, the Passport or the profile.
  - `AglAds.onTransition()` must not fire when switching to or from Safe Meet.
- **Onboarding and copy** written for DriftDate:
  - The splash shows the rings animating outwards: "Start with your ZIP area. Widen when you're ready."
  - Buttons read "Create my profile" and "I already have an account".
  - Remove "Get started", "Welcome back", "Find Real People / Not Just Profiles", "Find real connections" and "It's a Match!".
  - Settings copy names DriftDate concepts: "Rings you're visible in", "Trusted contact", "Check-in reminders".
- **Icon:** three apricot-to-lagoon contour rings around a single dot on mist, with no heart and no white glyph on a gradient.
  - Produce a 1024 px PNG without alpha, regenerate `AppIcon.appiconset` and the Android adaptive icon, and replace `assets/logo/*` so the brand matches everywhere.
- **Splash:** mist background with the ring mark. Edit only `ios/Runner/Base.lproj/LaunchScreen.storyboard` and the `LaunchImage.imageset` / `LaunchBackground.colorset` assets. **Do not touch `project.pbxproj`.**
- **Proof:** Settings uses DriftDate's own language sheet (it already does, not the shared `AglLanguageScreen`), and `grep -rn "Cupertino" lib/` is non-empty.

**M9. Depth: persistence, search, share, and real empty, error and offline states.**
- **Persisted:** the chosen ring, passes (already on the device), Safe Meet plans and history, the trusted contact, and chat drafts per conversation.
- **Search and filter:**
  - Matches: search by name, filter by ring matched in, and filter Unread.
  - Safe Meet: Upcoming, Active and Past.
- **Share:** Safe Meet plan share (M4). "Share DriftDate" in You is optional. Nothing exports another member's data.
- **Empty states**, using real numbers only:
  - Nearby ring with 0 people: "No one new in your ZIP area right now. 12 people in your county", or "…no one in your county either" when that is true. Offer "Widen" only when the next ring has people.
  - Matches empty: "Wave at someone in Nearby. A match appears when you both wave."
  - Safe Meet empty: "Plan your first date safely", with a button that creates a plan.
- **Error and offline:**
  - Keep `BackendUnavailableApp` (`main.dart:118-193`), restyled.
  - Each list keeps `ErrorView` with Retry.
  - When the network drops mid-session, show an offline strip ("Offline. Showing what was loaded"). Wave, send and report are disabled with that message, not attempted silently.
  - **Safe Meet works fully offline.**

**M10. Proven.**
- `/Users/spatchava/agl/.flutter-sdk/bin/flutter analyze` returns 0 issues.
- `flutter test` passes in full. Today there are 25 test files, 244 `test(`/`testWidgets(` call sites (by grep). I did not run the suite at base, because running `pub get` could rewrite `pubspec.lock`. **Baseline pass state: not verified.**
- New tests for M1–M9 as listed under each item, plus absence tests: none of these strings appear in `lib/` or the rendered app:
  - "Welcome back", "Get started", "Not available yet", "in this version"
  - "Server", as a layer label
  - "Premium (demo)", "AI", "miles"
- **The 2.1(a) launch crash:** build a **release** build and run it on a **physical iPhone** if one is available. Otherwise use the iOS 26 simulator, and the QA report must say "simulator only". Quote the launch log.
- Launch and screenshot: Nearby (Ring view), Safe Meet plan, the Need-help sheet, the Passport and Shared ground. Look at them before declaring done.
- Commit path-limited (never `git add -A`). Never touch `fastlane/**` or `ios/Runner.xcodeproj/project.pbxproj`. Push to `main`.
- The backend changes in M2, M5 and M7 go on the `driftdate-schema` PR branch, with the PGlite evidence re-run. That branch is not merged or deployed without the founder.

### SHOULD
- **S1.** Delete `lib/app_env.dart` and `services/error_reporter.dart` (the portfolio duplicates) in favour of direct `AglCrash` calls and a one-line URL check, if simple. They are invisible infrastructure, and the 4.2.6 binary-similarity concern is the only reason to bother.
- **S2.** Date ideas in Safe Meet: "Need an idea?" offers `DateIdeas` from shared vibes when the plan has a match. Keep them as activity ideas only, with no venues and no events (EventSpark's territory).
- **S3.** Check-in on Apple Watch or a Live Activity showing the plan end time. Only if trivial; otherwise out of scope.
- **S4.** Translate the new Safe Meet and Passport strings into the existing 11 locales. If they are not translated, the review notes must keep saying translation is partial.
- **S5.** Delete the unused repo folders that confuse audits (`expo_legacy/`, `legacy-native-android/`, `desktop/`, `watchos/`, `web/`). This is a separate commit and needs owner confirmation first. They are not in the binary.

## 5. Data source

| Data | Source | Status |
|---|---|---|
| Accounts, profiles, photos, waves, matches, messages, blocks, reports | Supabase `smvvjivvlprjhzhoizym`, schema `driftdate` (Backend PR #1 plus the M2/M5/M7 amendments) | **Not deployed.** Founder approval #19 (Charter §2). Until it is deployed the app shows its honest error, not sample people. |
| Email confirmation | Supabase Auth, built-in mail | Rate limits and SMTP configuration not verified (F4) |
| Phone confirmation | Supabase Auth SMS | Provider not verified (F3). Hidden by build configuration if absent. |
| ZIP→county | Census 2020 ZCTA–county relationship file, bundled at build time | URL answered HTTP 200 on 2026-10-12, keyless |
| Area | Device GPS (coarse) plus on-device reverse geocode, reduced to ZIP-3, county and state | Already in `location_service.dart`. Raw coordinates are never stored. |
| Safe Meet plans, trusted contact, check-ins | On-device only | New |
| Trust facts of others | `driftdate.trust_facts()` security-definer function (booleans plus created-month) | New, in PR #1 |

No invented data anywhere: no sample members, no estimated "people nearby", no ratings, no compatibility percentages.

## 6. Store impact (proposed; store-compliance applies it, and this spec does not edit store files)

**Listing (`store/apps/DriftDate.json`):**
- **Name** (30 max): keep `DriftDate: Layered Dating`.
- **Subtitle** (30 max): `Date nearby. Widen slowly.` (26 characters). It replaces "Dating that widens slowly".
- **Category:** keep primary LIFESTYLE. Tinder, Hinge and Bumble are all `primaryGenreName: Lifestyle` per today's iTunes lookup. Secondary is SOCIAL_NETWORKING.
- **Description:**
  - It does not open with the app name, has no '——' headings, and has no "not yet available" or "Identity, background and financial checks are listed as not yet available" sentences.
  - It does not use the word "AI".
  - The AdMob paragraph stays only if F7 keeps ads, written plainly and once.
  - Draft:
  > Start with the people in your own ZIP area. When you've seen them, widen to your county, then your state, then everywhere — one ring at a time, only when you choose. DriftDate never shows how many miles away anyone is: your location is reduced to a ZIP prefix, county and state on your phone, and your exact position is never stored.
  >
  > Before a first date, make a Safe Meet plan: who, where, and when you expect to be done. Send it to a friend in one tap. At the time you set, DriftDate asks if you're home safe; if you need help, call 911 or text your friend from the same screen. Plans and your trusted contact stay on your phone.
  >
  > Every profile shows facts, not scores: email confirmed, signed in with Apple or Google, member since. You match only when you both wave, and you can report or block anyone from their card, a match or a chat.
  >
  > DriftDate is for adults 18 and over in the United States.
- **Keywords:** `local dating,nearby singles,safe dating,date check in,safety plan,privacy,zip code,match,meet,relationships`
- **Promotional text:** "Make a Safe Meet plan for your next date. DriftDate checks in at the time you set and helps you reach a friend if you need to."
- **Release notes:** what changed, honestly:
  - Safe Meet
  - county ring
  - messaging between people who have confirmed their email
  - Passport limited to real checks
  - new look

**Screenshots: retake all of them** (iPhone 6.9" ×5, iPad 13" ×5, Play phone). Show the real app in use, with no login or splash frame (2.3.3):
1. The Ring view with real counts, from a real account
2. A Safe Meet plan with a trusted contact
3. The "Are you home safe?" check-in and the Need-help sheet
4. The Passport with the facts that account really has
5. Shared ground between two real accounts, only if F6 allows real staff profiles. Otherwise Matches empty-state or Settings → Rings you're visible in.

No invented members in any frame. The files in `fastlane/screenshots/` and `fastlane/metadata/` are dirty with someone else's work at base. Store-compliance must coordinate before overwriting them. Make a new Play feature graphic in the tide-rings style.

**Review notes:**
- Replace the "2. DEVICES…" skeleton and the simulator boilerplate. State a physical-device test only if it actually happened, and name the device.
- **What to try:**
  1. Sign in with Apple.
  2. Build a profile.
  3. Allow location and see your ZIP-area ring.
  4. Open Safe Meet, make a plan for "Sam" ending in 2 minutes, and share it.
  5. Wait for the check-in and tap Need help.
- Be honest that the member base is small: "If no one is in your rings yet, Nearby says so with real counts; Safe Meet and the Passport work without any match."
- Remove section 8, the paragraph saying messages are refused as intended. Explain the email-confirmation rule for messaging instead.
- Remove the shared `qa@americangroup.ai` (`demo_account_name`). Set `demo_account_required: false` if F6 chooses the Sign in with Apple self-serve path. Otherwise use a DriftDate-only review account with an ordinary profile (F6).
- The audience is §2 of this spec, not the subtitle. Contact name: a real person (founder decision, already open portfolio-wide), not "App Reviewer".
- Account deletion text stays (5.1.1(v)), and it requires MA-044 to be applied.

**Privacy label (`store/privacy/DriftDate.json`)** replaces the shared 13-app label, which under-declares:
- **Add as Linked, App Functionality:**
  - COARSE_LOCATION (ZIP-3, county, state)
  - PHOTOS_OR_VIDEOS (profile photos uploaded to storage)
  - OTHER_USER_CONTENT (prompts, messages, reports)
  - PHONE_NUMBER (only if F3 enables SMS)
  - date of birth under OTHER_DATA_TYPES
- **Keep:** EMAIL_ADDRESS, NAME, USER_ID.
- **Keep, Not Linked:** CRASH_DATA, PERFORMANCE_DATA, PRODUCT_INTERACTION.
- **Ads:** keep DEVICE_ID and ADVERTISING_DATA only if F7 keeps ads.
- The trusted contact and Safe Meet plans stay on the device and are **not collected**.
- The developer should confirm against Apple's category definitions; the store-compliance owner signs off.

**Differentiation answers** (JSON §3, 4.3 questions): use §3 of this spec, with the competitor table labelled as based on store descriptions. §4 (beta testing) must stay as measured: 1 install, 0 feedback.

## 7. Out of scope
- Event discovery, event hosting or ticketing (EventSpark). Venue search and places APIs (they need keys).
- ID-plus-selfie, SSN, background or financial verification: there is no provider and no key, and the legal exposure is a founder matter.
- Video chat, voice prompts, push re-engagement, premium tiers and in-app purchases. Anything described as "AI".
- Auto-sending SMS or alerting authorities automatically. iOS does not allow silent SMS, and the copy must not imply it.
- Countries other than the U.S.
- Editing `store/apps/*.json`, `store/privacy/*.json`, fastlane metadata or `docs/`. Approving, merging or deploying Backend PR #1. Replying to or resubmitting to Apple (Charter §1, 5.6 freeze MA-043).

## 8. Founder questions
- **F1. Keep DriftDate?**
  - Apple's 4.3(b) names dating as a category it "will not accept … unless they offer a meaningfully different or improved experience".
  - The app has 1 recorded install and 0 TestFlight feedback (`store/apps/DriftDate.json` differentiation §4).
  - A dating app with no members cannot show its core job to a reviewer, however good the build. This spec makes the difference visible: Safe Meet works with no matches.
  - The options are (a) build this spec and resubmit, (b) build it and launch on Google Play first to grow a real member base, or (c) retire or merge the app (Charter §8). The office recommends (a) or (b). It cannot promise approval.
- **F2. Approve Backend PR #1 (#19) with the M2/M5/M7 amendments:** the messaging rule becomes "both confirmed email or phone", plus the new `trust_facts()` function and a `reports.message_id` column. This is production data (Charter §2). Without it the app cannot work at all.
- **F3. SMS for phone confirmation.** A Supabase SMS provider (e.g. Twilio) costs money and needs credentials (Charter §3, §4). Default if unanswered: no phone step anywhere; email, Apple and Google only.
- **F4. Email delivery.** Supabase's built-in mailer is rate-limited; the exact limit for this project is not verified. Custom SMTP needs credentials (Charter §4). Default if unanswered: built-in mailer, with the "Resend" button rate-limited in the app.
- **F5. Who answers reports?** Guideline 1.2 requires "timely responses to concerns". The `reports` table is insert-only and nothing reads it. A named person and a response target (e.g. 24 hours) are needed, and only the founder can assign that (Charter §7).
- **F6. App Review access and screenshots.**
  - (a) The reviewer self-serves with Sign in with Apple, and the app has no demo account.
  - (b) A DriftDate-only review account with an ordinary profile, not the shared `qa@`.
  - Separately: may two staff members create **real** profiles with consent so that screenshots and review can show a match and Shared ground? They must not be presented as other users, and nothing is invented. If not, the screenshots show the empty states.
- **F7. Ads in a dating and safety app** (Charter §3). Options: keep one banner at the end of the Matches list only, or remove AdMob from DriftDate. Either way there is no interstitial around Safe Meet. Recommended: remove. A safety feature next to full-screen ads undermines the angle.
- **F8. Legal text** (Charter §6). The privacy policy at `americangroup.ai/policy/driftdate/` must describe the trusted contact and Safe Meet plans (on the device only), the county lookup (on the device), photos and messages in Supabase, and report handling. Wording is the founder's decision.
- **F9. Resubmission.** When the build meets this spec, App Review communication is Charter §1 and the 5.6 freeze (MA-043) still applies. The office prepares the reply draft and stops there.
