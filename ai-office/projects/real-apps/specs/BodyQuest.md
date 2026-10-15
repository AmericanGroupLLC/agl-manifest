# Spec — BodyQuest: a family body-map you master one organ at a time

- **Author:** product-manager (AI office), 2026-10-12
- **Repo:** /Users/spatchava/agl/BodyQuest, branch `master`, base `619ba3871641bb27a52e99c0d0c65d58e5fcbc9b`
- **Plan:** projects/real-apps/plan.md (acceptance criteria 1–7)
- **Store state:** Apple rejected 1.1.0 under 4.3 / 4.2.6 (`.dist/rejections.json` key `BodyQuest`, the shared message md5 f5127d27). Google Play: PRODUCTION_DRAFT_STAGED.
- **Overlap ruling followed:** overlap.md G5. BodyQuest is learn-by-playing health education. It drops water, sleep and the health score. MyHealth owns personal logs.

---

## 1. Problem

### What the app is today (read from `lib/`, base sha above)

An 8-tab shell (`lib/main.dart:216-257`): Home, Games, Care, Diet, Workout, Explore, Shop, Breathe. The task brief says the screenshot shows a 9-item bar. The code has 8, and so does `fastlane/screenshots/en-US/iphone69-01.png`, which I viewed. The startup path is disclaimer, then a Supabase sign-in wall, then the shell (`main.dart:185-202`).

| Screen | What works | What is shallow, off-job or wrong |
|---|---|---|
| Home `dashboard_screen.dart` (1277 lines) | Water ±, sleep slider, BMI, health score, steps dialog, quotes, Profile Settings (sign out, delete account, Privacy choices) | All of it is **personal logging** (water 551-631, sleep 633-713, BMI 715-805, health score 467-535, steps/calories 537-549). That is MyHealth's job (overlap G5). The five quotes (59-63) and the "Good Morning" greeting (362) are generic filler. |
| Games `games_screen.dart` | Body Explorer with Adult/Kids text, Organ Match (shuffled pairs), a 10-question quiz with explanations, Achievement Garden saved via `AchievementStore` | Thin content: 5 systems and 12 organs (`data/health_data.dart:7-79`), with "Lungs" listed twice (`lungs`, `lungs_resp`), and **10 fixed questions in a fixed order**. Nothing brings a wrong answer back later. |
| Explore `explore_screen.dart` | Static cards | A **second, inconsistent body-system dataset** (`_BodySystem` list, 263-292) that disagrees with `HealthData`: bone is "5x stronger than steel" (284) in one place and "4x stronger than concrete" (287) in another. |
| Diet `diet_screen.dart` | Food list, macros, micronutrients, food-science cards | `_todayFoods` (line 18) sums calories and protein for the foods you pick (test `health_math_test` "selecting foods sums their calories and protein"). That is a diet log. |
| Workout `workout_screen.dart` | Rep counter, rest timer, XP | A workout-session tracker, not education. |
| Care `care_screen.dart` | 8 daily habits, a streak, XP, 4 tips | A habit log ("8 Hours of Sleep", "Drink 8 Glasses of Water", lines 315-322) that duplicates MyHealth. |
| Shop `shop_screen.dart` | 9 Amazon/iHerb affiliate search links (supplements, BP monitor, smartwatch, lab-test kit), a coin-budget "game", the app's **only** banner ad (`_BannerAdSlot`, line 226) | Does not serve the education job. Supplement and lab-test affiliate links in an app with a Kids mode are a liability. |
| Breathe `breathe_screen.dart` (993 lines) | A real guided 4-7-8 timer, lotus animation, science facts, a session-day streak | Good. Keep it. 4-7-8 has a 7-second hold, which is long for young children. |
| Login `login_screen.dart` | Email, Sign in with Apple (328), Google (339), guest (369) | The portfolio sign-in family. **No feature needs an account.** `Supabase.instance` is used only in `services/auth_service.dart:52` (grep over `lib/`). Everything else is local. |

**Factual errors in a health-education app** (these must go regardless of the redesign):
- `health_data.dart` quiz: "largest organ = Skin" is tagged `systemId: 'nervous'`.
- `health_data.dart` organ `liver` uses the heart emoji 🫀.
- "a cubic inch of bone can withstand 19,000 lbs" (`health_data.dart`, bones) and the steel/concrete pair in `explore_screen.dart:284,287` are unsourced and contradict each other.
- `explore_screen.dart:277` "Stomach acid is strong enough to dissolve metal", `:292` "Fever kills bacteria by raising temperature" and `:272` "The brain is 73% water" are unsourced pop-science claims.

### Why Apple called it a template

Measured tells for this app:
- the shared sign-in wall and scaffold (`login_screen.dart`, `auth_service.dart`, `supabase_config.dart`, `app_env.dart`, plus the shared `error_reporter.dart`)
- the shared demo login `qa@americangroup.ai`
- the byte-identical `ios/Runner/Base.lproj/LaunchScreen.storyboard` (shasum `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, measured)
- a near-black background with a neon-teal accent (`theme/app_theme.dart:6-15`: bg `#050C17`, primary `#00D4C8`)
- the app icon is a white heart with an ECG line on a teal-to-blue diagonal gradient (I viewed `assets/images/app_icon.png`). That is the portfolio's glyph-on-gradient formula, and it reads as a vitals tracker, not a learning game.
- the 13-app privacy label (`store/privacy/BodyQuest.json` declares email, name, user id and advertising data)
- '——' description headings
- review notes built from the numbered skeleton, with "Intended audience: Wellness, learned by playing", which is the subtitle pasted in
- only 3 iPhone screenshots

The product problem behind the tells: BodyQuest tries to be six apps (tracker, diet log, workout timer, habit app, shop, game) and none of them is deep. The one thing nobody else in the portfolio does is teach the body through play. Today that is 12 organs and 10 questions.

## 2. User

**A parent and a child aged about 8–12 learning together, and curious adults.** The adult wants something screen-time-worthy that actually sticks. The child wants a game. Today both get one pass through 10 questions and nothing that brings knowledge back.

Not for: anyone tracking their own health (that is MyHealth), or medical students (Kenhub's and Anatomist's audience, below).

Do not market it with the words "for kids" or "for children". App Store guideline 2.3.8 reserves those words for the Kids Category. I fetched the live guideline today (`curl developer.apple.com/app-store/review/guidelines/`): *"Use of terms like 'For Kids' and 'For Children' in app metadata is reserved in the App Store for the Kids Category."* Whether BodyQuest joins that category is founder question F3.

## 3. Product

### Core job
**Learn how your body works, and remember it.** Open the Body Map, pick an organ, read it at your reading level, and answer its cards. Cards you miss come back on later days until you know them.

### Signature feature: the Body Map Mastery loop
A full-body illustration in which every organ starts as a pencil outline and fills with colour as you master it. Mastery comes from **on-device spaced repetition** (Leitner boxes) over cards written at two reading levels. The home screen is the map itself, with the day's review count on it: "6 cards to review".

**Competitors.** Existence, price, rating and description were checked today with Apple's keyless iTunes Search/Lookup API (`itunes.apple.com/search` and `/lookup`). Web search was disabled in this session, and I have not installed any of these apps. Each gap below comes from the store description only.

| App | What its store description says | Gap BodyQuest fills |
|---|---|---|
| The Human Body by Tinybop (id682046579, $3.99, 4+, rating 4.21) | "completely self-guided" interactive models of 8 systems | The description mentions no quizzing and no retention. It is free exploration only. |
| The Human Body: Learn Anatomy, Learny Land (id1453160339, free, 4+, rating 4.51) | 9 interactive scenes, "play and learn freely, with no pressure" | The same: exploration, no recall loop. |
| Daily Anatomy Flashcards, Kenhub (id1271405479, free, 12+, rating 4.84) | Spaced repetition over "the 500 most important anatomical structures" for **healthcare students** | Spaced repetition exists here, but the audience is students and the rating is 12+. There is no family reading level. |
| Anatomist (id1114940725, free, 12+, rating 4.63) | "3,500+ anatomy identifications… for anatomy and medical students" | Same student audience. |

**Honest angle:** the kid-friendly apps explore but do not make knowledge stick. The apps that make it stick are written for medical students. BodyQuest puts spaced-repetition mastery over a whole-body map at a family reading level, with the same organ written for an 8-year-old and for the parent. The gap claims rest on store descriptions only, as stated above.

Buildable now by one developer: pure Dart scheduler, bundled content, `flutter_svg` (already in `pubspec.yaml`) or `CustomPainter` for the map, and `shared_preferences` or `sqflite` (both already dependencies). No network and no keys.

---

## 4. Acceptance criteria

### MUST (what Apple has to see for a real, distinct app)

**M1. No sign-in wall. The app opens into its own onboarding.**
- Remove `screens/login_screen.dart`, `services/auth_service.dart`, `services/supabase_config.dart`, `lib/app_env.dart` and the startup gate's sign-in branch (`main.dart:195-200`), plus `Supabase.initialize` (`main.dart:73-91`).
- Remove the `pubspec.yaml` dependencies only auth used (`supabase_flutter`, `google_sign_in`, `sign_in_with_apple`, `crypto`), after a grep proves no other use. Profile Settings loses Sign out and Delete account, because there is no account. Guideline 5.1.1(v) requires deletion only for apps that create accounts.
- Onboarding is 3 BodyQuest screens:
  1. The map, with the heart filling in as a demonstration.
  2. "Who's reading?" chooses the reading level, *Young Explorer* or *Grown-up*. This replaces the Adult/Kids chip. It is stored and changeable in Settings. No age, birthdate or name is asked.
  3. The existing educational disclaimer, reworded to drop "Your health tracking data stays on your device", because there is no tracking any more.
- Test: a fresh install reaches the map through onboarding, with no screen containing "Sign in", "Continue as guest" or "Welcome Back".
- *(Founder question F1 confirms this. The default if unanswered is to build it, because no server-side data exists. TestFlight records 0 installs as of 2026-10-12 per `store/apps/BodyQuest.json` differentiation §4.)*

**M2. Off-job features removed (overlap G5 plus this review).**
- Delete the water tracker, sleep tracker, health score, BMI, steps/calories and quotes from Home.
- Delete the Care habit tracker. Its 4 tips become lessons (M4).
- Delete the Diet "pick foods, see totals" selection (`_todayFoods`).
- Delete the Workout rep counter, rest timer and XP.
- Delete the **Shop** screen and its affiliate links and banner ad. It sells supplements and lab tests next to a children's reading mode, and it teaches nothing.
- After this, no code writes `water_glasses`, `sleep_hours`, `steps`, `weight`, `height`, `age`, `care_*` or workout XP. A one-time migration deletes those keys from existing installs.
- Tests that cover only removed features are deleted **in the same commit as the feature**, and the commit message lists each deleted test file. No test is deleted for any other reason.

**M3. Signature: Body Map Mastery with spaced repetition (`lib/learning/` or similar).**
- **Map.** A front-facing body illustration with a tappable region for every organ in the content (M4). A region is drawn as an outline at mastery 0 and filled with its system colour in 5 steps up to mastery 5.
  - A system toggle (all, or one of 8 systems) dims the other systems.
  - Tapping an organ opens its page: reading-level text, function, one sourced fact, its cards and mastery, and a "Review this organ" button.
  - Every region carries a semantics label, for example "Heart, circulatory system, mastery 2 of 5".
- **Scheduler.** A pure Dart class with no Flutter imports, using the existing injectable `dailyClock` (`services/daily_progress.dart:8`).
  - Leitner boxes 0–5 with due intervals of 0, 1, 3, 7, 14 and 30 calendar days, computed with calendar arithmetic as `previousDayKey` does.
  - A correct answer moves a card up one box. A wrong answer sends it to box 1, due tomorrow.
  - The daily queue is all due cards plus up to 8 new cards. "New per day" is adjustable to 4, 8 or 12 in Settings.
  - Organ mastery is the floor of the mean box of its cards.
- **Persistence.** Per-card state (box, due day, right count, wrong count, last seen) survives restarts. A corrupt or wrong-typed stored value resets that card only, never the whole store. That is the same defensive pattern `AchievementStore._read` uses.
- **Home** is the map, with a "Today's review: N cards" button and the review streak, which is consecutive days with a finished queue, using the existing `consecutiveDayStreak`.
- Finishing a review shows which organs gained a level and animates their regions filling in.
- The Achievement Garden stays, and flowers now bloom on real mastery events: a system fully at mastery 3 or higher, the first organ at 5, a 7-day review streak.

**M4. One content set, bigger and sourced (`assets/data/*.json`, loaded and validated at start).**
- Replace both `HealthData.bodySystems` and Explore's `_BodySystem` list with **one** dataset:
  - **8 systems:** circulatory, respiratory, digestive, nervous, skeletal, muscular, immune/lymphatic, integumentary (skin).
  - **At least 24 organs or structures**, with no duplicates (one "Lungs").
  - **At least 3 cards per organ (at least 72 total).** Each card has a Young Explorer and a Grown-up wording, 4 options, an explanation, and a `source` URL on an allow-listed host (medlineplus.gov, nih.gov, nhs.uk, cdc.gov, en.wikipedia.org).
- Diet and Workout content becomes lessons inside the digestive and muscular systems: the macros, micros and food-science cards, and "which muscles does a squat or a plank use". No calorie totals and no rep counting.
- The errors listed in §1 are removed or corrected. Skin moves to the integumentary system. The liver gets its own emoji or illustration.
- Every source URL is checked with curl (HTTP 200, after redirects) by the developer, and the output is quoted in the commit or the QA report.
- The quiz draws its questions from the cards, shuffled per run, and can be filtered by system.

**M5. Depth: search, empty, error and offline states.**
- **Search:** "Find an organ or word" over organ names, system names and card text. A result opens the organ on the map. A no-match state reads "No organ or word matches 'xyz'".
- **Empty state:** when nothing is due, show "All caught up. Next review: {real next due date}". On a fresh install the map shows all outlines and "Tap any organ to start".
- **Error state:** if the bundled JSON fails validation, show an error screen with the failing card id. A blank map is not acceptable.
- **Offline:** everything works offline. The only network use allowed is S2's optional "Read more", which must show an offline message instead of a spinner.

**M6. Own identity, distinct from MyHealth (primary `#338CEB`), HerJourney (primary `#E85E8A`, Inter) and the portfolio's near-black-and-neon look.**
- **Colour.** A *light "anatomy notebook"* theme:
  - paper background `#FFF8EC`
  - sepia ink text `#2B1E16`
  - primary terracotta `#B8432F` (seed)
  - secondary deep teal `#2E6B70`
  - one fixed, muted colour per system for the map fills, none of them a Tailwind default hex (the diagnosis lists the defaults to avoid)
  - no dark neon theme as the default; an optional dark "night notebook" variant is allowed.
  - `grep -rlis -e B8432F -e 2E6B70 -e FFF8EC` over the 42 `lib/` and `mobile/lib/` folders under `~/agl` found no match (exit 1). One of the 43 apps keeps its code outside those two paths and was not searched.
- **Typography.** Keep **Nunito** for body text. It is already the app's face and the only distinct one in the health set. Add **Fredoka** (OFL) for headings and numbers. A grep for "fredoka" over the same 42 `lib/` folders and every `pubspec.yaml` found no match.
  - **Bundle both as font assets** in `pubspec.yaml` and set `GoogleFonts.config.allowRuntimeFetching = false`. Today Nunito is fetched over the network at runtime (`test/support/real_fonts.dart:11` says so), so an offline first launch falls back to the system font.
- **Shape language.** Hand-drawn-style outlines: 2 px ink strokes and card corners of 20, not the portfolio's 12. Paper texture is optional.
- **Shell.** 4 destinations: **Map** (home), **Review**, **Play** (Organ Match, Quiz by system, and S1 Family Duel if built) and **Breathe**. Settings is a "Grown-ups" gear in the Map header.
  - On iOS use `CupertinoTabBar` with CupertinoIcons or custom glyphs, and Cupertino page transitions. On Android use a Material `NavigationBar`.
  - The 8-tab glass bar (`main.dart:296-430`) goes.
- **Icon.** Not a white glyph on a gradient, and not a heart with an ECG line. Use a cream square with a sepia-outline body figure whose heart and lungs are filled in terracotta and teal, the half-finished body map. Produce `assets/images/app_icon.png` (1024 px, no alpha for iOS) and the adaptive foreground, then regenerate with `flutter_launcher_icons`.
- **Splash.** Replace the shared storyboard: paper `#FFF8EC` background and the outline figure. Update the `flutter_native_splash` block in `pubspec.yaml` (currently `#050C17`, fullscreen) and regenerate.
  - **Proof:** `shasum ios/Runner/Base.lproj/LaunchScreen.storyboard` must no longer be `3f6a9b27d8…`.
  - Change only the storyboard and the `LaunchImage.imageset` / `LaunchBackground` assets. **Do not touch `ios/Runner.xcodeproj/project.pbxproj`**, which has someone else's uncommitted edits.
- **Copy.** Remove the template copy: "Welcome Back", "Sign in to continue your quest", the time-of-day greeting, the quotes, the "Works Offline" pill on Games, and "Earn Rewards". Onboarding and Settings copy is written for BodyQuest, for example "Who's reading?", "New cards per day", "Reading level".

**M7. Honest and 5.6-safe.**
- No demo login.
- No remote switches: the AglInsights Remote Config must not gate any BodyQuest feature, and the developer must check this by grep.
- No reviewer, region or date detection. No hidden gestures.
- No invented numbers: no "players", ratings or percentile claims. Mastery and streaks come only from the user's own answers.
- Breathe keeps "Educational content only — not medical advice".

**M8. Proven.**
- `/Users/spatchava/agl/.flutter-sdk/bin/flutter analyze` returns 0 issues.
- `flutter test` passes in full.
- New tests:
  - scheduler: promote, demote, due dates across a DST change, the new-card cap, a corrupt stored card
  - content integrity: 8 systems, at least 24 organs, at least 3 cards per organ, both wordings present, a valid answer index, unique ids, allow-listed https source, every card's system exists, skin in integumentary
  - widget: fresh install → onboarding → map with no sign-in; answering a review persists across a simulated restart and raises the region's mastery; search finds "diaphragm"; the caught-up empty state; switching reading level changes card text; the M5 error state
  - absence: no "Water Intake", "Sleep Tracker", "Health Score", "Wellness Store", "Sign in with Apple" or "Continue as guest" anywhere in the rendered app or in `lib/`
- Build for the iOS simulator, launch it, and screenshot Map, Review and an organ page. Do not ship without looking at it.
- Commit path-limited (never `git add -A`), never touching `fastlane/` or `ios/Runner.xcodeproj/project.pbxproj`, which are dirty with other people's work at base. Push to `master`.

### SHOULD

- **S1. Family Duel (pass-and-play).** Two players on one device take turns answering the same 10 cards, each at their own reading level. The result shows who knew which organ. It is local only, with no accounts and no leaderboard.
- **S2. "Read more" on an organ page** opens the card's source URL. Alternatively, it shows the Wikipedia summary fetched live from `https://en.wikipedia.org/api/rest_v1/page/summary/{title}`, which is keyless; I curl-verified it today (HTTP 200 for `Diaphragm_(anatomy)`, redirecting to "Thoracic diaphragm"). Show it only at the Grown-up level. It needs offline and error states, a `User-Agent` header, and the host added to `scripts/verify_api_hosts.py` coverage.
  - I also checked the MedlinePlus search API (`wsearch.nlm.nih.gov/ws/query?db=healthTopics`, HTTP 200, keyless). It returns **disease** pages ("small intestine" returned "Intestinal Cancer"), so it is **not** suitable as live content for this audience. Use MedlinePlus only as hand-picked source links.
- **S3. Breathe joins the respiratory lesson.** The lotus is replaced by, or offered alongside, lungs that inflate while the diaphragm drops, so the exercise teaches the mechanism. Add a gentler "Balloon breathing" pattern (in 3, out 4, no hold) for the Young Explorer level. The 4-7-8 pattern stays for Grown-up.
- **S4. Share a system certificate.** When a system reaches mastery 3 or higher, offer to share an image or text: "We mastered the Respiratory System in BodyQuest", with the organs listed. Use the system share sheet (`share_plus`) and include no personal data.
- **S5. Export progress** as plain text (mastery per organ, streak) through the share sheet, so a parent can keep it.
- **S6.** `error_reporter.dart` (an exact duplicate in 13 apps) is replaced by direct `AglCrash` calls, if that is simple. It is invisible infrastructure and is not required.

## 5. Data source

- **On-device only for every MUST item.** The content is a bundled JSON asset written by the developer. Each card carries a public-authority source URL (MedlinePlus, NIH, NHS, CDC or Wikipedia), checked by curl, with the output recorded.
- Progress lives in local storage. No Supabase tables are needed. After M1, BodyQuest no longer talks to Supabase `smvvjivvlprjhzhoizym` at all.
- Optional live data (S2 only): Wikipedia REST summary, keyless, verified HTTP 200 on 2026-10-12.
- Nothing invented: no sample users, scores, "players learning now", ratings or prices. A fresh install shows real zero progress.

## 6. Store impact (proposed; store-compliance applies it, and this spec does not edit store files)

**Listing (`store/apps/BodyQuest.json`):**
- **Name** (30 max): `BodyQuest: Learn Your Body` (26).
- **Subtitle** (30 max): `A body map you learn by heart` (29 characters). It replaces "Wellness, learned by playing".
- **Primary category: EDUCATION.** It is currently HEALTH_AND_FITNESS, which puts BodyQuest in the same shelf as MyHealth and HerJourney. On Play, also Education.
- **Description:** opens with what you *do*, not with the app name. No '——' headings, no "Six modules", no Shop paragraph, and no "for kids" or "for children" (2.3.8). Draft:
  > Tap the heart and it starts as a pencil outline. Answer its questions over the next few days and it fills with colour. That is how BodyQuest works: a map of the whole body (8 systems, 24+ organs) that you colour in by actually remembering how it works.
  >
  > Every organ is written two ways: plain and playful for a young reader, fuller for a grown-up. Read it side by side with your child and quiz each other.
  >
  > Questions you miss come back tomorrow; ones you know come back in a week, then a month. Each day's review takes a few minutes. Every fact links to its public source (MedlinePlus, NIH, NHS, CDC).
  >
  > Also inside: Organ Match, quizzes by body system, and guided breathing that shows what your lungs and diaphragm are doing.
  >
  > No account. Everything stays on this device and works offline. BodyQuest is education, not medical advice.
- **Keywords:** `anatomy,human body,organs,body systems,biology,science,quiz,flashcards,spaced repetition,learn,family,homeschool`. Drop "fitness, diet, workout, habits".
- **Promotional text:** "Colour in the human body by remembering it: 8 systems, two reading levels, and reviews that bring back what you missed."
- **Release notes:** describe the rebuild honestly. Removed: tracking, shop and sign-in. Added: map, spaced review, 8 systems.

**Screenshots: retake all of them** (iPhone 6.9" ×5, iPad 13" ×5, Play phone and tablet), from the real app on a fresh install plus a few days of genuine use:
1. The map with 3 organs filled in and "Today's review: 6"
2. An organ page at the Young Explorer level next to the Grown-up level
3. A review card with the explanation and source line
4. The end-of-review screen with regions filling in
5. Breathe (the lungs version if S3 is built), or Organ Match

No sign-in screen, no 8-tab bar. The current files in `fastlane/screenshots/` and `fastlane/metadata/` have someone else's uncommitted changes at base. Store-compliance must coordinate before overwriting them. **Feature graphic:** a new one in the notebook style, not the generated layout.

**Review notes:**
- Remove the "2. DEVICES…" skeleton and the simulator boilerplate.
- State plainly:
  - no account and no demo login (set `demo_account_required: false`, remove `qa@americangroup.ai`)
  - what to try: open the app, finish onboarding, tap Heart, run Today's review, watch the heart fill in, search "diaphragm"
  - the audience as written in §2, not the subtitle
  - physical-device testing **only if it was actually done**, naming the device
- Remove the "Account deletion" line (no accounts), and the "Supabase", "Google Sign-In" and "Sign in with Apple" external services. AdMob stays listed only if F2 keeps ads.

**Privacy label** (replaces the shared 13-app label): after M1 and M2, drop EMAIL_ADDRESS, NAME and USER_ID.
- If F2 removes ads, also drop DEVICE_ID and ADVERTISING_DATA.
- The remaining items are Crash Data, Performance Data and Product Interaction (Firebase via `agl_observability`), all not linked to the user.
- If F3 chooses the Kids Category, Firebase Analytics and AdMob must go too, and the label shrinks again.

**Differentiation answers (§3, §6 in the JSON):** use §3 of this spec, with the competitor table labelled as based on store descriptions.

## 7. Out of scope

- Any personal health logging (water, sleep, weight, BMI, steps, vitals, diet or workout logs). That is MyHealth.
- Reproductive or life-stage content. That is HerJourney.
- Accounts, cloud sync, leaderboards, multiplayer over the network.
- A 3D anatomy model, AR, paid content, in-app purchases.
- Editing `store/apps/*.json`, fastlane metadata, `docs/`, or replying to or resubmitting to Apple (Charter §1, 5.6 freeze MA-043).
- Translating the new content into the other 11 locales. English first; the shared `agl_i18n` labels still apply. The review notes must keep saying translation is partial.

## 8. Founder questions

- **F1. Remove accounts from BodyQuest?** No feature uses Supabase beyond sign-in (`auth_service.dart:52` is the only `Supabase.instance` use), and App Store Connect shows 0 installs. Default if unanswered: remove (M1).
- **F2. Monetisation (Charter §3).** The Shop is the only ad placement and holds all the affiliate links. Removing it (M2) leaves BodyQuest with no ads or affiliate income; the affiliate earnings to date are not verified. Options:
  - (a) no ads at all, removing AdMob and the UMP prompt (recommended for a family-learning app)
  - (b) a banner only on Grown-up screens, never on Young Explorer screens
- **F3. Kids Category and Play Families.** Joining Apple's Kids Category allows "for kids" marketing, but 1.3 requires no third-party analytics or advertising and a parental gate for links. That means removing Firebase Analytics from this app, and the S2 links would sit behind a gate. Not joining means the copy avoids those words (2.3.8). On Google Play, a target audience that includes under-13s triggers the Families policy. Recommended: not Kids Category; Education, family positioning, ads off (F2a).
- **F4. Overlap dependency.** overlap.md G5 says MyHealth drops its anatomy screen (`screens/train/anatomy_screen.dart`) so that BodyQuest alone owns anatomy learning. Please confirm. Without it, 4.3(a) duplication inside the account remains.
- **F5. Resubmission.** When the build meets this spec, App Review communication is Charter §1 and the 5.6 freeze (MA-043) still applies. The office will prepare the reply draft and stop there.

## 9. Implementation notes (software-developer, 2026-10-12)

Built on BodyQuest `master` (commits listed in the run report). Facts the store work needs:

- **Content shipped:** 8 systems, 28 organs, 85 cards (every card two wordings, 57 unique source URLs, all HTTP 200 by curl on 2026-10-12; the list is in the learning-engine commit message). The description draft's "24+ organs" stays true.
- **Screenshots:** `integration_test/store_screenshots_test.dart` now drives a fresh install with no account: onboarding → `01_map` → `02_organ` (Heart, Young Explorer) → `03_review` → `04_grew` → `05_map_after` → `06_breathe`. The old script (QA sign-in, water/sleep/diet) is gone.
- **Review notes:** no account, no demo login, nothing to unlock. What to try: finish onboarding, tap Heart, "Review this organ", answer, watch the heart fill; search "diaphragm"; Settings is the gear ("Grown-ups").
- **Privacy label input:** the app no longer contains Supabase, Google Sign-In or Sign in with Apple (dependencies removed; the `com.apple.developer.applesignin` entitlement removed).
- **F2 still open:** with the Shop gone there is **no ad placement left**, but `AdService` (AdMob + UMP consent) is still initialised at launch for the Grown-up level, so an EEA/UK user can still be shown Google's consent form although no ad is ever requested. Young Explorer = Kids mode, no ads at all. Recommend F2(a): remove AdMob and UMP from BodyQuest; that is a founder decision and was not done.
- **Not built:** S1 Family Duel, S4 certificate share, S5 export through the share sheet (a plain-text report exists in code, `BodyQuestModel.progressReport()`, but is not wired to a share sheet because `share_plus` is not a dependency), S6. S2 is partial: "Read more" opens the card's source in the browser at the Grown-up level; no in-app Wikipedia fetch.
