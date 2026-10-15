# Spec: Radio Tune, live radio for people learning a language by ear

- **Repo:** `/Users/spatchava/agl/radiotune` (Flutter app at the repo root, `lib/`)
- **base_sha:** `3800548924cf668f2483ce448a66017b5b9f3cd0` (`git -C /Users/spatchava/agl/radiotune rev-parse HEAD`, 2026-10-12)
- **Branch:** `master` (`git branch --show-current`)
- **Author:** product-manager, AI Office. Written 2026-10-12. This is a spec only. I changed no app code, store file, fastlane file or docs file.
- **Store state:** Apple rejected version 2.0.1 under 4.3 / 4.2.6 on 2026-10-05T21:25:48Z. It was the shared message, with no 2.1 thread before it (`/Users/spatchava/agl/.dist/rejections.json` key `radiotune`, `threads: 1`). `docs/asc-build-state.json` lists build `202610081934` as `REJECTED`. On Google Play the production track has versionCode 4 as a **draft** and internal testing has versionCode 6 (`docs/play-production-blockers.json`, state `PRODUCTION_DRAFT_STAGED`). No build of this app has ever been public on either store.
- **Baseline on base_sha:** I ran this in a throwaway copy (`rsync` to `/tmp/rt_baseline/radiotune`). That kept golden-failure PNGs, which are tracked files, from being written into the real repo. `flutter analyze` → "No issues found! (ran in 22.9s)". `flutter test` → "+213: All tests passed!" (2026-10-12).
- **Other people's uncommitted changes. Do not touch these files** (`git status --short`, 25 entries): all of `fastlane/**` (descriptions, review notes, every screenshot, and the new `05.png` files), `ios/Podfile.lock` and `ios/Runner.xcodeproj/project.pbxproj`. Three consequences:
  - Every change in this spec has to avoid `project.pbxproj`. Fonts are Flutter assets. The launch colour goes in an asset-catalog colour set inside `Assets.xcassets`, which is a folder reference and needs no pbxproj edit. Do not add new Xcode build files.
  - Removing `supabase_flutter` (M6) changes the pods. **Do not commit `ios/Podfile.lock`.** Leave it to the person who owns the uncommitted lock, and tell the chief-of-staff that it needs regenerating after their commit. (Side note for the chief-of-staff: their uncommitted lock diff already removes `Google-Mobile-Ads-SDK` and `google_mobile_ads`. `agl_ads` needs both. I did not verify why the diff removes them.)
  - Store copy, screenshots and review notes are proposals in section 6. store-compliance applies them later.

---

## 1. Problem

### What the app is today (read from `lib/` at base_sha)

Radio Tune is a competent general internet-radio and podcast player. Sign-in was already removed (commit `2efe4fb`). Most features work. What is wrong is that **nothing in it is distinct**: it is a Radio Browser client with Apple's podcast charts, in a category where Apple can point to dozens of established apps.

| Screen | What works (evidence) | What is shallow, dead or a tell |
|---|---|---|
| **Shell** (`screens/main_shell.dart`) | A custom 4-tab bar (Listen · Browse · Live · Library). The mini player is docked. First run opens the genre picker (`:76-84`). Alarm re-arm and podcast checkpoints run on lifecycle events (`:57-71`). | `const AglAdBanner()` sits in the shell Column above the mini player and bar (`:113`). That is the portfolio's shared-shell tell. |
| **Listen** (`screens/listen_screen.dart`) | A hero band with live directory stats (`RadioApiService.getStats`; the screenshot shows 54,684 stations and 241 countries). Shelves: Continue listening, Trending (topclick), Made for you (`DiscoveryService.forYou`), Near you (location asked in context), Top podcasts. Every shelf has its own error and retry. | The hero copy is generic: "NOW LIVE / Your world of sound / Radio · Podcasts · Music", with a "Free · no account" stat (`widgets/hero_band.dart:62,78`). "Made for you" falls back to global trending for a new install (`discovery_service.dart:20-21`). `getNearby` sends full-precision GPS coordinates to radio-browser (`radio_api_service.dart:166`), although the cache key rounds them to 2 decimals. |
| **Browse** (`screens/browse_screen.dart`) | Debounced search over stations and podcasts, recent searches stored on the device, genres and countries with real counts, podcast categories. | Six "Moods" chips, and **Focus and Sleep both map to the same tag `ambient`** (`:54-59`). The search results have a "Start "X" radio / A rolling mix built from this search" banner (`:290-299`). It is not a mix: it lists stations whose *name or tag* matches the text (`discovery_service.dart:44-70`). A station named after an artist is not a station that plays the artist. That is an overclaim. |
| **Live** (`screens/live_screen.dart`) | Lists `getTrending(limit: 40)`. | **It duplicates Listen's "Trending now"** (the same endpoint, `:43`). The file header admits the concert and festival lists were removed (`:5-7`). This tab has no job left. |
| **Library** (`screens/library_screen.dart`) | Favourites, playlists (create, rename, reorder, delete), followed shows, saved episodes, history. All on the device. | Fine. |
| **Now Playing** (`screens/now_playing_screen.dart`) | Live/episode modes, ICY track line (`:261`), retry banner, sleep timer, Queue, Car mode, Similar, Share. | The pulsing coral disc is the "dark interface with a live audio visualiser" the listing advertises. It does no job. |
| **Car mode** (`screens/car_mode_screen.dart`) | Four oversized labelled controls. | Fine. It must stay (radiotune owns car mode). |
| **Podcasts** (`podcast_detail_screen.dart`, `podcast_category_screen.dart`, `services/podcast_api_service.dart`) | Real RSS episodes, resume, save, follow. Apple charts by category, with storefront `country = 'us'` hard-coded by default (`:76`). | The feed parser ignores the channel `<language>`. |
| **Settings** (`screens/settings_screen.dart`) | Favourite genres, Resume on launch, Car mode, Wake to radio (with honest limits: "while Radio Tune is open or playing in the background"), clear history, clear favourites, About, Privacy choices (UMP, only where required). | A legacy **Account** section with "Delete account" for a session "from an earlier version" (`:126-155`). No public build ever offered sign-in (see Store state above), so this serves nobody. |
| **Alarm** (`services/alarm_service.dart`) | A Dart timer that plays the chosen station and rolls over daily. Honest header. | It cannot wake a terminated app. The copy already says so. |

**Infrastructure left over from the template** (no UI, but it ships in the binary):
- `lib/services/supabase_config.dart` holds the shared project URL, anon key, Google OAuth client id and Apple service id. `lib/services/auth_service.dart` still reads a `radiotune_local_demo_email` "local demo session" key (`:30,56-57`). `main.dart:85-104` initialises Supabase at every launch.
- `lib/app_env.dart` and `lib/services/error_reporter.dart` are **used only by tests**. A grep of `lib/` outside those files finds no reference. `env/*.json` holds only `{"APP_ENV": "prod"}`, and no CI or fastlane file references `env/`.
- `pubspec.yaml` bundles `assets/logo/`, which contains `waveworld_icon.svg`, `waveworld_logo.svg` and `wordmark.png`. Nothing in `lib/` references them, so an old brand ("WaveWorld") ships inside the binary.
- `models/radio_station.dart` still carries `ContentType { radio, podcast, music, liveEvent, concert }` and the fields `eventDate`, `eventVenue`, `eventCity`, `concertArtist` and `concertTicketUrl` (`:4,26-33`). `pubspec.yaml` `description` reads "Radio, Podcasts, Music, Live Events & Concert Updates", and the `main.dart` header says the same. Neither the events nor the concerts exist.
- `test/failures/` holds 44 golden-failure PNGs committed to git (`git ls-files test/failures | wc -l` → 44).
- `theme/app_theme.dart` keeps "legacy aliases" (`cyan`, `pink`, `concertGradient`, `eventsGradient` and others), plus the Tailwind hexes `0xFF4ADE80` (green-400) and `0xFF6B7280` (gray-500).

### Why Apple called it a template (this app's tells)

1. **4.3(b), category clone.** The subtitle "50,000+ stations worldwide" and the description describe exactly what these apps already sell (iTunes Search API, 2026-10-12): TuneIn ("100,000 live AM/FM radio stations", 1,121,561 ratings), myTuner ("More than 50,000 radio stations… Recently played songs on the radio", 244,278), Simple Radio ("90,000+", 531,425), radio.net ("More than 60,000", 69,959), Radio Garden (globe, 2,302), and RadioApp ("Automatic Shazam Integration… Live Rewind", 68,923). Radio Tune adds nothing they lack.
2. **Shared scaffolding:** the byte-identical `LaunchScreen.storyboard` (shasum `3f6a9b27d8…`, white background, 540×540 `LaunchImage`), `AglAdBanner` in the shell, `themeMode: ThemeMode.dark` (`main.dart:134`), no typeface of its own, Tailwind hexes, and the Supabase config / auth / app_env / error_reporter files that belong to the 15-app sign-in family.
3. **Leftovers that read as generated:** dead concert and event fields, the WaveWorld assets, the "Ratio" class prefix (`RatioColors`, `RatioWordmark`; the HEAD screenshot `iphone69-01.png` still shows the wordmark "Ratio Tune"), and an artist-radio overclaim.
4. **Store packaging:** "——" section headings; the shared ads paragraph ("Google may use device identifiers…"); review notes on the shared "2. DEVICES…" skeleton with "Automated tests… simulators" and "Intended audience: Anyone who listens to live radio"; and a notes line that contradicts itself ("The app contains no advertising SDK and shows no ads." directly above the AdMob line, in `store/apps/radiotune.json` `review_information.notes`). The privacy label is the shared 13-app label and declares EMAIL_ADDRESS, NAME and USER_ID "linked to you" (`store/privacy/radiotune.json`), which the app does not collect.

---

## 2. User

**Primary user:** an adult who is **learning a second language by listening** (comprehensible-input style learners, heritage speakers rebuilding a language, people preparing to move abroad). They want **real native speech every day**, such as news, talk and phone-ins from Spanish, French, German, Japanese or Brazilian stations, and they want that time **to count**: how many minutes today, how many hours this month, and in which language. Today they piece this together from a generic radio app (where language is at best a filter) and a spreadsheet or a habit tracker.

**Secondary user (served, not targeted):** someone abroad listening to home radio, or anyone who just wants world radio. A "Just listening" choice in onboarding keeps the whole station directory, podcasts, favourites, car mode, sleep timer and alarm working with no target language. The log still records which languages they heard.

**Not the user:** people who want translation, flashcards or phrase practice (Verba owns that: `Verba/README.md` "Translate… Practice — SM-2 flashcards, phrasebook"), video (yourtube), music creation (VirtuBand), or scanner and air-traffic audio (see Out of scope).

---

## 3. Product

### Core job

**"Put live, native speech in my target language in my ears in one tap, and keep honest count of it."** Open the app → Today shows talk and news stations broadcasting now in your language → tap one → it plays, and the mini player says "Counting · Spanish" → the minutes land in your log. Everything a radio listener expects stays and keeps working: background playback, lock-screen controls, sleep timer, wake-to-radio, car mode, favourites, playlists and podcasts.

### Signature feature: **Immersion Log**, live radio that counts toward your language

Radio Tune measures how long you **actually listened**, per language, split into **talk/news vs music**:
- **What counts.** Time is counted on the device from player events: only while audio is really playing (`playing == true` and `processingState == ready`). Connecting, buffering and pause are not counted.
- **Which language.** A **station's** language comes from Radio Browser's `languagecodes` (ISO 639-1), with its `language` name list as the fallback. A **podcast episode's** language comes from the feed's `<language>` tag. If a feed has no tag, the listener sets the show's language once.
- **Talk/news vs music.** A station is "talk & news" when its Radio Browser tags match a spoken-word list (news, talk, information, public, culture/cultural, spoken, and the local words noticias, nachrichten, actualit*, notizie, documentar*, educa*). Otherwise it is music. The UI says this classification comes from the station's tags.
- **What you see.** A daily goal ring, a streak, a 7-day bar chart, hours per language (all time and this month), and a searchable session list you can export as CSV.

**Why it is distinct (evidence, with honest limits).** Web search was blocked in this session ("Internet mode is not enabled"), so I checked App Store listings with the keyless iTunes Search API on 2026-10-12 at 22:30–22:44Z:
- **Radio apps.** The descriptions of TuneIn, myTuner, radio.net, Simple Radio, RadioApp and Radio Garden contain **0** matches for `goal|streak|minutes listened|listening time` and **0** for "learn" in a learner sense (one TuneIn hit is unrelated). Receiver ("Radio - Receiver", 1,113 ratings) offers search "by… language". That is a filter, not tracking.
- **Language apps.** **PolyPod** (5 ratings) does "a podcast player with automatic listening-time tracking… daily goal… streaks". That covers podcasts only, and its description does not mention live radio. **Dreaming** (230) and **Umi** (2,667) are built around video. **RadioLingo** (2,243) teaches through "podcasts that teach you". **All World Radios** (17) only *mentions* using Spanish stations to learn and has no tracking.
- **Result:** in the listings I checked, **no app combines live radio by language with listening-time tracking.** I did not install or test these apps, so **the claim that they lack it is not verified beyond their store descriptions.**

**Data supports it (curl, 2026-10-12 22:30Z, `de1/de2.api.radio-browser.info`):**
- **Languages:** `/json/languages?order=stationcount&reverse=true` returns real counts (english 12,167; spanish 5,277; german 4,378; french 3,138; chinese 2,219; …).
- **Spoken stations per language:** `stations/search?language=<name>&languageExact=true&hidebroken=true&order=clickcount&reverse=true&limit=300`, filtered client-side with the spoken-tag list, gives: spanish 80/300 (Cadena SER, esRadio, RNE Radio 5), french 86/300 (RMC, Europe 1, France Culture), german 63, italian 65, portuguese 62, chinese 88, arabic 59, russian 49, english 66. Coverage is **thin** for japanese (10 of 132), korean (15 of 102) and hindi (19 of 300). The app must say so (M7).
- **`languagecodes`** is filled in for 5,285 of 5,336 Spanish stations.
- **A query pitfall:** `languageExact=spanish` is **not** a valid filter. That request returned French, German and English stations. The flag is a boolean: `language=spanish&languageExact=true`.

---

## 4. Acceptance criteria

### MUST (what Apple has to see for a real, distinct app)

**M1. Core job end to end on a fresh install. Every visible control does something real.**
- **Tabs become Today · Dial · Log · Library.** Remove the **Live tab** (`live_screen.dart`), which duplicates Trending.
  - **Today** replaces Listen.
  - **Dial** is today's Browse (search, genres, countries, podcast categories) plus a new **Languages** section from `/json/languages` with real station counts.
  - **Log** is M3.
  - **Library** is unchanged.
  - Settings is the gear on Today and Library.
- **Today, with a target language set:**
  - an **Immersion header** (M2 ring, streak, language switcher if the listener chose up to 3 languages);
  - **"Talk & news in Spanish, on air now"**, a list (not a rail) from the exact-language query above. Spoken stations come first, interleaved across the spoken tags as `DiscoveryService._interleave` does, then de-duplicated;
  - **"Music in Spanish"**, a rail;
  - **"Podcasts in Spanish"**, from the Apple chart of a storefront mapped from the language (es→`es`,`mx`; fr→`fr`; de→`de`; it→`it`; pt→`br`,`pt`; ja→`jp`; ko→`kr`; zh→`tw`,`cn`; ru→`ru`; ar→`sa`; en→`us`,`gb`). If no storefront is mapped, the shelf is omitted. Charts for es, mx, fr, jp, br, kr, cn, tw, de, it, ru and sa all answered with entries on 2026-10-12. The `in` chart is mostly English, so Hindi gets no podcast shelf unless the feed `<language>` is `hi`;
  - **Continue listening**.
- **Today in "Just listening" mode:** the ring shows minutes today with no goal, then the existing Trending, Near you, Continue listening and Top podcasts shelves.
- **Remove the artist-radio overclaim.** Delete the "Start "X" radio / A rolling mix built from this search" banner and the empty-state button (`browse_screen.dart:220-231,268-310`) and `ArtistRadioScreen.artist`. **Keep "Similar stations"** (tag-based, honest), titled "Stations like {name}", plus its station-sheet entry.
- **Remove the Moods chips** (two of them map to the same tag).
- Sleep timer, wake-to-radio, car mode, queue, share, favourites, playlists, podcasts follow/save/resume and background playback keep working (radiotune owns them).
- **Test:** a widget test with faked `RadioApiService`, `PodcastApiService` and audio. Fresh prefs → onboarding (M4) picks Spanish + 20 min → Today shows the spoken list from a fixture recorded from the real Radio Browser response → tap the first station → the mini player shows "Counting · Spanish". A test asserts the tab bar has exactly the four labels and no "Live".

**M2. Signature: Immersion Log tracking.**
- **Model.** `lib/models/listening_session.dart` has: `id`, `kind` (`live` | `episode`), `sourceId` (station uuid or episode id), `title` (station name or show title), `languageCodes` (List<String>, ISO 639-1), `spoken` (`true` | `false` | `null` = unknown), `start`, `end`, `seconds`. JSON is hand-written.
- **Service.** `lib/services/immersion_service.dart` (a `ChangeNotifier` singleton like the existing services). It listens to `AudioPlayerService` (`playingStream`, `processingStateStream`, `nowPlayingStream`) and accrues **wall-clock** seconds between "audible" and "not audible" transitions.
  - It does not use periodic timers for counting. Checkpoints happen on every transition, every 30 s while audible, and on `AppLifecycleState.paused`, which is already called in `main_shell.dart:63-65`. That keeps background playback correct on iOS.
  - Sessions shorter than 30 s are dropped, so scanning through stations is not counted.
  - A session that crosses local midnight is split into two days.
  - A station change or an episode change closes the session.
- **Language resolution:**
  - **Stations:** `languagecodes`. If that is empty, the `language` names are mapped through the `/json/languages` name→iso list, cached for a day, plus explicit aliases verified in the data: "castellano", "español" → es; "brazilian portuguese" → pt; "american english" → en.
  - **Episodes:** the feed's channel `<language>` (add it to `Podcast`/`PodcastEpisode` parsing in `podcast_api_service.dart` and `models/podcast.dart`; normalise `es-ES` → `es`). If that is missing, use a **per-show language the listener set**, stored as prefs `radiotune_show_language_v1`. Otherwise the language is unknown.
  - Curl evidence: the Acast and Megaphone feeds carry `<language>fr</language>` and `<language>ja</language>`. The COPE feed showed no `<language>` in its first 6 KB, so the fallback is needed.
  - Multi-language stations count toward every target language they list, and the session row shows all of them.
- **Spoken classifier:** a pure function `isSpoken(tags)` in `lib/services/spoken_classifier.dart` using the list in section 3. It returns `null` when the tags are empty.
- **Persistence:** SharedPreferences.
  - `radiotune_sessions_v1`: the last 1,000 sessions.
  - `radiotune_daily_v1`: per-day, per-language totals `{date: {lang: {spoken, music, unknown}}}`, kept forever, so the totals survive trimming of the session list.
  - Goal and target languages live in `UserPrefsService`.
- **Streak:** consecutive local days on which the goal was met for any target language. With no goal, a day needs ≥ 1 counted minute. Today does not break the streak until it ends.
- **Transparency chip** in the mini player and Now Playing:
  - "Counting · Spanish" when the audio is in a target language;
  - "Not counted · station is in English";
  - "Language unknown · Set language" for an episode with no tag, which opens the show-language picker;
  - in Just-listening mode, "Logging · English".
- **Test (unit, fake clock and fake streams):**
  - counts only while playing and ready, not while buffering or paused;
  - sessions under 30 s are dropped;
  - midnight split;
  - station switch closes the session;
  - a lifecycle checkpoint persists a partial session;
  - language resolution (languagecodes; name fallback; the three aliases; `es-ES` → `es`; show override; unknown);
  - `isSpoken` matrix from real tag strings recorded in the probe ("cultural news,live,news,news talk,spanish,sports news" → true; "enka,japan,japanese,jpop,kayokyoku,talk radio" → true; "news,pop,rock" → true; "pop,dance" → false; "" → null);
  - streak edges (goal met, missed, today in progress).

**M3. Log tab with real depth.**
- **Header:** today's ring (minutes vs goal), streak, **7-day bar chart** stacked spoken/music/unknown (drawn with `CustomPainter`, no chart package), **hours per language**: this month and all time.
- **Session list:** grouped by day, each row showing station/show, languages, minutes and a talk/music badge.
  - **Search** by station or show.
  - **Filter** by language, kind (live/episode) and talk vs music.
  - Swipe to delete one session, with undo. The daily totals are adjusted when a session is deleted.
- **Export:** "Export CSV" shares a file through `share_plus`, which is already a dependency. Columns: `date,start,end,minutes,languages,kind,title,spoken`, RFC 4180 quoting. "Copy summary" puts a plain-text month summary on the clipboard ("October: Spanish 14 h 20 min (talk 11 h 5 min)…").
- **Settings → Data** gains "Clear immersion log", with confirmation.
- **States:**
  - Empty: "Nothing counted yet. Play a station in Spanish and the minutes appear here."
  - Offline banner on Today and Dial: "You're offline. Your log, favourites and playlists are here; stations need a connection." The Log works fully offline.
  - Existing per-shelf `ErrorState` with Retry stays.
- **Test:** CSV export (quoting of commas and quotes in station names, header row), filter and search logic, delete-with-undo adjusting totals, the empty-state widget, and a golden of the Log header with fixture sessions.

**M4. Onboarding and settings copy of its own.**
- **First run** replaces the genre picker (`GenrePickerScreen(onboarding: true)`) with three skippable steps:
  1. **"Which language are you tuning into?"** A searchable list from `/json/languages` with live station counts ("Spanish · 5,277 stations"), up to 3 choices, plus **"Just listening, no target language"**. If the request fails, show a Retry error, never a hard-coded list.
  2. **"Daily listening goal"**: 10 / 20 / 30 / 45 / 60 min, or "No goal".
  3. **"Count music too?"** Yes counts all target-language audio toward the goal. No counts talk & news only, but music still appears in the log.
- No account, no permissions asked. Location stays an in-context card on Today in Just-listening mode only.
- **Settings sections:** Languages & goal (edit everything from onboarding), Playback (Resume on launch, Car mode), Wake to radio, Data (clear history, favourites, log), About ("Stations: Radio Browser (radio-browser.info), a community directory. Podcasts: Apple Podcasts directory and publishers' feeds."), Privacy choices (only where UMP requires it, as now). "Favorite genres" moves into Languages & goal as an optional "Music I like" row.
- **Remove the Account section** (M6).
- **Test:** an onboarding widget test (choose 2 languages + goal; Skip → Just listening), and prefs round-trip.

**M5. Own identity: the "paper dial" look (named concretely).**
- **Palette** (replaces coral on navy). Follow the system light/dark setting: remove `themeMode: ThemeMode.dark` and build `AppTheme.light` and `AppTheme.dark`.
  - **Day:** paper `#F2EDE4` (background), card `#FBF8F2`, ink `#1C1B22` (text), **dial blue `#1F4E8C`** (primary, play button, selected tab), **needle amber `#E39A2E`** (immersion ring, ON AIR, streak; fill only, with ink glyphs on it), muted `#706B62`, error `#B23A2B`.
  - **Night:** `#121417` (background), card `#1B1E22`, text `#EFEAE0`, primary `#7FA7E0`, amber `#F0B254`, muted `#9A958C`.
  - **Contrast** (computed, WCAG): ink on paper 14.65; dial blue on paper 7.13; paper on dial blue 7.84; muted on paper 4.54; ink on amber 7.26; error on paper 5.10; night text 15.39; night primary 7.47; night muted 6.20; ink on night amber 9.84. All ≥ 4.5.
  - **Uniqueness:** grep of every `*/lib`, `*/mobile/*/lib` and `agl-manifest/packages/*/lib` tree, and of `specs/*.md`, found **0** uses of `F2EDE4`, `FBF8F2`, `1C1B22`, `1F4E8C`, `E39A2E`, `706B62`, `B23A2B`, `121417`, `1B1E22`, `EFEAE0`, `7FA7E0`, `F0B254` and `9A958C`.
  - **Delete** every legacy alias and gradient in `app_theme.dart` (cyan, pink, purple, gold, `concertGradient`, `eventsGradient`, `musicGradient`, `podcastGradient`, `radioGradient`, `heroBannerGradient`) and the hexes `4ADE80` and `6B7280`.
- **Typography,** bundled under `assets/fonts/` with each `OFL.txt` (no runtime download):
  - **Unbounded** (wide, dial-like) for display: wordmark, ring numbers, screen titles, the chart's hour labels.
  - **Onest** for body and UI, with `FontFeature.tabularFigures()` for timers and minutes.
  - Files: `Unbounded[wght].ttf` (778,272 B) and `Onest[wght].ttf` (193,056 B) from `raw.githubusercontent.com/google/fonts/main/ofl/{unbounded,onest}/`. Both returned HTTP 200 on 2026-10-12, and both `OFL.txt` files contain "SIL OPEN FONT LICENSE" (copyright lines "The Unbounded Project Authors" and "The Onest Project Authors").
  - Neither name appears as a whole word in any app `lib/`, any app `pubspec.yaml` or any other spec (case-sensitive `grep -w`, 2026-10-12). Hanken Grotesk, Bricolage, Fraunces, IBM Plex, Overpass, B612, Figtree and Lexend were rejected because sibling specs already claim them.
  - Station names in CJK, Arabic or Devanagari fall back to system fonts. A golden must show a Chinese and an Arabic station name rendering.
- **Shape language:**
  - Cards are rectangles with a **4 pt** radius and a 1 pt ink hairline at 12 % opacity, with no shadows. This replaces the 14/18/20 radii.
  - The immersion ring is a **270° dial arc** with tick marks every 5 minutes. It is not a full circle.
  - The tab bar is a flat paper strip with a 2 pt amber underline under the selected label. It is not the Material NavigationBar or the current boxed-icon bar.
  - Now Playing replaces the pulsing coral disc with a horizontal **tuning scale**: a needle position derived from the station's index in the queue, which is a real value, plus the station artwork and the M2 chip.
- **Ads, kept but moved out of the shell.** Remove `const AglAdBanner()` from `main_shell.dart:113`. Place one `AglAdBanner` **inline** in the Today list after the second section, and one in Dial's directory list after Genres. None appears on Log, Now Playing, Car mode, onboarding or Settings. `AglAds.onTransition()` on tab change stays. Placement is not gated by anything other than consent (no remote switch).
- **Splash:**
  - **iOS.** Replace the shared storyboard: the background uses a named colour `LaunchBackground` in `Assets.xcassets` (any appearance `#F2EDE4`, dark appearance `#121417`), and `LaunchImage` becomes the new mark (the dial arc and needle, no text), not the app icon. The storyboard's shasum must differ from `3f6a9b27d8…`.
  - **Android.** `@color/brand_background` and the drawable are updated the same way.
- **Icon:** redraw it in the new language as a dial-blue arc scale with an amber needle on paper. It must not be a Material glyph and must not be the current coral globe with waves. Regenerate `AppIcon.appiconset` and the Android mipmaps from one 1024 px source committed under `assets/brand/`. **Exception:** if `flutter_launcher_icons` would touch `project.pbxproj`, stop and report rather than editing it.
- **Wordmark:** "Radio Tune" set in Unbounded. Rename the `Ratio*` classes to `Rt*` (mechanical; it also removes the "Ratio Tune" tell from future screenshots).
- **Test:** goldens re-baselined in the same commit as the theme change (light and dark, Today, Log, Now Playing, multi-script tile). A unit test asserts that `AppTheme.light.colorScheme.primary == Color(0xFF1F4E8C)` and that both fonts are declared in `pubspec.yaml`. A test asserts that no `AglAdBanner` is a direct child of the shell.

**M6. Remove this app's template tells.** Each deletion is named in its commit message.
- **Supabase family:** delete `lib/services/supabase_config.dart`, `lib/services/auth_service.dart`, `lib/app_env.dart` and `lib/services/error_reporter.dart`, the `Supabase.initialize` block in `main.dart:85-104`, the Settings Account section, `supabase_flutter` from `pubspec.yaml`, and `env/` (only `APP_ENV`, referenced by nothing). Delete their tests together with them: `account_deletion_test.dart` (5), `app_env_test.dart` (8), `error_reporter_test.dart` (5), and the `honest_features_test.dart` case "a session from an earlier version can still be deleted". **Replace** that case with a test asserting that `lib/` imports no `supabase_flutter`, contains no `delete_user` and no `Sign in`.
  - Justification: no public build ever existed (Play production draft unpublished, Apple build rejected). The founder confirms in F2.
- **Dead leftovers:**
  - `ContentType` and the event and concert fields in `radio_station.dart`, and their tests in `models_test.dart`, updated rather than skipped;
  - `live_screen.dart`;
  - the WaveWorld and unused files under `assets/logo/`, and the `assets/logo/` and `assets/icons/` entries in `pubspec.yaml` (`assets/icons/` is empty);
  - the `pubspec.yaml` `description` (new text: "Radio Tune — live radio and podcasts by language, with an immersion log");
  - the `main.dart` header comment.
- **`test/failures/`:** `git rm -r --cached test/failures` and add `test/failures/` to `.gitignore`.
- **Hero copy:** "NOW LIVE / Your world of sound / Radio · Podcasts · Music" and the "Free · no account" stat are replaced by the Immersion header. The live directory counts move to Dial's Languages header ("54,684 stations in 241 countries" from `/json/stats`; hidden on failure, as now).
- **Test:** an extended `honest_features_test` asserts that none of these strings appear in `lib/`: "Your world of sound", "rolling mix", "Concert", "Live Events", "WaveWorld", "Ratio".

**M7. Honest by construction.**
- **Coverage notice:** when the spoken query for a target language returns fewer than 10 stations, Today says "Radio Browser lists only {n} talk or news stations in {Japanese} that are working right now. Music stations in {Japanese} are below." No padding with other languages.
- **Classification disclosure:** a one-line footnote on Log: "Talk/music comes from each station's tags in Radio Browser and can be wrong. Tap a session to correct it." Tapping lets the listener flip `spoken` for that station, stored on the device as `radiotune_station_spoken_override_v1` and applied to future sessions.
- **Location privacy:** `getNearby` sends coordinates **rounded to 1 decimal (about 11 km)**, not full precision. Test: the built URL contains `geo_lat=37.8` for input 37.7749.
- **Alarm** copy stays honest (as now). Add: "On iPhone, keep Radio Tune open or playing; iOS does not let apps start audio from a closed state."
- No sample data, no fake streaks, no seeded sessions. The ring starts at 0. Nothing is gated by region, date, reviewer, remote config or a hidden gesture (`AglInsights` Remote Config must not gate any feature; add a grep test for `RemoteConfig` use in `lib/`).
- `scripts/verify_api_hosts.py` must still pass. The hosts are unchanged: `de1` and `de2.api.radio-browser.info`, `itunes.apple.com`, publishers' feeds.

**M8. Proven.**
- `flutter analyze` clean and `flutter test` all green.
- **Total tests ≥ 213** (baseline) after the 19 deletions in M6, so roughly ≥ 19 new tests on top of those listed in M1–M7.
- No `skip:`, and no test deleted except together with its code (M6).
- Goldens re-baselined only in the commit that changes the visuals.
- Path-limited commits (never `git add -A`; never `fastlane/`, `ios/Podfile.lock` or `ios/Runner.xcodeproj/project.pbxproj`), pushed to `master`.
- **Launch and screenshot** on an iOS simulator and an Android emulator, light and dark. Fresh install → onboarding → Today with real Spanish talk stations → play → log shows minutes after ≥ 30 s. Attach the screenshots to the report.

### SHOULD
- **S1.** A "This week in {language}" share card: a PNG rendered from the Log header, shared through `share_plus`.
- **S2.** A wake-to-radio picker that suggests a talk station in the target language.
- **S3.** Car mode shows the M2 chip and today's minutes in large type.
- **S4.** The Dial Languages screen sorts by "talk & news stations" as well as by total.
- **S5.** Spanish UI strings for the new screens through `agl_i18n` (the app's own copy is English today).

---

## 5. Data source

| Data | Source | Verified |
|---|---|---|
| Stations, tags, languages, `languagecodes`, directory stats | Radio Browser `de1`/`de2.api.radio-browser.info` (keyless; UA `RadioTune/…` as now) | curl 2026-10-12 22:30Z: `/json/languages` (counts above); `stations/search?language=spanish&languageExact=true&tagList=news…` returned Cadena SER, esRadio, COPE, RNE Radio 5 (all `lastcheckok=1`); per-language spoken counts in section 3 |
| Podcast charts by storefront | `itunes.apple.com/{cc}/rss/toppodcasts/limit=N/json` → `/lookup` (already used) | es, mx, fr, jp, br, kr, cn, tw, de, it, ru and sa all returned entries on 2026-10-12 |
| Episode language | RSS channel `<language>` | Acast feed `fr`, Megaphone feed `ja`. The COPE feed had no tag, hence the manual override |
| Immersion sessions, goals, streak, overrides | On the device (SharedPreferences) | n/a. No server, no account |
| Fonts | google/fonts `ofl/unbounded`, `ofl/onest` | HTTP 200, sizes and OFL text above |
| Supabase `smvvjivvlprjhzhoizym` | **Not used** after M6 | — |

---

## 6. Store impact (proposals; store-compliance applies them after the build is verified; nothing here edits `store/apps/*.json` or fastlane)

- **Name / subtitle:** proposed name **"Radio Tune: Language Radio"** (26 characters). Proposed subtitle **"Language immersion, live radio"** (30 characters; the developer must check the length against the 30-character limit). This replaces "Radio Tune: Live Radio" / "50,000+ stations worldwide", which put it head-on against TuneIn, myTuner and Simple Radio. The founder decides on repositioning (F1).
- **Category:** keep `MUSIC` primary with `EDUCATION` secondary, or swap them (F3). Verba is `EDUCATION`.
- **Description** (outline). Do not open with the app name. No "——" or ALL-CAPS headings. Keep one ads sentence, not the shared paragraph:
  1. "Learning Spanish, French or Japanese by ear? Tune into real talk and news radio in that language, and see every minute add up."
  2. The Immersion Log: goal ring, streak, hours per language, talk vs music, CSV export.
  3. Today: stations on air now in your language; the honest coverage note for smaller languages.
  4. Everything else: thousands of stations from the community Radio Browser directory (use the live count only in-app, not a fixed number in copy), podcasts, sleep timer, wake to radio, car mode, favourites and playlists, background playback.
  5. Privacy: no account; the log stays on your phone; ads by Google AdMob with consent where required.
- **Keywords:** language learning,immersion,listening practice,spanish radio,french radio,talk radio,news radio,comprehensible input,radio,podcasts,sleep timer
- **Promotional text:** "Pick the language you're learning. Radio Tune finds talk and news stations on air in it right now, and logs your listening hours."
- **Screenshots** (retake from a real build with real data; light theme first, one dark):
  1. Today in Spanish: the ring at real minutes and the talk list.
  2. Log: week chart and hours per language.
  3. Now Playing with "Counting · Spanish".
  4. Onboarding language list with live station counts.
  5. Car mode or sleep timer.
  - Drop the "Your world of sound" hero and "Ratio Tune" shots. The current uncommitted screenshots in `fastlane/` belong to another workstream. Coordinate before replacing them.
- **Feature graphic and icon:** regenerate from the new icon and palette. No Flutter logo, no monogram.
- **Privacy label** (`store/privacy/radiotune.json`, store-compliance):
  - Remove EMAIL_ADDRESS, NAME and USER_ID. No account exists after M6.
  - Keep DEVICE_ID and ADVERTISING_DATA (AdMob), and CRASH_DATA, PERFORMANCE_DATA and PRODUCT_INTERACTION (Firebase).
  - **Consider adding** COARSE_LOCATION (not linked, App Functionality), because the rounded location is sent to radio-browser for Near you. That is store-compliance's call.
  - The privacy *policy* text is legal (Charter §6, F4).
- **Review notes:**
  - Rewrite them without the "2. DEVICES…" skeleton.
  - Remove "The app contains no advertising SDK and shows no ads." (false; AdMob is integrated) and every Supabase / account-deletion line.
  - State plainly: no account, no demo login. On first launch pick a language (e.g. Spanish) or "Just listening". Play any talk station for at least 30 seconds, and the minutes appear in the Log tab.
  - Name the intended user concretely (section 2), not "Anyone who listens to live radio".
  - Claim physical-device testing **only** if it was done and recorded. I cannot verify that it was.
- **Differentiation answers** (for a later Resolution Center reply, which is the founder's decision under Charter §1): Q3 gap = section 3 evidence; Q5/Q6 = radio + podcasts + immersion log is the only audio player in the account (iMaps drops its radio screen per overlap G7); Q7 = only `agl_i18n`, `agl_observability` and `agl_ads`, with no Supabase anymore.

---

## 7. Out of scope

- **Scanner / air-traffic genre** (offered by the overlap guidance). Radio Browser lists such streams, but rebroadcast rights (for example LiveATC or Broadcastify feeds inside a third-party app) are **not verified**, and the genre dilutes the learner focus. Founder question F5.
- Song identification, track log or ICY song history (myTuner, RadioApp and FM Radio App already do it), and recording or time-shift.
- Flashcards, phrasebook, translation, transcripts (Verba's job).
- Accounts, cloud sync, leaderboards, social features.
- CarPlay / Android Auto (needs native work and entitlements).
- An OS-level alarm that wakes a terminated app.
- Any paid API or key.
