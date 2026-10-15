# Spec: yourtube → an archival-film player: public-domain films by decade, with a contact sheet of every film

Author: product-manager (AI office), 2026-10-12
Project: real-apps (`../plan.md`, criteria 1–7)
Repo: `/Users/spatchava/agl/yourtube` (Flutter project at the repo root. `CLAUDE.md` says `yourtube_app/`, but that is stale: `lib/` and `pubspec.yaml` are at the root, and `flutter analyze` ran from the root.)
Base: `master` @ `58c3dbf7f265a9a63be0ceccf1b6c9eddd55f388` (from `git rev-parse HEAD` and `git branch --show-current`, run 2026-10-12)

Baseline, run 2026-10-12 at the repo root with `/Users/spatchava/agl/.flutter-sdk/bin/flutter`:
- `flutter analyze` → "No issues found! (ran in 43.0s)"
- `flutter test` → "+389: All tests passed!"

**Preconditions: founder decisions Q1 (pivot) and Q2 (name).**
- This spec turns a general video aggregator into a product with one specific job. If the founder rejects the pivot (Q1), do not build this spec. Send it back to product.
- M1 (the name) can ship before Q2 is answered, because the name lives in one constant. But it must not be **submitted** until Q2 is answered.

**Other people have uncommitted work in this repo. Do not touch it.** `git status --short` shows changes under `fastlane/**` (descriptions, `review_information/notes.txt`, screenshots, plus new untracked `iphone69-0*.png`, `ipadpro13-0[45].png` and `tenInchScreenshots/0[45].png`), `ios/Podfile.lock` and `ios/Runner.xcodeproj/project.pbxproj`.
- Removing Supabase, Google Sign-In and Sign in with Apple (M5) changes the pods. That normally rewrites `ios/Podfile.lock`, and possibly `project.pbxproj`. **Both already carry someone else's uncommitted edits.**
- The developer must not commit, revert or overwrite those two files. Commit only `lib/`, `test/`, `pubspec.yaml`, `pubspec.lock`, `assets/`, `android/` and the iOS files named in M6. If a `pod install` is needed, leave the resulting `Podfile.lock` diff uncommitted and report it to the chief-of-staff. Do not mix it into this work.
- Store copy and screenshots are proposals in §5, for store-compliance to apply.

---

## 1. Problem

### Apple and Google state
- Apple, version 1.0.2, 4 messages in `/Users/spatchava/agl/.dist/rejections.json` → "yourtube":
  - **4.3 Spam / 4.2.6 App Generation Services**: "duplicate content or functionality", "indistinguishable from what's already widely available or is an opportunistic variant of an existing category or popular app".
  - Then **2.1(a)**: "crashed on launch", on an iPhone 17 Pro Max with iOS 27.0.
  - And **2.3.3**: "Marketing or promotional materials that do not reflect the UI of the app are not appropriate for screenshots… splash and login screens are generally not considered to show the app in use."
  - The 4.3 text is the same message Apple sent to 26 apps in the same minute.
- Google Play: PRODUCTION_DRAFT_STAGED.
- The launch crash has **not been diagnosed** for this binary. I did not read a crash log. Since 1.0.2, commit `0c84f6a` added the real AdMob app id. `agl-manifest/docs/MANUAL_ACTIONS.md:2128` says "An iOS build that includes the AdMob SDK without a real app id crashes at launch", so that is a plausible cause. It is **not verified**.

### Why Apple sees a copy of YouTube
I read all of `lib/`: 33 files, 12,480 lines.
- **Name and mark.**
  - The name is "YourTube" in `AppConstants.appName`, `MaterialApp.title` (`main.dart`), `CFBundleDisplayName` and `CFBundleName` (Info.plist), the TV rail wordmark (`main_scaffold.dart`), the search hint 'Search YourTube' (`search_screen.dart:81,167`) and 'About YourTube'.
  - The icon (`assets/icons/app_icon.png`, viewed) is a glowing red rounded play triangle with a "Y" cut out, on black.
- **Literally YouTube's palette.** `core/theme/app_theme.dart:11-48`:
  - `brand = 0xFFFF0000` (the alias is even named `youtubeRed`);
  - `darkBg 0xFF0F0F0F`, text `F1F1F1` / `AAAAAA` / `717171`, chip `272727`.
  - The font is `GoogleFonts.roboto` (`:115-206`), fetched at runtime and not bundled.
- **Layout.** Eight tabs, in the same order as YouTube's feature set (`widgets/common/main_scaffold.dart:20-29, 91-126`): Home, Shorts, Search, For You, Trending, Saved, Explore and Settings.
- **Content.** Feeds are Dailymotion's trending and search lists (`data/services/video_api_service.dart:174-245`), uploads by anyone. The store screenshots showed Dailymotion thumbnails titled "FULL MOVIES ENGLISH SUB" and "My Online Girlfriend is a CEO". That is an aggregator of what is already everywhere.
- **Sign-in wall first.** `/login` is the initial gate (`config/routes.dart:41-46` `authRedirect`). Its buttons are "Sign in with Apple", "Continue with Google" and "Continue as guest" (`screens/auth/login_screen.dart:297,323,347`), the family shared by 15 apps. The review notes give the shared demo login `qa@americangroup.ai`. No feature needs an account: Watch Later, likes and history are stored only on the device (`presentation/providers/video_provider.dart:41-44`).
- **Play feature graphic** (`assets/images/feature_graphic.png`, viewed):
  - "YourTube — Stream. Discover. Enjoy." over stock tiles with **invented** numbers: "8.2M views", "125K watching", "LIVE", "4K".
  - None of these are in the app. This is fake data in a store asset.

### What works today
- **Dailymotion lists and search.** Keyless, real, played in Dailymotion's embed web view (`widgets/video/embed_video_player.dart`). Failures raise `VideoFetchException` and the screen shows Retry (`widgets/common/feed_error_view.dart`).
- **Watch Later, likes, hidden ("Not interested") and history.** Persisted in `shared_preferences`, with careful restore/merge logic (`video_provider.dart:340-420`). Tests cover it (`test/video_provider_test.dart`, `test/player_watch_later_test.dart`).
- **Local "For You" ranking.** A keyword-weight scorer, not machine learning (`data/services/recommendation_engine.dart:384-420`).
- **Player.** `video_player`/`chewie` for direct MP4, with ±10 s seek (`screens/player/video_player_screen.dart:381-455`). There is **no resume position**.
- **A TV layout** with a side rail (`main_scaffold.dart:149+`).
- **UMP "Privacy choices"** and in-app account deletion (`settings_screen.dart:48-51, 223`).

### What is shallow, dead or misleading
- **Shorts is always empty in release.** It reads only Pexels (`video_api_service.dart:276-298`). `docs/api-vendor-keys.json` → yourtube → `PEXELS_API_KEY` `"effective_in_release": "EMPTY"`, so the tab shows 'No shorts available' (`shorts_screen.dart:89,137`). Pixabay and the YouTube key are also EMPTY.
- **Notifications bell with no backend.** It always opens 'No new notifications' (`home_screen.dart:52-80, 116`).
- **"On-Device AI Recommendations"** (`settings_screen.dart:363,673`, `AppConstants.aiDisclosure`) is called AI. It is a weighted keyword count.
- **Trending and Explore** are both Dailymotion lists, differently filtered. There are 15 hand-picked categories in `app_constants.dart:132-148`.
- **Shared scaffold:**
  - `app_env.dart` and `supabase_config.dart` (duplicates across apps);
  - `error_reporter.dart` (sha shared by 13 apps; infrastructure, invisible, out of scope);
  - the byte-identical `LaunchScreen.storyboard` (`shasum` = `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, the same as in 37 apps);
  - the same Google-Sign-In error strings.
- **Privacy label** (`agl-manifest/store/privacy/yourtube.json`) declares EMAIL_ADDRESS, NAME and USER_ID linked to you. That body is shared with 12 other apps, including MyHealth.

### The honest product
A general "watch anything" video app cannot be distinct: YouTube, Dailymotion and Tubi already own that category. The obvious unclaimed angle for our data is **films the public is allowed to watch**: the Internet Archive's public-domain and openly licensed film collections. That covers educational and industrial films, newsreels, silent films and features, which nobody browses well on a phone.

## 2. User and product

**User:** someone who watches old films on purpose. Examples:
- a history or media-studies teacher looking for a 1950s classroom film or a 1940s newsreel to show;
- a video editor or student who needs footage whose licence they can see;
- a classic-film fan who wants to browse by era rather than by algorithm.

Their complaints:
- archival films are buried in general video apps among re-uploads of unclear origin;
- you cannot see what a film contains before committing 20 minutes to it;
- the licence is never stated.

**Core job (one, done well):** *Pick a decade, find a film from the Internet Archive's public-domain and openly licensed film collections, see what is in it, watch it, and keep your place. Every film shows its stated licence and a ready-made credit line.*

**Signature feature: the Contact Sheet.**
- Before you press play, a film's detail page shows a grid of real frames from the whole film, one every 30 seconds. Each frame is labelled with its timecode ("04:30") in a monospaced face.
- Tap a frame to start the film at that moment.
- Select a frame and press "Save moment" to keep a timecoded bookmark (frame + film + second) in your Library. Moments can be shared as text with a link and the credit line.
- The frames are the Internet Archive's own derived thumbnails (`<id>.thumbs/<id>_000030.jpg` …). The file name is the second of the frame. No key, no server, and no frame extraction on the phone.

**Competitors.** App Store listings were read on 2026-10-12 via the keyless iTunes Search/Lookup API (`itunes.apple.com/search?term=public+domain+movies`, `lookup?id=6755102519,652389989`). I did not use the apps themselves. Web search was not available in this session: the WebSearch hook said "Internet mode is not enabled".
- **Eye Yay – Public domain player** (id 6755102519, Bucket Brigade Software): "explore historic audio and video collections made available… by open online archives".
  - Features: "Smart resume", offline saving, Picture-in-Picture.
  - "Create Personal Bookmarks — mark your own moments" is behind the paid "Supporter Edition".
  - It mixes audio (radio dramas, podcasts) with video.
- **Eznetsoft OpenFlick** (id 652389989): "Full-length free Movies and Videos from many public Domain sources", categories, favourites, auto-resume.
- **Tubi** (id 886445756), **Fandango** (id 487285735), **Kanopy** (id 1205614510): free or library streaming of licensed catalogues, not public-domain archives.

The honest angle against these **listings**: neither public-domain listing mentions (a) a frame contact sheet with tap-to-start, (b) browsing by decade of production, or (c) a stated licence and credit line per film. Moments are free here; in Eye Yay they are paid. I have **not verified** whether these apps have such features without mentioning them, so treat this as "not in their listings", not "they lack it". **4.3(a) risk:** public-domain players already exist on the store, so the store copy and review notes must lead with the contact sheet, decades and licences, not with "free old movies".

## 3. Data source (keyless, curl-verified 2026-10-12)

All of these are Internet Archive endpoints. They are HTTPS, keyless, and no sibling app uses them: `grep -rl "archive\.org" --include='*.dart'` across `/Users/spatchava/agl` returned nothing. They do not overlap radiotune: video only, and no audio, radio or podcast collections.

1. **Search** with `https://archive.org/advancedsearch.php`. Verified:
   - Query: `q=collection:prelinger AND mediatype:movies AND year:[1950 TO 1959]&fl[]=identifier,title,year,licenseurl,runtime,downloads&sort[]=downloads desc&rows=5&output=json`
   - Result: HTTP 200, `numFound: 1566`.
   - First doc: `HealthYo1953`, "Health: Your Posture", year 1953, `licenseurl` `http://creativecommons.org/licenses/publicdomain/`, runtime "10:20".
2. **Collection sizes**, from three `rows=0` queries each: total / with `licenseurl:*` / with a year in 1890–2030.

   | Collection | Total | With `licenseurl:*` | With a year |
   |---|---|---|---|
   | prelinger | 10,461 | 1,914 | 4,970 |
   | feature_films | 28,529 | 9,125 | 17,832 |
   | silent_films | 3,524 | 729 | 2,999 |
   | universal_newsreels | 611 | 595 | 609 |
   | classic_cartoons | 81 | 46 | 68 |
   | classic_tv | 11,027 | 2,520 | 7,783 |
   | nasa | 13,774 | 719 | 11,579 |

   So `licenseurl:*` works as a query filter. **Not run:** a single query combining several collections with `OR`, and the distribution of licence values. My attempt was refused by the office's action judge as "unrelated to PilotEnRoute", because the session's working directory was another repo. The developer must run both before building M2 and quote the output in the commit message.
3. **Item metadata** with `https://archive.org/metadata/HealthYo1953`. Verified, HTTP 200:
   - `metadata.licenseurl`, `description`, `runtime` "10:20", `color` "B&W", `sound` "Sd", `subject` "Health and hygiene". `metadata.year` is absent, so take the year from the search doc.
   - Files include `HealthYo1953.mp4` (format "h.264", 640×480, 640.44 s) and `HealthYo1953_512kb.mp4` ("512Kb MPEG4", 320×240).
   - **22 frames** `HealthYo1953.thumbs/HealthYo1953_000001.jpg`, `_000030`, `_000060` … `_000630`, one every 30 s.
4. **Playback** of `https://archive.org/download/HealthYo1953/HealthYo1953_512kb.mp4`. Verified: 302 to `dn600309.us.archive.org`, then 200, `content-type: video/mp4`, `accept-ranges: bytes`, so `video_player` can stream and seek it.
5. **Tile image** at `https://archive.org/services/img/HealthYo1953`. Verified: 200, `image/jpeg`.

**Not verified:** what share of catalogue items have a `.thumbs/` folder. I measured one item. **Gate for M3:** the developer samples 40 identifiers from the M2 catalogue query (10 per decade shelf), fetches their metadata and records how many have ≥ 3 `.thumbs` frames. If fewer than 32 of 40 have them, stop and report to product before building M3. The honest fallback (M3 empty state) must exist either way.

**Rules:**
- Send a descriptive `User-Agent` (for example `<AppName>/1.1 (Flutter; archive film player; support@americangroup.ai)`).
- Request at most 24 search rows per page, and fetch metadata only when a detail page opens.
- Show "From the Internet Archive" with a link to `https://archive.org/details/<id>` on every detail page.
- Licence text is always "as stated on the Internet Archive item". The app never asserts that a film is public domain on its own authority.

## 4. Acceptance criteria

### MUST (what Apple has to see for this to be a real, distinct app)

**M1. A name and mark of its own (no YouTube imitation).**
- Put the visible name in one constant, `AppConstants.appName`. Use it in `MaterialApp.title`, the iOS `CFBundleDisplayName`/`CFBundleName`, the Android `@string/app_name`, the TV rail and Settings → About.
- Until the founder answers Q2, use the recommended working name **"Nitrate"**. In an App Store search for "Nitrate" (iTunes Search API, 2026-10-12) no app had that title. That check says nothing about trademark or about App Store Connect name availability (**not verified**).
- The bundle id `com.americangroupllc.yourtube` stays. It is invisible and tied to the existing records.
- No string "YourTube", "Tube" or "YouTube" remains in `lib/`, the `ios/Runner/Info.plist` names or `android/app/src/main/res/values*/strings.xml`, except one sentence in the review notes (§5).
- New icon. Do **not** use `agl-manifest/scripts/generate_app_icons.py`, a Material glyph, a gradient or a play triangle.
  - Design: a single 4:3 film frame with four sprocket holes down each side, drawn flat in brass `#C8A24A` on darkroom ink `#14130F`. Make it with an SVG or a Pillow script committed under `tool/icon/`.
  - Regenerate the iOS/Android/web icons with the existing `flutter_launcher_icons` config.
  - Delete `assets/logo/yourtube_icon.svg`, `yourtube_logo.svg`, `assets/images/app_icon_v2.png` and the old `feature_graphic.png` from the app bundle if nothing references them.
- *Acceptance:*
  - `grep -rniE "yourtube|youtube|your tube" lib ios/Runner/Info.plist android/app/src/main/res` returns nothing. Quote the output.
  - The new 1024 px icon is viewed and attached to the QA report.

**M2. Core job: decades → film → watch, from the Internet Archive.**
- Replace `VideoApiService`'s Dailymotion, Pexels and Pixabay calls with an `ArchiveFilmService` built on the §3 endpoints. Delete the Dailymotion embed web-view path (`embed_video_player.dart`), the Pexels/Pixabay/YouTube key constants, and `secrets.example.json` entries for them.
- Catalogue query: `mediatype:movies AND licenseurl:* AND collection:(prelinger OR silent_films OR universal_newsreels OR feature_films)` plus the decade's `year:[Y TO Y+9]`, sorted `downloads desc`. Cartoons are excluded pending Q4.
- Search adds the user's terms. A pure, unit-tested function builds the query string.
- **Home = the Decade Dial.**
  - A horizontal, snapping strip of decades at the top: 1900s, 1910s … 1970s. The default is the decade chosen in onboarding.
  - Below it, shelves for that decade. A shelf with zero results is hidden, never shown empty:
    - "Classroom & industrial films" (prelinger)
    - "Newsreels" (universal_newsreels)
    - "Silent films" (silent_films)
    - "Feature films" (feature_films)
  - Each card is a 4:3 frame from `services/img/<id>`, with the title in Zilla Slab, and year · runtime · "B&W"/"Colour" (only when the metadata has them) in Share Tech Mono.
- **Film detail page:**
  - title, year, runtime, description (HTML stripped), sponsor (hidden when "N/A" or empty), subject chips;
  - the licence badge (M4), the Contact Sheet (M3), and Play / Watch Later / Share.
- **Player:**
  - plays the item's `h.264` MP4, else `512Kb MPEG4`, else shows "This film has no phone-playable copy on the Internet Archive" plus a button to the archive page;
  - ±10 s seek stays;
  - **resume:** the position is saved every 5 s and on exit. Reopening offers "Resume at 12:40" or "Start over". A film watched to within 30 s of its end is marked watched and its resume entry is cleared.
- *Acceptance:*
  - a unit test parses committed fixtures captured from the real endpoints (`test/fixtures/ia_search_1950s.json`, `test/fixtures/ia_metadata_HealthYo1953.json`; the first line of a sibling `.txt` records the capture date and URL; never invented items) into film models with the right MP4 choice, year, runtime seconds, colour and licence;
  - a query-builder test covers decade bounds and escaping of user terms;
  - a widget test switches the dial from 1950s to 1920s and asserts the service was asked for `year:[1920 TO 1929]`;
  - a resume test: play to 760 s, dispose, reopen → "Resume at 12:40" → the controller seeks to 760 s.

**M3. Signature: the Contact Sheet and Moments.**
- From the item's `files`, collect `<id>.thumbs/<id>_NNNNNN.jpg`, parse `NNNNNN` as seconds, and sort.
- Show them as a 3-column grid of 4:3 frames (`https://archive.org/download/<id>/<path>`). Each frame has a timecode label (`mm:ss`, or `h:mm:ss` past an hour) in Share Tech Mono.
- **Tap a frame** to open the player at that second.
- **Select and save:** each frame has a visible bookmark button (no long-press-only action and no hidden gesture). It saves a **Moment** `{filmId, title, year, second, frameUrl, savedAt}`.
- Moments are listed in Library with their frame and timecode. Tapping one plays from that second. A Moment can be renamed with a short note, deleted (swipe plus a visible delete in edit mode) and shared (M4).
- Fewer than 3 frames → an honest empty state: "The Internet Archive has no frame previews for this film." Play still works.
- Semantics: each frame is labelled "Frame at 4 minutes 30 seconds. Double-tap to play from here."
- *Acceptance:*
  - a unit test turns the fixture's 22 `.thumbs` paths into seconds `[1, 30, 60 … 630]`;
  - a timecode formatter has golden tests (`1` → `00:01`, `630` → `10:30`, `3725` → `1:02:05`);
  - a widget test taps the `04:30` frame and asserts the player route was opened with `startAt: 270`;
  - Moments persist across a provider dispose and recreate;
  - the empty state is shown for an item with no thumbs.

**M4. Depth: Library, search and filter, licence and share, real states.**
- **Library tab:** Continue watching (resume entries, newest first), Watch Later, Moments and Watched.
  - Each section is searchable by title and has an empty state with one action. For example, Watch Later: "Films you save appear here" → "Browse the 1950s".
  - Watch Later keeps `VideoProvider`'s existing restore/merge logic, re-keyed to Internet Archive identifiers.
  - Old Dailymotion entries stored under `yt_watch_later_v1` / `yt_watch_history_v1` are dropped once on upgrade (they can no longer play). A one-time snackbar says so: "Saved Dailymotion videos were removed. This app now plays Internet Archive films."
- **Search tab:**
  - free text, plus filters for decade (multi-select), collection (the four shelves) and length (Under 15 min / 15–60 min / Over 60 min, computed from `runtime`);
  - recent searches persist (the existing engine's search history store may be reused) and can be cleared;
  - "No films match '<q>' in the 1930s. Try another decade or remove a filter."
- **Licence badge and credit line:**
  - Map `licenseurl` to a label:
    - `…/publicdomain/` → "Public domain (as stated)"
    - `…/publicdomain/mark/1.0` → "Public Domain Mark"
    - `…/publicdomain/zero/1.0` → "CC0"
    - `…/licenses/by/x.y` → "CC BY x.y", `by-sa` → "CC BY-SA x.y", and so on
    - anything else → the URL's host + path
  - Tapping the badge opens the licence URL.
  - "Copy credit" puts on the clipboard: `"<title>" (<year>)[, <sponsor>]. Internet Archive, https://archive.org/details/<id>. Licence: <label> (as stated on the item).`
- **Share** (film or Moment, via `share_plus`): title, year, `at mm:ss` for a Moment, the archive.org details link, and the credit line. Do not claim the link opens at the timecode (not verified).
- **States:**
  - Loading uses 4:3 skeleton frames.
  - Error shows "The Internet Archive didn't answer" with Retry. `VideoFetchException` is kept or renamed.
  - Offline (`connectivity_plus`) shows a banner, "You're offline. Your Library is here; films need a connection to play." Library lists work offline from stored metadata.
- *Acceptance:*
  - licence-mapping golden tests for each case above;
  - a credit-line golden test with and without a sponsor;
  - a length-filter unit test on runtime strings ("9:43", "1:12:05", missing);
  - a widget test for the offline banner with Library still listing a stored film;
  - an upgrade test proves the old Dailymotion keys are cleared once and the snackbar is shown once.

**M5. Remove the template tells and dead screens.**
- **Delete the sign-in wall and accounts entirely**, subject to founder Q3:
  - files: `screens/auth/login_screen.dart`, `data/services/auth_service.dart`, `data/services/supabase_config.dart`, the `authRedirect` gate in `routes.dart`;
  - the Supabase init and `AppEnv.validate` Supabase checks in `main.dart`, and `app_env.dart` if nothing else needs it;
  - the `supabase_flutter`, `google_sign_in`, `sign_in_with_apple` and `crypto` dependencies;
  - Settings "Sign Out" / "Delete Account" (no account exists, so there is nothing to delete);
  - the app opens straight into onboarding (first run) or Home.
- **Delete:**
  - Shorts (no key in release);
  - Trending, Explore/Categories (Dailymotion);
  - For You and every "AI" wording (`AppConstants.aiDisclosure`, the settings tile 'On-Device AI Recommendations', `for_you_screen.dart:309`);
  - the notifications bell;
  - the 'Watch. Share. Discover.' tagline;
  - the house-ad-free but Dailymotion-specific 'Report' email flow (no third-party uploads remain).

  `recommendation_engine.dart` may stay only if it powers a visible, honestly labelled "Because you watched <title>" shelf (SHOULD S2). Otherwise delete it.
- **Navigation:**
  - three tabs, **Films** (Decade Dial), **Search** and **Library**; Settings is reached from a gear in Library's app bar;
  - on iOS use `CupertinoTabBar` with `CupertinoIcons` (`film`, `search`, `bookmark`); on Android a `NavigationBar`;
  - the TV rail gets the same three destinations.
- **Ads:** the existing `AdBannerWidget` may stay on Home below the first shelf and on the detail page below the credit line. Never put it over the video or the contact sheet. Keep the consent flow and 'Privacy choices'.
- Tests for deleted features (`auth_session_test.dart`, the auth parts of `navigation_test.dart`, Dailymotion/Pexels cases in `video_api_service_test.dart`) are removed **in the same commit as the code they test**. The commit message lists every removed test, and each removed suite is replaced by a test of the new behaviour (for example, a "no /login route exists; first run opens onboarding" test). Never skip or delete a test that still has code behind it.
- *Acceptance:*
  - `grep -rnE "Sign in with Apple|Continue with Google|Continue as guest|Supabase|dailymotion|pexels|pixabay|in this build|coming soon|AI " lib` returns nothing. Quote the output.
  - `pubspec.yaml` no longer lists the four auth and Supabase dependencies.

**M6. Own identity: colour, type, shape, splash and onboarding.**
- **Palette, "darkroom & brass".** Seed `ColorScheme.fromSeed(seedColor: Color(0xFFC8A24A))`, then override:
  - dark: background/surface `#14130F` / `#1E1C17`, onSurface `#EDE6D6`, primary brass `#C8A24A`, secondary nitrate teal `#5E7C78`;
  - light: paper `#F3EBDD`, ink `#1E1C17`, primary `#8A6D24`;
  - default to dark.

  None of these hexes, nor any Tailwind default or YouTube hex (`FF0000`, `0F0F0F`, `F1F1F1`, `AAAAAA`, `717171`, `272727`), may remain in `lib/`. I searched the whole `/Users/spatchava/agl` tree for `0xFFC8A24A|0xFF1B1A17|0xFFE8DCC4|0xFFD9A441|0xFF14130F`: no app uses them today.
- **Typography, bundled under `assets/fonts/` with their OFL licence files, never fetched at runtime:**
  - **Zilla Slab** (400/600) for titles and the decade dial;
  - **Arsenal** (400/700; Latin, Cyrillic, Vietnamese) for body text;
  - **Share Tech Mono** for timecodes, years and runtimes;
  - delete `google_fonts` if nothing else uses it.

  Changed 2026-10-14 (decision log #39): the first pairing, Fraunces with IBM Plex Sans and Mono, was not this app's alone. AGCleaner keeps IBM Plex, and AGrammarly and BuddyPlay bundle Fraunces. The `family:` entries of every pubspec.yaml under `/Users/spatchava/agl` name none of Zilla Slab, Arsenal or Share Tech Mono. All three are static TTFs taken unmodified from github.com/google/fonts (`ofl/zillaslab`, `ofl/arsenal`, `ofl/sharetechmono`), each with its OFL.txt, and they are registered with `LicenseRegistry`.
- **Shape language:**
  - 4:3 frames with a 2 px corner radius (the portfolio's common radius is 12);
  - a thin sprocket-hole rule (a row of small rounded rectangles drawn with `CustomPainter`) as the section divider on Home and the detail page;
  - no `BorderRadius.circular(12)` in new code.
- **Splash:**
  - replace `ios/Runner/Base.lproj/LaunchScreen.storyboard` with one whose background is `#14130F` and whose image is the new mark at 30 % width;
  - update `flutter_native_splash` (`color: "#14130F"`, the new `splash_logo.png`) and Android `launch_background.xml` to match.

  These iOS files do not currently carry anyone else's edits. Check `git status` first and stop if they do.
- **Onboarding.** One screen, first launch only, stored flag:
  - headline "Films the public owns.";
  - two sentences: "Every film here comes from the Internet Archive's public-domain and openly licensed collections. Pick a decade to start.";
  - a row of decade chips;
  - the button reads "Open the 1950s" (it follows the chip);
  - no "Get started", "Welcome" or sign-in.
- **Settings copy is specific to this app:**
  - "Default decade";
  - "Clear watch history";
  - "Clear search history";
  - "Clear frame cache" (image cache);
  - Language (agl_i18n, infrastructure);
  - Privacy choices;
  - About: "Films and frames come from the Internet Archive (archive.org). Licences are shown as each item states them.";
  - Privacy policy / Terms;
  - Send feedback.
- *Acceptance:*
  - a theme test asserts the seed and the three font families;
  - `shasum ios/Runner/Base.lproj/LaunchScreen.storyboard` ≠ `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`;
  - a widget test shows onboarding exactly once and lands on the chosen decade;
  - screenshots of onboarding, Home, detail with contact sheet, player and Library (iPhone simulator, dark) are attached to the QA report, together with the screenshot of the new launch screen.

**M7. Honest and launch-proven.**
- Real data only:
  - no bundled sample films;
  - no view/like counts, "LIVE" or "4K" badges;
  - the IA `downloads` field is used only for sorting and never displayed as "views";
  - no remote switches, no reviewer, region or date detection, no hidden gestures.
- **Launch proof.** A release-mode iOS simulator build (`flutter build ios --simulator` plus run, or `flutter run --release` where supported) launches to onboarding on a fresh install and plays HealthYo1953 for ≥ 10 s from the 04:30 frame. Attach screenshots. Also build the Android release bundle.
- A physical-device run is required by Apple 2.1 but cannot be done by the office. Record it as a founder/manual item.
- `flutter analyze` must be clean ("No issues found!"), and `flutter test` must pass with the count quoted. The commit is path-limited (never `fastlane/`, `ios/Podfile.lock` or `ios/Runner.xcodeproj/project.pbxproj`; see the note at the top) and pushed to `master`.

### SHOULD (after the MUSTs pass)
- **S1. Downloads for offline viewing** of the 512 kb MP4 into app support, with size shown before download and a storage screen. Eye Yay has this, so it is table stakes rather than signature.
- **S2. "Because you watched <title>"** shelf, from shared `subject` values of watched films, labelled exactly that way (no "AI").
- **S3. Decade × collection counts** on the dial ("1950s · 1,566 classroom films"), using `numFound` from `rows=0` queries.
- **S4. Picture-in-Picture** on iOS.

## 5. Store impact (proposals; store-compliance applies them after the build and the founder's answers)

Do not edit `store/apps/yourtube.json`, `fastlane/` or `docs/` from this workstream.

**Name and copy (en), assuming "Nitrate" (Q2):**
- Name: "Nitrate: Public-Domain Films". Play title: "Nitrate – Public-Domain Films".
- Subtitle: "Archive films by decade".
- Short description (Play): "Classroom films, newsreels and silent features from the Internet Archive, by decade."
- Description (draft; it opens with the job, not the app name, and has no ALL-CAPS headings):
  > Browse a century of films the public is allowed to watch. Pick a decade, from the 1900s to the 1970s, and see what the Internet Archive holds from it: classroom and industrial films, Universal newsreels, silent films and features.
  >
  > Before you press play, every film opens on a contact sheet: a real frame from every 30 seconds of the film, with its timecode. Tap a frame to start right there, or save it as a Moment to come back to.
  >
  > Each film shows its licence as the archive states it, and one tap copies a credit line with the source link, for a lesson, an essay or an edit.
  >
  > Your place in every film is remembered. Watch Later, Moments and your history stay on this phone. There is no account to create.
  >
  > Films and frames come from the Internet Archive (archive.org). Nitrate is not affiliated with the Internet Archive.
- Keywords: `archive film,public domain,newsreel,silent film,classroom film,prelinger,old movies,1950s,contact sheet,film history`
- Category: keep ENTERTAINMENT. Consider EDUCATION as secondary.
- Ads sentence: keep only if AdMob units are live in that build, and use this app's own wording, not the 32-app boilerplate.

**Screenshots (retake all; iPhone 6.9", iPad 13", Play phone/tablet; dark; no login or splash; no third-party Dailymotion content):**
1. Home on the 1950s with the classroom-films and newsreels shelves.
2. A film detail page with the contact sheet.
3. The player started from a frame, timecode visible.
4. Library with Continue watching and Moments.
5. Search with decade and length filters applied.
6. The licence badge and "Copy credit" confirmation.

**Play feature graphic:** replace `fastlane/metadata/android/en-US/images/featureGraphic.png` and the in-repo `assets/images/feature_graphic.png`. The current one shows invented "8.2M views / 125K watching / LIVE / 4K". The new one shows the brass film-frame mark, the name, and three real contact-sheet frames from a public-domain film (for example HealthYo1953), with no counts.

**Review notes:** write them per app. Do not use the shared "2. DEVICES…" skeleton, and do not paste the subtitle as the audience. Draft:
> Nitrate plays films from the Internet Archive's public-domain and openly licensed collections (Prelinger, Universal Newsreels, silent films, feature films), organised by decade. No account exists and nothing is behind a sign-in. The app opens on a one-screen decade picker, then Home.
>
> To see the main feature: open any film, and its detail page shows the contact sheet (frames every 30 s, from the Internet Archive's own thumbnails). Tap a frame to play from that point. Tap the bookmark on a frame to save a Moment, which then appears in Library.
>
> Who it is for: teachers and students of history and media, video editors who need footage with a stated licence, and classic-film viewers who browse by era.
>
> External services: Internet Archive (archive.org) search, metadata, thumbnails and MP4 files, keyless. Firebase Crashlytics/Analytics. Google Mobile Ads with Google's consent form.
>
> This version replaces the previous general video browser ("YourTube"), which used Dailymotion. That app and its sign-in were removed entirely.

- Testing statement: only what was actually done (simulator runs and the physical device, if the founder does one). Never "a build that cannot start never ships".
- `demo_account_required: false`. Remove `demo_account_name`.
- Contact name: the founder's choice, not "App Reviewer" (Q6).

**Privacy label** (`store/privacy/yourtube.json`): remove EMAIL_ADDRESS, NAME and USER_ID, because there are no accounts after M5. Keep only what the remaining SDKs collect: crash data and device id for Crashlytics/Analytics, and advertising data and device id for AdMob. store-compliance must confirm against the SDK list. The result will no longer match MyHealth's label.

**Remove `_blocker`** requirements that no longer apply (`PEXELS_API_KEY`, Supabase). The trademark item is replaced by Q2.

## 6. Out of scope
- Audio, radio, podcasts or old-time radio collections (radiotune's job), and `classic_tv` and `nasa` collections at launch.
- Uploads, comments, accounts, sync across devices.
- Any server or Supabase table: everything is on the device.
- Redesigning the TV layout beyond the theme, fonts and three-destination rail.
- Shared infrastructure files (`error_reporter.dart`, agl_* packages, the `main()` bootstrap order).
- Diagnosing the 1.0.2 launch crash from Apple's log (M7 proves the new build launches; the old log is not in the repo).
- Replying to Apple, submitting, editing store JSON, fastlane or docs.

## 7. Founder questions
- **Q1 (pivot):** approve turning yourtube from a general Dailymotion video browser into an Internet Archive public-domain film player? This is effectively a new product on the existing records.
- **Q2 (name):** approve a rename away from "YourTube" (4.3(b) imitation and possible 5.2 trademark risk)? The recommendation is "Nitrate", with "Kinescope" as an alternative. Neither appeared as an app title in an iTunes search on 2026-10-12; trademark and App Store Connect availability are **not verified**, so store-compliance must check them.
- **Q3 (accounts):** approve removing Supabase sign-in and accounts entirely? Nothing in the app needs an account. Whether any real Play accounts exist (the Play status is a staged production draft) is **not verified**.
- **Q4 (content/age rating):** exclude `classic_cartoons` at launch (some 1930s–40s cartoons carry racial stereotypes), and which age rating to declare for archival films that contain period violence and attitudes? The recommendation is to exclude cartoons and declare 12+.
- **Q5 (privacy policy, Charter §6):** update the yourtube policy text for no accounts and the Internet Archive as the content source.
- **Q6 (review contact):** whose name replaces "App Reviewer" in App Review Information, and will someone run the build on a physical iPhone and record it (Apple 2.1)?
