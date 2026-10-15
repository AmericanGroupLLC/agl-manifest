# Spec — Kinnav: get home on foot, with someone expecting you

- **Author:** product-manager (AI office), 2026-10-12
- **Repo:** /Users/spatchava/agl/Kinnav, branch `master`, base `4b72bfef6c752895be71ca30331aa505eecb125f`
- **Plan:** projects/real-apps/plan.md (acceptance criteria 1–7)
- **Store state:** Apple rejected 1.0.1 under 4.3 / 4.2.6 (`.dist/rejections.json` key `Kinnav`, the shared 4.3 text). A follow-up message added **2.3.3**: "The 6.7-inch iPhone and 13-inch iPad screenshots only display a login screen." Google Play: PRODUCTION_DRAFT_STAGED.
- **Overlap ruling followed:** overlap.md G7. iMaps owns driving navigation and road hazards. Kinnav owns on-foot personal safety and leaves `NAVIGATION`. This spec adds **no map, no routing and no turn-by-turn**. Directions are handed off to the phone's own maps app.
- **Dirty files at base (other people's work, do not touch):** `fastlane/**` (11 modified, 12 untracked) and `ios/Runner.xcodeproj/project.pbxproj` (`git status --short`, run 2026-10-12).

---

## 1. Problem

### What the app is today (read from `lib/` at the base sha)

Startup goes onboarding → Supabase sign-in wall → profile setup → home (`lib/main.dart:119-129`). There is no tab bar. A drawer (`screens/menu_drawer.dart:90-158`) leads to Guardians, Profile, Safety Contacts, Call History, Resources, Benefits, Language, How to use, Feedback and About.

| Screen | What actually works | What is shallow, placeholder or dead |
|---|---|---|
| Home `home_map_screen.dart` | A location status pill with real GPS through geolocator, and retry when it fails (`:166-248`) | The "map" is a placeholder. `widgets/live_map.dart:24` falls back to `MapView` unless `AppConfig.hasMaps`. `MAPS_API_KEY` is not in `env/prod.json`, and `ios/Runner/Info.plist:43-44` has an empty `GMSApiKey`, so every build shows "Map not available in this version" (`app_en.arb:354-355`). The bottom sheet is a guardian roster ("No guardians nearby right now", `arb:268`) for a guardian network that does not exist. Its main button is **CALL GUARDIANS** (`arb:58`). |
| Call options `call_options_screen.dart` | Slide-to-activate across 4 call types | 3 of the 4 types lead nowhere real: Voice and Video go to the mock call, and Text goes to the dead chat screen (`:22-31`). |
| Safe Call `safe_call_screen.dart` (854 lines) | Confirmed 911 dial (via `services/emergency.dart:7-63`), opens the SMS composer to safety contacts with location (`:183-235`), writes a history record on hang-up (`:251-260`) | Every call ends in `_CallPhase.unavailable` (`:36-41`) because `CallService` is `MockCallService` (`services/call_service.dart:35-46`, "it connects nobody"). The screen carries a **"DEMO · simulated safe call (no live video)"** badge (`arb:23`), plus video/speaker/map toggles and coach marks for a call that never happens. |
| Chat `chat_screen.dart` | Email-support and 911 buttons | **Dead control** (criterion 1). It exists to say "Live chat isn't available yet" (`:10-17`, `arb:308`). Two entry points lead to it: the chat bubble on Home (`home_map_screen.dart:125-131`) and "Text" in Call options. |
| Safety contacts `safety_contacts_screen.dart` | Add (name + phone), remove, persisted (`app_state.dart:200-216`) | No edit, no import from the phone's contacts, and no phone validation. A blank number is saved as the literal "No number" (`:66-69`). |
| Call history `call_history_screen.dart` | A persisted list of `CallRecord` (`models/call_record.dart`) | Records describe a call that did not happen: guardian count, duration, "Police". There is no search, filter, export or delete-one. |
| Guardians `guardians_screen.dart`, Guardian course `guardian_course_screen.dart` | Real Supabase reads of a `guardians` table (`services/supabase_guardian_service.dart:85`), with loading, error and empty states | No guardians exist. Whether the table exists in production was **not verified**: the read was refused as production access. Both screens say training is "coming soon" (`arb:222,486-487`). |
| Resources `modules_screen.dart`, `module_detail_screen.dart` | Lesson **titles** only (`models/content.dart:51-104`) | "Full lessons are coming soon" (`arb:457`). 3 of the 6 modules are `comingSoon: true` stubs. One of the 2 ad placements is here (`modules_screen.dart:37`). |
| Benefits `rewards_screen.dart` | — | All 6 entries are `comingSoon: true`. "Every entry is coming soon" (`content.dart:106-111`). The other ad placement is here (`rewards_screen.dart:53`). |
| Sign-up `sign_up_screen.dart`, `services/auth_service.dart` | Email/password, Apple and Google sign-in via Supabase, an 18+ checkbox | **No feature needs an account.** Supabase is used only for auth and the empty guardian roster (grep `Supabase.instance` in `lib/`: `app_state.dart:133`, `auth_service.dart:24,170`, `call_token_client.dart:94`, `supabase_guardian_service.dart:85`). Account deletion calls `rpc('delete_user')` (`auth_service.dart:170`). The office memory says that RPC is unapplied in production (MA-044); I did not re-check that in this session. |
| Profile setup / edit | Collects name, birth month and year, gender identity and languages | Birth date, identity and languages exist only to match guardians that do not exist. That is sensitive data collected for no function. |
| About, How to use, Legal, Feedback | Feedback opens a mail draft. Legal links out to kinnav.com. | About recruits "Benefits Partners" and "Partners" (`arb:522-525`) for programmes that do not exist. |
| Leftovers | — | `AppState.enterDemoMode()` seeds "Demo User" (`app_state.dart:184-197`). It has no caller in `lib/` today, but it ships in the binary. `AppConfig.screenshotMode` refers to "Demo mode (dev)" buttons (`config/app_config.dart:133-143`). `call_token_client.dart` targets an `API_BASE_URL` that is empty by design. |

**What is genuinely good and must survive:** the confirmed emergency dial, which returns whether a dial really happened and shows a "dial it yourself" fallback on iPads and SIM-less phones (`emergency.dart:15-63`); the SMS alert that counts only contacts with real numbers (`safe_call_screen.dart:199-235`); location that fails honestly instead of inventing coordinates (`location_service.dart:34-79`); defensive persistence (`app_state.dart:76-117`); and about 302 existing test cases (`grep -c "testWidgets\|test("` over `test/` and `integration_test/`).

### Why Apple called it a template

Measured tells for this app:
- **Shared splash.** `shasum ios/Runner/Base.lproj/LaunchScreen.storyboard` = `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, the portfolio-wide storyboard (run today).
- **Shared sign-in family:** "Sign in with Apple" / "Continue with Google" (`arb:157-158`), `lib/app_env.dart`, and an `auth_service.dart` with 0.52 similarity to Uscis-Case.
- **Shared demo login and contact:** demo login `qa@americangroup.ai`, review contact "App Reviewer" (`store/apps/Kinnav.json` `review_information`).
- **Shared privacy label:** the 13-app label (`store/privacy/Kinnav.json` declares EMAIL_ADDRESS, NAME, USER_ID, DEVICE_ID, ADVERTISING_DATA and more).
- **Generic onboarding:** "Get Started" (`arb:7`), "Welcome to Kinnav" (`arb:9`).
- **No typeface of its own.** No `fontFamily`, no GoogleFonts and no `fonts:` in `pubspec.yaml` (grep, 0 hits). Stock Material on iOS: 0 Cupertino widgets in `lib/`.
- **Shared settings furniture:** the `AglLanguageScreen` page (`menu_drawer.dart:130`) and the `AglAdBanner` placements.
- **Store copy and notes.** The listing says what the app does not do: "not available yet" ×3, "coming soon" ×2, "early access" in the description and the promotional text. The review notes use the shared skeleton ("2. DEVICES…", simulators only), and "Intended audience: Safety, support and self-care" is the subtitle pasted in. Category is NAVIGATION, shared with iMaps.
- **Inaccurate Resolution Center reply.** The 2026-09-29 reply told Apple "No account and no login are required" and listed "Apple In-App Purchase — paid features". Both are false: the app opens on a sign-in wall and has no IAP. The 2.3.3 rejection followed.

**The product problem behind the tells:** Kinnav was designed around a guardian network that does not exist. Every central surface is built for that network: the map of guardians, CALL GUARDIANS, the video call, the chat, guardian training, partner benefits. So the app is mostly honest "not yet" screens around two real features, a 911 dial and a text to contacts. Apple sees a shell.

## 2. User

**A woman walking somewhere alone, usually at night, who wants one particular person to know when she should be home, and to know if she isn't.** Typical moments:
- the walk from the train to her flat after a late shift
- crossing campus from the library
- leaving a first date
- walking to her car in an emptying car park

She already has the people she trusts in her phone. What she lacks is a simple way to tell them "I'm walking, expect me by 23:40", and a nudge that starts the alert if she doesn't arrive.

The app is built with women in mind, as kinnav.com says, but nothing in it is gated by gender, and the copy should not exclude anyone who walks alone.

**Not for:**
- driving (iMaps)
- continuous family location tracking (Life360's job)
- monitored dispatch: Kinnav has no call centre and must never imply one

## 3. Product

### Core job: **Safe Walk**
1. Before she leaves, she sets how long the walk should take and taps **Start walk**.
2. Kinnav opens a pre-written text to her chosen contacts with her ETA and location, and starts a countdown that keeps running when the phone is locked.
3. She taps **I'm safe** when she arrives, and Kinnav offers the "home safe" text.
4. If she doesn't check in, Kinnav raises a notification at the deadline. After a short grace period it raises a second one that opens the alert text with her current location, ready to send. **Call 911** (confirmed) is on screen the whole time.
5. Every walk is saved to her history.

### Signature feature: **Safe Havens: places you can walk into right now**
A list of nearby places that are **staffed and open now**, from OpenStreetMap: police stations, hospitals with an emergency department, pharmacies, and late-opening shops such as convenience stores and petrol station shops.
- Each row shows its distance and a **compass arrow** pointing to it from where she stands, so no map or routing is needed.
- Each row shows whether it is open now, with closing time, parsed on-device from the OSM `opening_hours` tag. If the tag is missing or can't be parsed, the row says so ("Hours not listed").
- The havens around her start point are fetched and cached when a walk starts. If the network drops mid-walk, or the public server is overloaded, the nearest havens and their arrows still work from the cache.
- One tap hands walking directions to the phone's own maps app.

**Competitors.** Checked today with Apple's keyless iTunes Search/Lookup API (`itunes.apple.com/search`, `/lookup`). Web search is disabled in this session (`WebSearch` hook: "Internet mode is not enabled"). I have not installed these apps, so every gap below is read from the **store description only**.

| App (iTunes id) | Rating / count | What its description says | Gap Kinnav fills |
|---|---|---|---|
| Noonlight (716262008), Lifestyle | 4.74 / 16,634 | Hold a button and release it with a PIN; a timer mode; "certified dispatchers… 24/7" | It routes alerts through its dispatch service. Kinnav texts *your own* people, with no service in between. The description says nothing about places to walk into. |
| bSafe – Never Walk Alone (459709106), Lifestyle | 3.38 / 208 | "voice activation, live streaming, audio/video recording, fake call, and follow me" | The description mentions no open-now places to go. |
| Bond – Personal Security (1439903736), Lifestyle | 4.75 / 1,058 | "virtual check-ins"; agents "send a car to pick you up and take you to a nearby safe place", listed under "Premium services" | A safe place is something an agent arranges, and it is premium. Kinnav shows them to you for free. |
| Aster: 24/7 Personal Safety (6447322524), Lifestyle | 4.76 / 17 | Automated texts at an event start time; "Features included without a subscription: none" | Kinnav's timer and havens need no subscription and no account. |
| Citizen (1039889567), News | 4.72 / 521,354 | Live crime map and incident alerts | It shows where danger is. Kinnav shows where help is open. |
| Apple's built-in Check In (Messages) | — | **Competitor not verified.** From my own knowledge it is iOS 17+ and iMessage-only, and it has no list of nearby open places. I could not confirm this in this session. | Kinnav works with any phone number through plain SMS, on Android too, and adds Safe Havens. |

**Honest angle:**
- Kinnav needs no account, no subscription and no monitoring company.
- Your contacts don't need the app.
- It adds the one thing none of the descriptions above mention: a live list of staffed places, open now, that you could walk into.

**Honest limit, stated in-app and in the listing:** iOS and Android do not let an app send a text by itself. At the deadline Kinnav prompts you and opens the alert ready to send, and you tap **Send**. Kinnav cannot alert anyone if you can't touch your phone. Automatic sending needs a paid SMS provider (founder question F3).

**Data check for Safe Havens.** `overpass-api.de` with `User-Agent: Kinnav-spec-check/1.0 (support@kinnav.com)`, 2026-10-12, roughly 22:00 UTC:
- Single-category queries answered: NYC police 200 (3.0 s); NYC hospitals 200 (1.1 s), 7 results, 4 with `emergency=yes` and `opening_hours=24/7`; NYC pharmacies 200 (1.0 s), 12 results, **9 with opening_hours**, e.g. `Mo-Fr 07:00-21:00; Sa 08:00-20:00; Su 09:00-19:00`; SF police 200 (2.2 s), 11 results, **0 with opening_hours**.
- **Every union query returned 504** (3 of 3). 3 of 7 single-category queries also returned 504.
- The mirrors `overpass.kumi.systems` and `overpass.private.coffee` timed out from this machine (curl code 000). That may be this machine's proxy, so they are **not verified**.
- So the source is real but flaky, and the design below depends on one query per category, a retry, caching and honest partial results.

**Hand-off URLs, keyless, curled today:**
- `https://maps.apple.com/?q=pharmacy&sll=…` → 301 to `maps.apple.com/search`
- `https://www.google.com/maps/search/?api=1&query=…` → 200
- `https://www.google.com/maps/dir/?api=1&destination=…&travelmode=walking` → 200

---

## 4. Acceptance criteria

### MUST (what Apple has to see for a real, distinct app)

**M1. The guardian-network shell is removed. No screen says "coming soon", "not available yet", "DEMO" or "early access".**
- **Delete these screens and services:** `chat_screen.dart` (the dead control), `call_options_screen.dart`, `safe_call_screen.dart`, `guardians_screen.dart`, `guardian_course_screen.dart`, `modules_screen.dart`, `module_detail_screen.dart`, `rewards_screen.dart`, `widgets/coming_soon_badge.dart`, `widgets/map_view.dart`, `widgets/live_map.dart`, `services/call_service.dart`, `services/call_token_client.dart`, `services/guardian_service.dart`, `services/supabase_guardian_service.dart`, `models/guardian.dart`, `models/call_type.dart`, and the `kModules` / `kRewards` content.
- **Remove from About:** the "Benefits Partner" and "Partner" recruitment copy.
- **Remove from AppState:** `enterDemoMode`, and the guardian, reward and module state and keys. Clear those keys from existing installs once, in a migration.
- **Remove from AppConfig:** the `screenshotMode` "Demo mode" path and the Agora/Maps flags.
- **Remove `google_maps_flutter`** from `pubspec.yaml` and the `GoogleMaps` import and `GMSServices` call from `ios/Runner/AppDelegate.swift:3,11-15`. Remove the empty `GMSApiKey` from `Info.plist` and the Android `geo.API_KEY` meta-data (`AndroidManifest.xml:11`).
- **Do not delete `supabase/migrations/0001_guardians.sql`.** It documents the founder's planned network (F1). The app must not reference it.
- **Tests:** tests that cover only removed features are deleted **in the same commit as the feature**, and the commit message lists each deleted test file. No other test is deleted or skipped.
- **Proof:** `grep -rniE "coming soon|not available yet|in this (build|version)|early access|DEMO ·|guardian" lib/` returns nothing, apart from a code comment explaining a migration.

**M2. No sign-in wall. Kinnav opens into its own setup.**
- **Remove auth:** `sign_up_screen.dart`, `services/auth_service.dart`, `lib/app_env.dart`, `services/secure_store.dart` (after the one-time legacy clear), `Supabase.initialize` (`main.dart:55-72`), the `signedIn` routing branch (`main.dart:126`) and the auth watcher (`app_state.dart:27,131-163`).
- **Remove auth-only dependencies,** after a grep proves no other use: `supabase_flutter`, `google_sign_in`, `sign_in_with_apple`, `crypto`, `flutter_secure_storage`, `image_picker`. Kinnav then makes no Supabase calls at all.
- **Profile:** replace profile setup with one optional field, "Your first name (used to sign your texts)". Stop collecting birth month and year, identity and languages, and delete them from existing installs.
- **Data erasure:** "Delete account" becomes **"Erase everything on this phone"** in Settings, with a confirm step. It clears contacts, history, templates and settings, and the test proves storage is empty afterwards. App Store guideline 5.1.1(v) applies only to apps that create accounts. Existing Supabase accounts are handled by founder question F2.
- **Setup flow:** first launch runs 3 Kinnav-specific steps, each skippable with "Not now" (no "Get Started", no "Welcome to"):
  1. "Who should know you got home?" Add the first safety contact.
  2. "Your emergency number." Prefilled from the device's region (911 / 112 / 999 / 000 table in code), editable, and shown on every Call button. This replaces the compile-time default (`app_config.dart:105-110`). It is a visible, user-editable setting, not hidden region logic.
  3. "Two permissions, and why." Location while in use ("to put your location in texts you choose to send, and to point you to Safe Havens") and Notifications ("so your walk timer can reach you when the phone is locked"). The system prompt appears only after the user taps Allow on Kinnav's explanation.
- **Proof:** a widget test runs a fresh install through setup to Home, and no screen contains "Sign in", "Log in", "Continue with Google" or "Get Started".

**M3. Core job: Safe Walk, end to end (`lib/walk/` or similar).**
- **Home card "Walk home":**
  - duration chips: 10, 15, 20, 30, 45 min, and Custom (5–180)
  - the arrival time shown live ("Expect me by 23:40")
  - contact chips with per-walk toggles, defaulting to every contact with a number
  - a big **Start walk** button
- **Start:**
  - The start time and the deadline are persisted **before anything else**, so a crash or kill can't lose the walk.
  - The location is read with a timeout (the existing `LocationService`). If it fails, the text goes without a link and the screen says "Sent without location".
  - Opens the SMS composer with the **start template**: "{name} here. I'm walking now and should arrive by {eta}. If you don't hear from me by then, please check on me. {location}". The location link is `https://www.google.com/maps/search/?api=1&query={lat},{lng}`.
  - Schedules two local notifications: the deadline and the deadline plus grace (default 2 min, settable 1–10).
- **Active walk screen:**
  - a large countdown ring and ETA
  - **I'm safe** (primary)
  - **+5 min**, which reschedules both notifications and offers an "Running late, new ETA {eta}" text
  - **Send alert now**
  - **Call {number}**, through the existing `Emergency.confirmAndDial`
  - the nearest cached Safe Haven with its arrow (M4)
  - The screen restores itself after an app kill, from the persisted walk.
- **Deadline:**
  - Notification 1: "Are you there yet? Tap I'm safe, or add time."
  - Notification 2: "Kinnav: tap to alert {n} contacts."
  - Tapping notification 2, or opening the app after the deadline, shows the **Alert screen**. It holds the alert text, "{name} hasn't checked in from a walk that should have ended at {eta}. Last location: {location}. Please call me", with a fresh GPS fix when one is available. It has one large **Send alert** button, and Call {number}.
  - The app must never say contacts *were* alerted. It says "Your messages app is open. Tap Send." The history records `alert_opened`, never `alert_sent`, because the OS doesn't report whether the user tapped Send.
- **I'm safe:** cancels both notifications and offers the "Home safe" text as a choice, not automatically.
- **Templates:** all three templates are editable in Settings, so the user can write them in her own language. Placeholders are validated. Reset to default is available.
- **Multi-recipient SMS:** the developer **must test** multi-recipient `sms:` on a physical iPhone and Android. iOS handling of comma-separated recipients is not verified (the current code joins numbers with `,`, `safe_call_screen.dart:235`). If iOS drops recipients, fall back to the share sheet or one composer per contact, and say which in the commit.
- **Android:** use exact alarms only when the user has granted `SCHEDULE_EXACT_ALARM`. Otherwise use an inexact schedule and show "On this phone the reminder may arrive a few minutes late. Allow exact alarms in Settings". Do not declare `USE_EXACT_ALARM`, which Play restricts.
- **iOS:**
  - Standard local notifications only. **Do not add capabilities or entitlements** such as Time Sensitive or Critical Alerts, background location or background modes. They need `project.pbxproj` edits, and that file is dirty with someone else's work.
  - If `pod install` changes `project.pbxproj`, do not commit it. Report it.
- **Packages:** `flutter_local_notifications` and `timezone` (free, keyless), plus the existing `geolocator`, `url_launcher` and `shared_preferences`.

**M4. Signature: Safe Havens (`lib/havens/` or similar).**
- **Source:** Overpass API `https://overpass-api.de/api/interpreter`, **one category per request**, run one after another, never a union (unions returned 504 in 3 of 3 tries today). Each request carries a timeout of 15 s and `User-Agent: Kinnav/<version> (support@kinnav.com)`, and gets one retry with backoff on 429, 504 or timeout.
- **Categories and tags:**

  | Category | Tags | Radius |
  |---|---|---|
  | Police | `amenity=police` | 3 km |
  | Emergency department | `amenity=hospital` + `emergency=yes` | 5 km |
  | Pharmacy | `amenity=pharmacy` | 1.5 km |
  | Open late | `shop=convenience`, `amenity=fuel` with `shop`, `amenity=fast_food`, each limited to features that have `opening_hours` | 800 m |

  Use `out center tags`. Send coordinates rounded to 3 decimals (about 110 m). That rounding is the privacy floor declared in §6.
- **Open-now parser** (pure Dart, no Flutter imports, injectable clock and timezone):
  - **Must handle:** `24/7`, weekday ranges and lists (`Mo-Fr`, `Sa,Su`), multiple rules separated by `;`, multiple time spans separated by `,`, spans past midnight (`18:00-02:00`), `off` and `closed`, and `PH off`, where a public holiday is treated as unknown.
  - **Must return:** `open` with a closing time, `closed` with the next opening time, or `unknown`. Anything not handled, such as `||` fallbacks with comments, week numbers or sunrise, returns `unknown`. **It never guesses `open`.**
  - **Proof:** a unit test for each real string captured today, including `Mo-Fr 07:00-21:00; Sa 08:00-20:00; Su 09:00-19:00` and `06:00-24:00 open "Store" || Mo-Fr 07:00-19:00 open "Pharmacy"`, which must give `unknown` or the correct store hours. It is not allowed to crash.
- **Ranking:** open-now first, then unknown hours, then closed. Within each group, sort by straight-line distance. Police and ED with unknown hours are shown with "Hours not listed. In an emergency call {number}". Police stations are never claimed to be open when no tag says so.
- **Row:** name (or "Unnamed {category}"), category icon, distance in the user's units, a **compass arrow**, the open/closed/unknown line, and **Walk there**.
  - The compass arrow combines bearing from the current GPS fix with the device heading. Use `flutter_compass` or `sensors_plus` (keyless). When no heading is available, show a cardinal word such as "NE" and no rotating arrow.
  - **Walk there** opens `maps.apple.com/?daddr=lat,lng&dirflg=w` on iOS or `google.com/maps/dir/?api=1&destination=…&travelmode=walking` on Android, so Kinnav never draws a route.
  - A footer on every list reads "Place data © OpenStreetMap contributors", linking to `openstreetmap.org/copyright`, as ODbL requires.
- **Cache:** the result per category is keyed by a ~1 km grid cell and kept for 7 days, with "Updated {time}" shown.
  - Starting a walk pre-fetches all four categories for the start cell in the background, without blocking the walk.
  - During a walk and on the Alert screen, the nearest haven comes from the cache, with the live distance and arrow recomputed from GPS.
- **States, each per category, so one failure doesn't blank the list:**
  - loading
  - "Couldn't reach OpenStreetMap. Showing places saved {time}" (stale cache)
  - "Couldn't load pharmacies. Retry" (no cache)
  - "No police station within 3 km", which also offers "Search a wider area" (double radius, once)
  - offline
  - location off, which offers "Search Maps instead"
- **"Search Maps instead"** is always present at the bottom and opens the system maps search for that category near the user (the hand-off URLs curled above). It is keyless and works whenever Overpass is down.
- **Filter:** chips for All, Police, Emergency, Pharmacy, Open late. A toggle **Open now only**.
- **Home:** a "Safe Havens near you" card shows the 3 best rows, and **See all** opens the full list.

**M5. Depth: history, contacts, search and export.**
- **Walk history** replaces Call History. It is still the "Safe Call history" the overlap ruling assigns to Kinnav, now recording real events.
  - **Each record:** start, planned ETA, end time, outcome (`checked_in`, `extended` ×n, `alert_opened`, `emergency_dialled`, `abandoned` if the app found an unfinished walk more than 12 h old), contacts chosen, and start and end location only when the setting "Save locations in history" is on (default **off**).
  - **Migration:** old `CallRecord` entries are kept and shown as "Safe Call (earlier version)". They are not deleted.
  - **Search** by contact name or note. **Filter** by outcome and by date range.
  - **Swipe to delete** one record, and **Clear all** with a confirm.
  - **Add a note** to a walk ("Man followed me from the station").
  - **Export:** a selected walk, or a date range, goes through the share sheet (`share_plus`) as plain text: times, outcomes, notes, and coordinates if saved. The point is "a record for a police report or for yourself". No PDF is needed.
- **Safety contacts:**
  - add, **edit** and remove
  - phone number required and validated, with no "No number" placeholder
  - optional "Add from Contacts", using the system picker only (`flutter_native_contact_picker` or similar, with no full address-book read). If the picker needs a permission or plist key that touches `project.pbxproj`, skip it and report.
  - per-contact "Include in walk texts" default
  - empty state: "Add the person who should know you got home"
  - migration: stored "No number" contacts get a "Needs a number" badge and are excluded from texts, as they are today.
- **Empty, error and offline states:**
  - Home with no contacts: the Start walk button is still usable, and the text step explains that it needs a contact.
  - No history: "Your walks will be listed here."
  - Location denied: an explicit banner with an "Open Settings" deep link.
  - Notifications denied: a banner explaining that the timer can't reach a locked phone.
- **Offline:** every MUST works offline except a fresh Safe Havens fetch, which falls back to the cache or "Search Maps instead".

**M6. Own identity, distinct from the portfolio scaffold and from HerJourney (pink `#E85E8A`, Inter).**
- **Colour: "Dusk"**, which keeps kinnav.com's purple family but moves it to a deeper, quieter key.

  | Role | Hex | Use |
  |---|---|---|
  | Seed and primary | `#3B1F5C` (plum ink) | primary colour |
  | Background | `#F4EFE6` (warm parchment) | screen background |
  | Accent | `#E8A33D` (marigold) | the gold of the icon's trident; used for Start walk, the countdown ring and haven arrows |
  | Emergency | `#B3261E` | used **only** for Call {number} and the Alert screen |
  | Active-walk surface | `#1F1A24` | the active-walk screen only, so the phone doesn't light up her face at night; marigold on it, not neon |

  - **Uniqueness check:** `grep -rlis` for each of the five hexes over the 41 other apps' `lib/` and `mobile/lib/` folders under `~/agl` returned no match (run today). One app keeps its code outside those paths and was not searched.
  - The old `AppColors` lavender/`#BF6EEE` scaffold (`theme/app_theme.dart:12-56`) goes.
- **Typography: Atkinson Hyperlegible** (SIL OFL, from the Braille Institute) for everything. It was designed for legibility at a glance and in low vision, which suits reading a countdown while walking.
  - **Bundle it as a font asset** in `pubspec.yaml`. Do not fetch it at runtime.
  - Countdown digits use tabular figures at weight 700.
  - **Uniqueness check:** `grep -rlis atkinson` over the same 41 folders and every `pubspec.yaml` found no match (run today).
- **Shape language:** pill buttons (fully rounded, stadium), cards at radius **20**, never the portfolio's 12. The countdown is a thick ring of 10 px stroke. Haven arrows are a custom drawn chevron, not a Material icon.
- **Home layout** has no tab bar, no drawer and no bottom NavigationBar:
  - a header with the Kinnav wordmark, a History button and a Settings button
  - the Walk home card (M3)
  - the Safe Havens card (M4)
  - a full-width outlined **Call {number}** pill pinned at the bottom
- **Platform-adaptive.** On iOS, use CupertinoIcons for the header and list affordances, Cupertino page transitions, `showAdaptiveDialog` (so the 911 confirmation is a Cupertino alert), and `CupertinoSwitch` in Settings. On Android, Material.
- **Splash:** replace the shared storyboard with a parchment `#F4EFE6` background and the shield-and-trident mark. Change **only** `LaunchScreen.storyboard` and `LaunchImage.imageset` / background assets. **Never** touch `project.pbxproj`. **Proof:** the new shasum is not `3f6a9b27…`.
- **Icon:** keep the existing bespoke shield, wings and trident artwork (`ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png`, viewed). It is not the generated glyph-on-gradient. Replace its purple gradient background with flat plum `#3B1F5C` so it matches the new palette, and regenerate all sizes plus the Android adaptive icon. Keep no alpha channel on iOS.
- **Copy:** remove "Welcome to Kinnav", "A new way of women safety and empowerment", "Get Started", "Invite a Friend", "Kinnav member / Community Member" and "There's more to Kinnav". Settings has Kinnav's own sections:
  - **Your walk:** default duration, grace period, templates
  - **Emergency number**
  - **History:** save locations, export, clear
  - **Language:** an inline list of Kinnav's 6 locales, not the shared `AglLanguageScreen` page
  - **Privacy choices:** the UMP row, kept because the law requires it, and only if ads remain (F4)
  - **Erase everything on this phone**
  - **About**, rewritten in 4 sentences without partner recruitment.

**M7. Honest and 5.6-safe.**
- No demo login, no demo mode, and no `SCREENSHOT` define that changes the UI.
- No remote switches: AglInsights Remote Config must not gate any Kinnav feature. The developer checks this by grep and quotes the result.
- No reviewer, region or date detection. The only region-dependent value is the visible, editable emergency number prefill. No hidden gestures.
- No invented data: no sample havens, no fallback coordinates, no "X women walked home safely" counters, no ratings. A haven exists only if OSM returned it.
- The app never claims a text was sent, a contact was notified, or help is coming. Copy says "Your messages app is open. Tap Send." Kinnav states plainly that it is not an emergency service and has no call centre.
- Ads, if F4 keeps them, never appear on Home, the active walk, the Alert screen, Safe Havens or contacts.

**M8. Proven.**
- `/Users/spatchava/agl/.flutter-sdk/bin/flutter analyze` returns 0 issues.
- `flutter test` passes in full.
- **New tests:**
  - **Walk state machine:** start → check-in; start → extend ×2 → check-in; deadline → alert_opened; app killed mid-walk and restored; abandoned after 12 h. Notifications scheduled and cancelled, through a fake notifier. Persisted before the composer opens.
  - **Templates:** placeholder substitution; the location-failed branch omits the link and says so; contacts without a number are excluded.
  - **Opening-hours parser:** at least 15 cases, including the strings captured today, overnight spans, `off`, and unparseable input → `unknown`. A DST-change day.
  - **Havens service:** one request per category; a 504 then 200 retry; a 504 with cache → stale banner; a 504 without cache → per-category error while other categories render; rounding of coordinates to 3 dp in the request; ranking order; OSM attribution present.
  - **Widgets:** fresh install → setup → Home with no sign-in; Start walk opens `sms:` with the expected body (fake url_launcher, as `test/functional/emergency_test.dart` already does); Alert screen copy never contains "sent" or "notified"; history search, filter, delete and export text; Erase everything empties storage.
  - **Absence:** none of "Sign in with Apple", "CALL GUARDIANS", "Guardian", "coming soon", "DEMO", "Benefits", "Get Started" in the rendered app or in `lib/`.
- Keep the existing emergency-dial tests (`test/functional/emergency_test.dart`, `emergency_dial_failure_test.dart`) passing unchanged.
- **Look at the result.** Build for the iOS simulator, launch, and screenshot Home, the active walk, the Alert screen and Safe Havens. The developer must look at them before shipping.
- **Device test.** If a physical device is available, test multi-recipient SMS and the locked-phone notification on it, and say which device. If not, report "not verified on a device".
- **Commit.** Commit path-limited (never `git add -A`). Never touch `fastlane/**` or `ios/Runner.xcodeproj/project.pbxproj`. Push to `master`.

### SHOULD

- **S1. Loud "I need attention" alarm** on the Alert screen and Send alert now: a siren sound at full volume plus the flashlight strobe (`audioplayers` is already in the local pub cache). Off by default and opt-in per walk.
- **S2. "Send my location again"** during a walk: a fresh fix in a new composer, "Update: I'm here now {location}".
- **S3. Home-screen quick actions** (`quick_actions` package): "Start a 15-min walk" and "Call {number}" from the app icon long-press. They are visible, not hidden.
- **S4. Arrival suggestion:** if the user picked a haven or a saved "Home" coordinate, show "You're within 50 m of Home. Check in?" while the app is in the foreground. This is not background geofencing.
- **S5. Translate the new safety-critical strings** (911 confirmation, alert screen, setup) into the 5 existing locales (ar, es, fr, hi, zh), with a human review note in the commit. Until then the editable templates let users write their own.
- **S6.** `AglLanguageScreen` is replaced entirely by the inline picker. The `agl_i18n` delegates stay.

## 5. Data source

- **On-device:** walks, history, contacts, templates and settings in `shared_preferences`, through the existing `Storage`. GPS through `geolocator` (when in use only). Notifications through `flutter_local_notifications`. Phone dialler and messages through `url_launcher` `tel:` / `sms:`.
- **Keyless public API:** OpenStreetMap Overpass at `overpass-api.de`. It answered single-category queries today with HTTP 200 and returned 504 on unions and on about 40% of single queries (§3), hence the cache and per-category retry. `scripts/verify_api_hosts.py` picks up the host from the code automatically.
- **Hand-off only, no data fetched:** `maps.apple.com` and `www.google.com/maps` URLs, curled today (301 and 200).
- **Supabase `smvvjivvlprjhzhoizym`: not used** after M2. No new tables.
- **Nothing invented.** A fresh install shows zero walks, zero contacts, and only the havens OSM actually returns.

## 6. Store impact (proposed; store-compliance applies it, and this spec does not edit store files)

**Listing (`store/apps/Kinnav.json`):**
- **Name:** keep `Kinnav`.
- **Subtitle** (30 max): `Walk-home timer, safe places` (28). It replaces "Safety, support and self-care".
- **Primary category: LIFESTYLE.** It replaces NAVIGATION (overlap G7). The iTunes lookups above show Noonlight, bSafe, Bond and Aster all filed as Lifestyle, so this is where users look. Secondary: UTILITIES, or none. On Play: Lifestyle.
- **Keywords:** `walk home,safety timer,check in,safe walk,personal safety,women safety,emergency,SOS,late shift,campus,pharmacy open now`. Drop "guardian, escort, self care".
- **Description.** It opens with the moment, not the app name. It has no ALL-CAPS headings, no "coming soon", no "early access", no "not available yet", and no guardian network or benefits. Draft:
  > Tell someone you're walking, and when to expect you. Pick how long the walk should take and tap Start walk: Kinnav opens a text to the people you chose with your arrival time and location, then counts down, even with your phone locked.
  >
  > Tap I'm safe when you get there. If you don't, Kinnav reminds you at your arrival time, and a couple of minutes later it opens the alert to your contacts with your latest location, ready to send. Your phone asks you to tap Send; Kinnav can't send texts on its own.
  >
  > Safe Havens shows staffed places near you that are open right now (police stations, emergency departments, pharmacies, late-night shops) with an arrow pointing the way and opening hours from OpenStreetMap. Kinnav saves the list when you set off, so it still works if your signal drops.
  >
  > Your emergency number is one confirmed tap away on every screen.
  >
  > Every walk is kept in your history, with your notes, and you can export it as text.
  >
  > No account. No subscription. Your contacts don't need the app. Everything stays on your phone. Kinnav is not an emergency service and has no call centre.
- **Ads paragraph:** only if F4 keeps ads. It must name the screens that show them.
- **Promotional text:** "Set a walk timer, text your ETA to the people you trust, and see which places nearby are open right now."
- **Release notes:** describe the rebuild honestly. Removed: sign-in, the guardian screens, resources and benefits. Added: Safe Walk, Safe Havens, walk history and export.

**Screenshots: retake all of them** (this answers the 2.3.3 rejection): iPhone 6.9" ×5, iPad 13" ×5, Play phone and tablet, all from the real app.
1. Home: Walk home card ("Expect me by 23:40") and Safe Havens card
2. The active walk: countdown ring on the dusk surface, I'm safe
3. Safe Havens list: open-now badges, arrows, filter chips
4. The Alert screen with the prepared text
5. Walk history with a note and Export

- No sign-in screen and no guardian UI.
- Haven data must be real OSM results for the city shown. Name the location in the screenshot notes; no edited data.
- The current `fastlane/screenshots/` and `fastlane/metadata/` files have someone else's uncommitted changes at base. Store-compliance must coordinate before overwriting them.
- **Feature graphic:** new, in the Dusk palette, with no Flutter logo and not the generated layout.

**Review notes:**
- Drop the "2. DEVICES…" skeleton and the simulator boilerplate. State plainly:
  - **No account and no demo login.** Set `demo_account_required: false` and remove `qa@americangroup.ai`.
  - **What to try:** open the app, finish the 3 setup steps (add any phone number as a contact), set a walk to 10 min, tap Start walk (the messages app opens; cancel is fine), tap +5 min, then open Safe Havens. To see the alert path without waiting, tap **Send alert now**.
  - **Audience:** as written in §2, not the subtitle.
  - **External services:** OpenStreetMap Overpass (place data), the device's messages app, phone dialler and maps app, Firebase Crashlytics/Analytics (`agl_observability`), and AdMob only if F4 keeps ads.
  - **No Supabase, no Google Sign-In, no Sign in with Apple, no In-App Purchase.** The 2026-09-29 reply wrongly listed IAP, so say this explicitly.
  - **Physical-device testing only if it was actually done,** naming the device.
- **Drop the "Account deletion" section** (no accounts). Mention "Erase everything on this phone" instead.
- **Review contact:** replace "App Reviewer" with the real person or role who answers. Only the founder can name them (F5).

**Privacy label** (replaces the shared 13-app label):
- Remove EMAIL_ADDRESS, NAME and USER_ID.
- Add **Coarse Location: App Functionality, not linked, not tracking.** Rounded coordinates go to Overpass for the haven lookup. Precise location goes only into texts the user sends herself, which Apple does not count as developer collection. That reading is the office's interpretation, and store-compliance should confirm it against Apple's definitions.
- Keep Crash Data and Product Interaction (Firebase, not linked).
- Keep DEVICE_ID and ADVERTISING_DATA only if F4 keeps ads.
- Play Data safety must match.

**Differentiation answers (`differentiation` §3 and §6 in the JSON):** use §3 of this spec. Label the competitor table as based on store descriptions. In §6, say iMaps is driving navigation and that Kinnav has no map or routing.

## 7. Out of scope

- Any guardian or volunteer responder network, live calls, video, chat, training, partner benefits, monitored dispatch. These are founder decisions (F1, F3).
- Automatic SMS sending without a user tap (needs a paid provider, F3).
- Background location tracking, geofencing, Live Activities, widgets, Apple Watch, Time Sensitive or Critical Alert entitlements. They all need native target or `project.pbxproj` changes, and that file is dirty.
- A map, routing or turn-by-turn. That is iMaps. Kinnav hands off to the system maps app.
- Crime maps or incident feeds. That is Citizen's category, and we have no licensed data.
- Accounts, cloud sync, multi-device.
- Editing `store/apps/*.json`, fastlane metadata or `docs/`. Replying to Apple or resubmitting (Charter §1; 5.6 freeze MA-043).
- The kinnav.com website copy, which still describes the guardian network. Flagged in F1.

## 8. Founder questions

- **F1. Park the guardian-network concept in the app?** The app, kinnav.com and `supabase/migrations/0001_guardians.sql` all describe vetted guardians who take Safe Calls. None exist, and every screen built for them is a "not yet" screen Apple counts against us. This spec removes them from the app (M1) and keeps the migration file. Confirm. If the network is still planned, it returns as a separate project with real people, vetting and a call backend (Agora keys, token server; money and legal).
- **F2. Existing Supabase accounts.** M2 removes sign-in. Any accounts already created by testers (TestFlight records 4 installs and 48 sessions in 365 days per `store/apps/Kinnav.json` differentiation §4; the number of Kinnav auth users is **not verified**) stay in the shared Supabase project. Deleting them is a production-data action (Charter §2). Options: (a) delete them via the backend workflow you approve; (b) keep a web deletion request at kinnav.com/contact. The privacy policy text is legal (Charter §6).
- **F3. Automatic alerts.** Kinnav cannot text anyone unless the user taps Send. That is the honest limit, and it matters most when she can't touch her phone. Automatic sending needs a paid SMS provider (for example Twilio) behind a Supabase Edge Function, which means money and credentials (Charter §3, §4). Do you want that as a later paid project?
- **F4. Ads in a safety app (Charter §3).** Both current ad placements (Resources, Benefits) are deleted with those screens. The app is not live on either store, so the ad revenue at stake is $0 as far as measured. Options: (a) no ads, removing `agl_ads`, the UMP prompt and the advertising entries in the label (recommended); (b) one banner on the History screen only. Default if unanswered: (a).
- **F5. App Review contact.** Who is the named reviewer contact for Kinnav instead of "App Reviewer"?
- **F6. Resubmission.** When the build meets this spec, App Review communication is Charter §1 and the 5.6 freeze (MA-043) applies. The office will prepare the reply draft, including corrections to the false "no login / IAP" statements of 2026-09-29, and stop there.

## 9. Implementation notes (software-developer, 2026-10-13, Kinnav commit 12b4d93)

Facts store-compliance and the founder need before §6 is applied. This section is notes only; no store file was edited.

- **Ads removed (F4 default (a)).** `agl_ads` is no longer a dependency. `GADApplicationIdentifier` and the SKAdNetwork list were removed from Info.plist, and the AdMob meta-data from AndroidManifest. The privacy label should drop ADVERTISING_DATA and DEVICE_ID, and the ads paragraph should not be added. If the founder picks F4(b), this has to be re-added on purpose.
- **Privacy manifest changed in the binary.** `ios/Runner/PrivacyInfo.xcprivacy` no longer declares EmailAddress, UserID or PhotosorVideos. It still declares Precise and Coarse Location (App Functionality, not linked). The App Store label should match (§6).
- **Sign in with Apple entitlement removed** from `ios/Runner/Runner.entitlements`. No pbxproj change was made. The App ID capability can stay.
- **Android permissions added:** RECEIVE_BOOT_COMPLETED and SCHEDULE_EXACT_ALARM, for the walk reminders. POST_NOTIFICATIONS and VIBRATE come from the plugin. USE_EXACT_ALARM is not declared. Play Data safety needs no new data types for these.
- **Network:** the only host the app calls is `overpass-api.de`, with rounded coordinates. Maps hand-offs open `maps.apple.com` / `www.google.com/maps` in the system app.
- **Translations:** every new string exists in es/fr/hi/zh/ar, written by the developer agent and **not reviewed by a person** (S5 is still open).
- **Not verified:** multi-recipient SMS and locked-phone notifications on a physical device (none was connected). The hand-off sheet always offers one composer per contact and the share sheet, in case iOS drops recipients.
- **Review notes, "what to try":** still accurate as written in §6. Send alert now opens the Alert screen at once.
- **kinnav.com/privacy and /terms** are linked from Settings. They may still describe accounts and the guardian network (F1/F2); that is legal text and a founder decision.
