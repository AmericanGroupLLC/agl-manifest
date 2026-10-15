# Spec: daily-pulse — the morning edition that only tells you what changed since yesterday

Author: product-manager (AI office), 2026-10-12
Project: real-apps (`../plan.md`, criteria 1–7)
Repo: `/Users/spatchava/agl/daily-pulse` (Flutter app at the repo root)
Base: `master` @ `f681cb455043605ad8abaa39a087ff64fc7edb18` (`git rev-parse HEAD`, `git branch --show-current`, run 2026-10-12)
Baseline (run 2026-10-12 against that base): `flutter analyze` → "No issues found! (ran in 73.0s)"; `flutter test` → "+376: All tests passed!"

**Other people's uncommitted work is in this repo. Do not touch it.** `git status --short` shows modified files under `fastlane/**` (descriptions, notes.txt, changelogs, screenshots), new untracked screenshots under `fastlane/`, and a modified `ios/Runner.xcodeproj/project.pbxproj` (8 lines changed). Nothing in this spec requires editing any of those files. In particular, the Sign in with Apple capability is removed by editing `ios/Runner/Runner.entitlements` only; `CODE_SIGN_ENTITLEMENTS` in the pbxproj keeps pointing at that file and must not be edited. If any file this spec changes picks up someone else's edits before you start, stop and report it.

---

## 1. Problem

**Apple's state** (`/Users/spatchava/agl/.dist/rejections.json` → "daily-pulse"; dates 2026-09-27, 2026-09-29 ×2, 2026-10-05):
- 2026-10-05: Guidelines 4.3 Spam and 4.2.6 App Generation Services. This is the same message every one of the 26 apps received ("duplicate content or functionality", "indistinguishable from what's already widely available", "created from a commercialized template").
- 2026-09-29: 2.1(a): crashed on launch (iPhone 17 Pro Max, iOS 27.0). Also 2.3.3: "The screenshots only display a login screen."
- 2026-09-27: 2.1 Information Needed. Our reply was the 23-app template, with "WHO IT IS FOR: News, weather, air & markets" (the subtitle pasted in).
- Google Play: PRODUCTION_DRAFT_STAGED.

**What this binary does today.** I read every screen under `lib/presentation/screens/` on 2026-10-12.

What works, uses real data, and should be kept:
- Open-Meteo weather and European AQI for a typed city, plus OSM Nominatim reverse geocoding when the user asks for it (`lib/core/services/weather_service.dart:41-234`, `location_service.dart:33`). It has a skeleton state and an honest error state (`home_screen.dart:48-66`).
- A news engine with about 40 publisher RSS feeds. It parses RSS and Atom, handles CDATA, dedupes by title prefix, sorts newest first, keeps a 30-minute in-memory cache, and throws `FeedUnavailableException` when every source fails (`lib/core/services/news_service.dart:97-238, 601-640`). Search goes through Google News and Bing News RSS (`:434-460`).
- Good News and Alerts feeds (`getGoodNews`/`getBadNews`, `:326-350`), World News with country editions (`world_news_screen.dart`), and user-made topic pages (`dynamic_page_screen.dart`, `DynamicPagesNotifier` persisted in shared_preferences, `app_providers.dart:184-266`).
- Bookmarks persisted in shared_preferences (`app_providers.dart:482-521`), and a profile persisted in shared_preferences (`:122-177`).
- A watchlist glance from Yahoo chart and CoinGecko (`stocks_service.dart:57-195`).
- Real empty and offline views (`widgets/common/feed_state_views.dart`). There is no fake data on the production news, weather or quote paths.

What is shallow, dead, or template:
- **An account wall that guards nothing.** The router sends every signed-out user to `/login` (`lib/core/utils/app_router.dart:38-44`). Supabase is used **only** for auth: the one call to the backend is `rpc('delete_user')` (`auth_service.dart:40`), and every piece of user data lives in shared_preferences on the device. The wall is the shared 15-app scaffold: 'Sign in with Apple' (`login_screen.dart:288`), 'Continue with Google' (`:302`), 'Continue as guest' (`:315`), 'Welcome back' (`:174`), plus `app_env.dart`, `supabase_config.dart` and `auth_service.dart`. The wall is also why the screenshots showed a login screen (2.3.3), and why the review notes needed the shared demo login `qa@americangroup.ai`.
- **Notifications is a dead screen.** "Starts empty. The app has no push or notification backend" (`notifications_screen.dart:23-24`). Yet the bell sits on Home (`home_screen.dart`, `_AppBarIconBtn` notifications), there is a Settings row reading "No notifications yet" (`profile_screen.dart:344-345`), and a badge counter is wired to the Search tab (`main_shell.dart`, `hasBadge = i == 2`).
- **'AI' that is not AI.** "AI Daily Briefing" (`home_screen.dart:469`) is two counts. The FAB "Open the AI assistant" (`main_shell.dart:98`) is a rule-based intent parser (`ai_service.dart`). That parser carries a dead OpenAI path with an empty key (`ai_service.dart:25-28,82`; `app_constants.dart:47-50`) and a `HealthData` model for a health feature that does not exist (`stock_quote.dart:111`, ARB key `heartRate`).
- **Person Intelligence** ("Search any world leader, CEO, or celebrity", `home_screen.dart:98,665`; `screens/person/`, 1,121 LOC) is a celebrity news-sentiment page. It has nothing to do with a morning brief, and it widens the app into "general news reader".
- **Trending** (`trending_screen.dart`) just re-sorts the Good News, Alerts and World feeds the app already shows.
- **A tone classifier that misfires.** It does substring matching (`lower.contains(w)`, `news_service.dart:844,847`) on lists that include `'new'` and `'first'` (`:833`) and `'war'` and `'ban'` (`:836,839`). So any headline containing "news" or "first" scores positive, and "software", "award", "bank" and "urban" score negative. The Good News and Alerts feeds, the app's stated differentiator, rest on this.
- **Seeded tickers that overlap ApexMarketWatch.** A fresh profile carries AAPL, TSLA, GOOGL, MSFT and NVDA (`lib/data/models/user_profile.dart:21`). The store screenshot test types the persona "Alex" (`integration_test/store_screenshots_test.dart:57`) and signs in with the QA account (`:250-258`). That is the "Good afternoon, Alex" + AAPL/TSLA screenshot.
- **Fabricated mockups shipped inside the binary.** `assets/images/screenshot_home.png` (opened and looked at 2026-10-12) is a rendered marketing mockup: "Good Morning, Alex", "AI Briefing BETA — Traffic is light this morning. Your first meeting is in 2 hours", "AAPL +2.1% TSLA -0.8% BTC +5.2%". The app has no traffic or calendar feature. The same folder also holds `screenshot_ai_chat.png`, `screenshot_person.png`, `screenshot_world_news.png`, `store_feature_graphic.png` and `splash_screen.png`. None of them is referenced from `lib/` or `test/` (grep, 0 hits), but `pubspec.yaml` bundles `assets/images/`, so every IPA ships invented content.
- **A hard-coded wrong version.** The Version row says '1.0.0 (Build 1)' (`profile_screen.dart:409`). `pubspec.yaml` is `1.0.0+3`.
- **Template skin.** `ThemeMode.dark` only (`lib/main.dart:125`). Neon-on-near-black palette: `#6C63FF` primary, `#00D4AA`, `#FF4FA3`, `#08080F` background (`lib/core/theme/app_theme.dart:14-49`), plus purple-gradient tab pills and FAB. Inter everywhere (`GoogleFonts.interTextTheme`, `app_theme.dart:156`; 168 `GoogleFonts.` calls in `lib/`). The splash is the shared one (`ios/Runner/Base.lproj/LaunchScreen.storyboard` shasum `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, white, with a 540 px `LaunchImage@3x.png`; Android `launch_background.xml` is `@android:color/white`). The ads layout is the shared one: `AglAdBanner` above the bar except on Profile (`main_shell.dart:86`), and an interstitial on tab switches (`:66`). The copy is generic: "Get Started" (`app_en.arb:336`), "Good afternoon" (`app_en.arb:12`), the 👋 greeting, "Quick Access", "Rate Daily Pulse / Share your feedback".
- **Icon.** It does not come from the generator (daily-pulse is not in `scripts/generate_app_icons.py`). It is a neon heartbeat line over a dotted globe on navy (looked at 2026-10-12): the stock "pulse" cliché, in the same neon family as the theme.

**Why Apple sees a template.** The first thing a reviewer meets is the shared login wall. Behind it is a generic "news + weather + stocks + AI assistant" dashboard. That reads as an opportunistic variant of a crowded category (4.3(b)), and it duplicates our own NewsBoard (news) and ApexMarketWatch (tickers) (4.3(a); `overlap.md` G2).

## 2. User and core job

**User:** someone who checks the news, the weather and the air every morning before leaving home. They have about five minutes, and they already saw yesterday's headlines. Their complaint about news apps is that every morning shows the same stories again, from five outlets, mixed with things they read last night. On heavy days they want to limit how much hard news they take in before work.

**Core job:** once a day, open one screen and be done. It shows:
- the weather and air for where you wake up, said as a change from yesterday,
- the stories that are actually new since your last brief, each shown once however many outlets carry it,
- the ongoing stories, marked with how many days they have run,
- a capped amount of hard news and a few bright stories.

Then it ends: "That's today's edition."

**Signature feature: the Since-Yesterday Edition.** Each morning the app builds a dated **edition** on the device and keeps it. When it builds today's edition, it compares the day's stories with the editions already stored:
1. **One item per story.** Headlines from different outlets are clustered by title similarity, and the item says "BBC, NPR, DW +1".
2. **New since your last brief.** Clusters that match nothing in earlier editions lead the edition.
3. **Still developing, Day N.** Clusters that match a story from earlier editions (looking back 7 days) get a "Day N" badge. Tapping it opens the **story thread**: the headline from each day, oldest to newest, with outlets and links.
4. **Already seen.** A story you already had, with the same publisher URL, is not shown again.
5. **The sky, compared with yesterday.** "High 19.6°, 1.5° warmer than yesterday · Air 51, a little worse than this time yesterday · Rain 0% · Sunrise 07:15." This comes from Open-Meteo `past_days=1`.

Editions are archived on the device. The archive can be searched and shared, and it works offline.

**Prototype result (evidence that the matching works on our feeds, not copy for the app).** On 2026-10-12 I ran a Python check on live BBC (31 items), Al Jazeera (25), NPR (10), DW (137) and Sky (8). It used title tokens, lower-cased, with stop words and a trailing "s" removed, and Jaccard similarity across outlets. At a threshold of 0.3 it found **14 cross-outlet pairs, and all 14 were the same story by my reading**. Examples: BBC "Immigration agents search Democratic congresswoman Ilhan Omar's home" ↔ Al Jazeera "US Rep. Ilhan Omar's home searched by immigration agents" ↔ DW "US federal agents search home of Trump critic Ilhan Omar". At 0.4 it found only 2 pairs. Start at 0.3, and fix the threshold with a committed fixture test (M8). France 24 returned HTTP 403 to Python's default user agent. The app sends its own UA (`news_service.dart:83-88`), but I did not test it with that UA.

**Competitor check.** iTunes Search/Lookup API, 2026-10-12. This rests on store descriptions only: I did not run the apps, and WebSearch is disabled here ("Internet mode is not enabled").
- *Morning Brief – Routine* (id6794152945, 4 ratings): "Weather, agenda, commute, headlines and markets become a scroll of cards", with an Apple Intelligence spoken summary.
- *DayStart AI: Morning Briefing* (id6751055528): an AI-voiced "five-minute show" with calendar and commute.
- *Morning Brief: 5 Min News* (id6761484506): "our AI … picks the 5 most important stories", plus an archive and streaks.
- *Scout: Your Daily Brief* (id6756247274): a daily edition by role and industry.
- *Good News Every Morning* (id6786611963): a finite positive-news edition with a "Good Score".
- *Good News Network* (id1044963284, 824 ratings).

None of these descriptions claims to drop stories you saw in earlier briefs, to track a running story day by day, to show one item per story with its outlet list, or to give weather and air as a change from yesterday. Most are AI-written and need an account or a server. Ours runs on the device with no account, no AI, and every source named.

So the claimed gap is **a finite daily edition that knows what you already saw.** The claim rests on descriptions, and **competitor behaviour is not verified.** The category is crowded: "morning brief" alone returns at least five 2025–26 apps. A generic dashboard cannot pass 4.3(b) here. Only the signature can.

## 3. Data sources (real only)

| Data | Source | Proof (2026-10-12) |
|---|---|---|
| Weather now, today/yesterday highs and lows, rain chance, sunrise | `https://api.open-meteo.com/v1/forecast?...&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code,sunrise,sunset,uv_index_max&past_days=1&forecast_days=2&timezone=auto` (keyless) | curl: HTTP 200, 2,690 bytes. `daily.time` = 2026-10-11, -12, -13. Highs 18.1, 19.6, 21.7. Sunrise 07:14, 07:15. tz America/Los_Angeles |
| Air now vs same hour yesterday | `https://air-quality-api.open-meteo.com/v1/air-quality?...&current=european_aqi,us_aqi,pm2_5&hourly=us_aqi,european_aqi&past_days=1&forecast_days=1&timezone=auto` | curl: HTTP 200. current european_aqi 36, us_aqi 51. 48 hourly rows from 2026-10-11T00:00 |
| City search | `https://geocoding-api.open-meteo.com/v1/search?name=…` (already in `weather_service.dart:52`) | curl "Pune": HTTP 200, lat 18.51957, timezone Asia/Kolkata |
| Reverse geocode (only when the user asks) | OSM Nominatim (already in `weather_service.dart:85`) | not re-curled |
| Headlines | publisher RSS already in `news_service.dart` | curl: BBC 200 (31 items), Al Jazeera 200 (25), NPR 200 (10), DW 200 (137). Sky answered through the Python prototype (8). France 24 gave 403 to a default UA (see above). The other ~35 feeds were **not re-checked today**; run `scripts/verify_api_hosts.py` before the build |
| Topic/local search | Google News and Bing News RSS (already in `news_service.dart:389-442`) | not re-curled (my broader curl batch was refused by the office command reviewer, so I kept to the four feeds above) |
| Glance line per symbol | Yahoo chart, CoinGecko (already in `stocks_service.dart`) | **not verified by me today.** The ApexMarketWatch spec (same date) records Yahoo chart answering HTTP 200 |
| Editions, story threads, saved stories, settings | on-device (one JSON file in app documents, or shared_preferences) | — |

No Supabase (the account wall goes, see M1). No API keys, no paid feed, no backend.

## 4. Acceptance criteria

### MUST (what Apple has to see for a real, distinct app)

**M1. No wall, no scaffold, no dead screens.**
- **Account removal.** Remove sign-in entirely:
  - `screens/auth/` (login, signup, auth_widgets),
  - `core/services/auth_service.dart`, `supabase_config.dart` and `app_env.dart`,
  - `authStateProvider` / `AuthNotifier` and the login steps in `app_router.dart`,
  - `Supabase.initialize` in `main.dart:62-70`,
  - the dependencies `supabase_flutter`, `google_sign_in`, `sign_in_with_apple` and `crypto` (if unused afterwards),
  - the `com.apple.developer.applesignin` key in `ios/Runner/Runner.entitlements` (the file stays, with an empty `<dict/>`),
  - the Account section (Sign Out and Delete Account) in Profile. With no account there is nothing to delete; account deletion (5.1.1(v)) applies only to apps that create accounts.
- **Other removals:**
  - the assistant (`screens/ai_lifestyle/`, `ai_service.dart`, the FAB, `aiChatProvider`), the OpenAI constants and `HealthData`,
  - Person Intelligence (`screens/person/`, `person_search_service.dart`, its routes, banner and Quick Access tile),
  - Trending,
  - Notifications (screen, bell, badge counter, Settings row),
  - "Quick Access", "Rate Daily Pulse" and "Share App". Rating and sharing the app are not the app's job, and both are boilerplate tiles.
- **Bundle and defaults.** Delete `assets/images/screenshot_*.png`, `store_feature_graphic.png` and `splash_screen.png` from the bundle. If the store pipeline needs them, they move outside `assets/`; otherwise delete them. Remove the default watchlist (`user_profile.dart:21` → `const []`) and the default interests.
- **Version.** The Version row reads `PackageInfo` (or is removed). No hard-coded '1.0.0 (Build 1)'.
- **Acceptance:**
  - (a) `grep -rniE "supabase|sign in with apple|continue with google|continue as guest|welcome back|openai|person intel|ai assistant|ai daily briefing|notifications|1\.0\.0 \(Build 1\)" lib` → 0 hits. Unrelated words, such as the publisher name "Notifications" if one exists, need a written justification in the PR.
  - (b) `grep -rn "fromEnvironment" lib` → only `AglAdIds.fromEnvironment` in `main.dart`.
  - (c) In a release iOS build, `strings build/ios/iphoneos/Runner.app/Frameworks/App.framework/App | grep -ciE "Sign in with Apple|Continue as guest|AI assistant|Traffic is light"` → 0, and `Runner.app/Frameworks/App.framework/flutter_assets/assets/images/` contains no `screenshot_*`.
  - (d) A widget test shows that a fresh install reaches the edition after onboarding, with no sign-in step.

**M2. Signature: the Since-Yesterday Edition engine.**
- **Pure module `lib/edition/edition_builder.dart`** (no Flutter imports). Input: today's fetched articles plus the stored editions from the last 7 days. Output: an `Edition {date, number, builtAt, sky?, clusters[]}`.
  - Each cluster has `{id, headline (from the outlet with the earliest pubDate), outlets[], articles[], tone, firstSeen, dayN, threadId}`.
  - Clustering: tokenise titles (lower-case, HTML entities decoded, stop words and a trailing "s" removed, tokens of length 3 or more), and union-find on Jaccard ≥ `kClusterThreshold` (start at 0.3) between outlets.
  - Continuity: a cluster matches a prior cluster when Jaccard of the token union ≥ the same threshold. It inherits `threadId`, and `dayN` = number of distinct prior edition dates in the thread + 1.
  - Clusters whose every article URL already appeared in a prior edition are dropped.
- **Sections, in order:**
  1. "New since your last brief", sorted by outlet count, then recency.
  2. "Still developing", with a Day N badge.
  3. "Bright side" (up to 3 stories with positive tone).
  4. "Your topics" (one row per followed topic, up to 3 stories each).
  5. End card: "That's today's edition · N stories from M outlets".
- **Timing.** One edition per local calendar date, built on the first open of the day. Pull-to-refresh later the same day appends a "Since this morning" section, using the same dedupe rules, to the same edition. It does not build a second edition.
- **Story thread screen.** Every headline in a thread, grouped by edition date, with outlet names. Each row opens the publisher URL externally (existing `url_launcher` pattern).
- **Copy.** Edition numbering starts at "No. 1" on the user's first edition. A visible caption explains it once on the first edition: "Tomorrow, stories you've already seen here won't be repeated."
- **Acceptance:**
  - Unit tests on a committed fixture of **real** headlines captured from the feeds (`test/fixtures/edition_day1.json`, `edition_day2.json`, with source URLs and the capture date in the file). Day 2 shows one story as Day 2, drops a repeated URL, and lists the remainder as new.
  - Three outlets' versions of one story form one cluster.
  - Two unrelated headlines that share one proper noun do **not** cluster. The fixture must include such a pair.

**M3. The sky band: today compared with yesterday.**
- Extend `WeatherService` to request `past_days=1` (forecast and air quality) with `timezone=auto`. Return today's high and low, yesterday's high, the precipitation max, sunrise, current AQI and the AQI for the same hour yesterday.
- Render one band at the top of the edition: current temperature and condition, then a delta sentence built from real values only:
  - "x° warmer/cooler than yesterday", or "about the same as yesterday" when |Δ| < 1°,
  - "Air {value} ({band}), better/worse than this time yesterday",
  - "Rain {p}%",
  - "Sunrise HH:MM".
- Settings: units °C/°F (default from locale) and AQI scale European/US (default European, as today).
- When yesterday's value is missing, leave that clause out. Never print "0° warmer".
- **Acceptance:** unit tests for the delta wording at the boundaries (Δ = 0.9, 1.0, −1.0; null yesterday). A widget test asserts the band renders from a recorded Open-Meteo JSON fixture.

**M4. Tone you control, and say why.**
- Rewrite `_computeSentimentScore` as a separate `lib/edition/tone.dart`:
  - whole-word matching (`\b` boundaries),
  - remove the ambiguous words (`new`, `first`, `best`, `great`, `record`, `launch`, `rise`, `fall`, `drop`, `ban`, `risk`, `concern`),
  - return `{tone: bright|neutral|hard, matched: [words]}`.
- **Setting "Hard news in my morning":** None · Up to 3 (default) · All. Hard clusters over the cap are folded into one closing line: "N more hard-news stories today" (tap to expand). The cap applies to the edition, not to the Alerts view.
- Each story card shows a small "why" note when tone ≠ neutral, e.g. "Hard: earthquake, killed". The user sees the rule, not a black box.
- Keep Good News ("Bright side") and Alerts as full lists reachable from their edition sections. Both use the new classifier.
- **Acceptance:** tests that the following stay neutral: "Software update…", "Award-winning…", "Bank of England…", "News in brief", "First look…". "Earthquake kills 12" is hard; "Vaccine breakthrough…" is bright. Further tests: the cap folds clusters correctly, and with "None" no hard cluster appears in the edition body.

**M5. Depth: archive, saved, search, share, offline.**
- **Archive tab.**
  - Lists past editions (date, number, story count).
  - Opening one shows it exactly as built, read from storage, not re-fetched.
  - A search field filters headlines across all stored editions.
  - Retention: 30 editions, oldest pruned. Show the count: "30 editions kept on this phone".
- **Saved tab.** The existing bookmarks, plus a search field and a tone filter (All, Bright, Hard).
- **Share.** "Share today's edition" shares plain text: date, sky sentence, each new story's headline and publisher URL, and an "Edited by Daily Pulse on your phone" footer. Each card also has "Share story". Use the existing `share_plus` dependency.
- **States:**
  - Offline at launch with a stored edition: show the latest edition with a banner "Offline: this is your {date} edition".
  - Offline with no edition: "Your first edition needs a connection to the news and weather sources." with Retry.
  - Some feeds failing: the edition builds from what answered and says "Built from 31 of 38 sources".
  - Weather failing: the sky band shows the existing retry notice.
  - No city set: the band asks for one.
- **Acceptance:** airplane-mode relaunch shows the stored edition with the offline banner (widget test with a fake client throwing `SocketException`). Archive search finds a headline from a stored fixture edition. The share text matches a golden string.

**M6. A home and onboarding built for this job (not the shared shell).**
- **Shell.** Three tabs: **Today** · **Archive** · **Saved**. Settings opens from a gear in the Today masthead. There is no FAB and no gradient pill tabs.
  - On iOS use `CupertinoTabBar` with `CupertinoIcons` (`cupertino_icons` is already a dependency).
  - On Android use the Material `NavigationBar` styled with the M7 tokens.
- **Today layout** (single column, newspaper order):
  - masthead "Daily Pulse · No. 12 · Monday 12 October · Pune",
  - sky band,
  - glance line (if the user added symbols),
  - the edition sections from M2,
  - end card.
  - No name greeting, no emoji, no "Good afternoon".
- **Glance line (ApexMarketWatch boundary).** One line of text, at most 5 symbols, e.g. "AAPL 247.10 +0.8% · BTC 61,200 −1.2%". Delayed quotes, source named. No chart, no tap-through, no detail screen. Empty by default; added in Settings → "Glance line".
- **Topics.** "Your topics" replaces the assistant's page builder. Settings → Topics offers "Add a topic" with a text field and suggestions from the existing category list, plus "Local news for {city}". Each topic is a saved Google News RSS query, using the existing `getForPage`/`PageConfig` storage.
- **Onboarding** (first run only, replaces the 4-step name/city/interests/personality flow):
  1. "Where do you wake up?": Open-Meteo city search with a result list showing country and region, or "Use my location" (the existing permission path).
  2. "How much hard news before breakfast?": the M4 setting.
  3. "Anything you follow?": optional topic chips; Skip is allowed.

  The button copy is "Build my first edition", not "Get Started".
- **Ads.** No `AglAdBanner` in the shell. At most one inline banner after the edition's end card and one in the Archive list after the 5th row, never inside the story sections. The interstitial on tab switches (`main_shell.dart:66`) is removed pending founder decision Q2. Keep `AglAds.configure/initialize` and the Privacy choices row (UMP, legally required).
- **Acceptance:**
  - Widget tests for: three tabs; onboarding shown once; Skip on step 3; no sign-in route exists (`/login` is not registered).
  - `grep -n "AglAdBanner" lib/presentation/screens/home/main_shell.dart` (or its replacement shell) → 0.
  - The glance line test asserts there is no `onTap` and at most 5 symbols.

**M7. Own identity: palette "First Light", typography, shape, icon, splash.**
- **Palette "First Light".** Use `ThemeMode.system` and build both themes from tokens. Every screen reads `Theme.of(context)`/tokens; no hard-coded `AppColors.dark*`. There are 518 `AppColors.`/`Color(0x` references in `lib/presentation` today.
  - Light: surface `#F2F5F9` (cool morning sky, deliberately **not** the cream/paper surfaces several sibling specs chose), ink `#14202B`, seed/primary harbour blue `#2F5D8A`, sun accent apricot `#F2A65A` (sky band and edition number only).
  - Dark: surface `#0F1720`, text `#E6EDF3`, primary lifted to `#7FA7CF`.
  - Tone colours: bright `#2E8B6E`, hard `#A63D40`, neutral = ink at 55%.
  - A grep on 2026-10-12 found none of these seven hexes in any app's `lib/` or in the other specs.
  - Acceptance: `grep -rhoiE "6C63FF|00D4AA|FF4FA3|08080F|0F0F1A|141428|4FC3F7|FFD700|FF4757|00C896" lib` → 0. `grep -n "ThemeMode.dark" lib/main.dart` → 0.
- **Typography.** **Newsreader** (Production Type, OFL) for headlines, the masthead and the edition number. **Figtree** (OFL) for UI and body. Bundle the TTFs under `assets/fonts/` with their `OFL.txt` files, declare them in `pubspec.yaml`, and remove `google_fonts` (no runtime font download). A grep on 2026-10-12 of every app's `lib/` and `pubspec.yaml` and of the other specs found neither font in use.
  - Acceptance: `grep -rn "GoogleFonts\|google_fonts" lib pubspec.yaml` → 0.
- **Shape.** 8 px corners on cards and 0 px on the masthead rules. Hairline 1 px dividers between stories, as in print. No glass, blur, glow or gradients.
- **Icon.** Hand-built art: a half sun rising over three stacked horizontal rules (a folded newspaper edge). Apricot `#F2A65A` sun on harbour blue `#2F5D8A`. No Material glyph, no heartbeat line, no globe. Regenerate every `AppIcon.appiconset` size, the Android mipmaps and `play_store_icon_512.png`. Keep daily-pulse out of `scripts/generate_app_icons.py`.
- **Splash.** A new `LaunchScreen.storyboard` with background `#F2F5F9` and the new mark at its native size. Android `launch_background.xml` and `values-v31` use the same colour.
  - Acceptance: shasum of `ios/Runner/Base.lproj/LaunchScreen.storyboard` ≠ `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`. `LaunchImage@3x.png` ≠ 540×540 white-padded copy.

**M8. Honest, and proven.**
- **Copy:**
  - Settings shows the "Sources" list: every feed the edition uses, by publisher name, plus Open-Meteo, OSM Nominatim (only on "Use my location"), and Yahoo Finance/CoinGecko (only if the glance line is used).
  - It states that editions are stored only on this phone and that nothing is sent to a Daily Pulse server.
  - No "AI", "coming soon", "not connected", "in this build" or "simulator" anywhere in `lib/`.
- **Tests** (`flutter analyze` clean; `flutter test` all pass). New tests cover:
  - edition builder (clustering, continuity/Day N, seen-URL drop, false-positive pair),
  - tone (word boundaries, cap, why-words),
  - sky deltas,
  - archive retention and search,
  - offline edition,
  - share text,
  - onboarding once,
  - three-tab shell,
  - glance line limits,
  - an extended `release_sanity_test` that greps `lib/` for the M1 forbidden strings.
- **Tests removed with their code.** `account_deletion_test.dart`, `signup_test.dart`, and the auth, assistant, person and trending cases in `navigation_test.dart`, `foldable_layout_test.dart`, `production_fixes_test.dart` and `app_env_test.dart` are removed **only together with the code they test**. The commit message lists each removed test by name. No other test is deleted or skipped.
- **Screenshot test.** Rewrite `integration_test/store_screenshots_test.dart`: no persona name, no QA sign-in, a real city typed in onboarding, and live feeds. The edition-continuity screenshot needs a stored prior edition. Seed it from a **real** edition captured on an earlier day of real use, stored as a fixture with its capture date, and label that screenshot's caption "Day 2". Never seed invented headlines.
- **Launch proof.** Build a release iOS app, launch it on the simulator, and screenshot onboarding step 1, Today (sky band plus new and developing sections), a story thread, Archive search, and Settings → Sources. Look at each one (no white screen; memory "Build it and look at it").
  - The 2.1(a) launch crash was never symbolicated in this repo. Check the IPA (`check-what-apple-checks`): run `strings` on the release binary for the removed plugins. Record that a physical-device launch is a human step and is **not verified** by the office.
- Commit path-limited (never `git add -A`; `fastlane/` and `project.pbxproj` carry someone else's edits) and push to `master`.

### SHOULD (in this order, if time allows)

- **S1. A morning reminder on the device.** An optional local notification at a time the user picks: "Your edition is ready: 9 new stories since yesterday". It is computed at fire time from a background-free schedule, so it may say "Open to build today's edition" when there is no data. Needs `flutter_local_notifications` and a permission prompt only when the user turns it on. This replaces the dead Notifications screen with something real.
- **S2. Home-screen widget** with the sky sentence and the count of new stories from the last built edition.
- **S3. Thread follow.** "Follow this story" on a thread keeps it pinned at the top of future editions until the user unfollows it, or until 3 days pass with no new coverage.
- **S4. Infrastructure de-duplication.** Fold `core/services/error_reporter.dart` (byte-identical in 13 apps) into the direct `AglCrash` calls in `main.dart` if that changes no behaviour, and remove `permission_handler` together with a `pod install` that updates `ios/Podfile.lock`. Check first that `Podfile.lock` has no foreign edits.

### CONDITIONAL — only if the founder approves D2 (NewsBoard retired into daily-pulse)

- **C1.** Port NewsBoard's following and hashtag behaviour (`NewsBoard/mobile/lib/features/following/following_screen.dart`, `hashtag/hashtag_screen.dart`, `PreferencesStore.normalizeFollowValue`) as daily-pulse's Topics:
  - normalised follow values ("#Climate" equals "climate"),
  - a topic detail with a follow toggle,
  - a topic rail of chips above "Your topics" in the edition.
- The rest of NewsBoard (its feed and trending tabs, and any ticker follow, which that file says was already removed) is **not** ported. Without D2 approval, M6's Topics stands alone and NewsBoard is not touched.

## 5. Store impact (proposed; store-compliance applies it later; nothing here was written to `store/` or `fastlane/`)

**Name:** keep "Daily Pulse: Morning Brief" (founder may decide otherwise, Q4). **Category:** propose primary **NEWS** (today `LIFESTYLE`, chosen by automation per `_drafted_fields_note`) and secondary WEATHER.

**Subtitle (≤30):** `What's new since yesterday` (26 chars)

**Play short description (≤80):** `A morning edition that skips what you saw yesterday. Weather and air, compared.` (79 chars)

**Promotional text (≤170):** `Each morning, one finished edition: only stories new since your last brief, ongoing ones marked Day 2, Day 3 — and today's weather and air against yesterday's.`

**Description (draft; no "——" headings, no ALL-CAPS skeleton, does not open with the house ads paragraph):**
> Most news apps show you the same stories every morning. Daily Pulse remembers what it already showed you.
>
> Each morning it builds one dated edition on your phone. Stories that are new since your last brief come first. A story that five outlets cover appears once, with the outlets listed. Stories that are still unfolding carry a Day 2 or Day 3 mark — tap it to read how the story moved, day by day. Anything you already saw is left out. When you reach the end, you're done.
>
> The top of every edition tells you how today compares with yesterday where you wake up: warmer or cooler, whether the air is better or worse than this time yesterday, the chance of rain, and sunrise — from Open-Meteo.
>
> You decide how much hard news you want before breakfast: none, up to three stories, or all of it. Every story that is marked bright or hard shows the words that put it there.
>
> Past editions stay on your phone for a month and can be searched and shared. Follow topics or your city's local news. Add up to five symbols to a one-line glance at prices.
>
> No account. Your editions are kept only on your phone. Headlines come from publishers' public feeds and open at the publisher's site. Daily Pulse is free with ads from Google AdMob; where the law requires consent you choose first, and you can change it in Settings.

**Keywords (≤100):** `morning,edition,brief,headlines,since yesterday,weather,air quality,news digest,good news,local news`

**Screenshots to retake** (live data at capture time, no persona, no sign-in screen, no seeded tickers; iPhone 6.9", iPad 13", Play phone and tablet):
1. Today: masthead, sky band with the "warmer than yesterday" sentence, the "New since your last brief" section.
2. "Still developing": a Day 2/Day 3 badge, and the story thread opened.
3. One story card showing "BBC, NPR, DW +1" and its "why" tone note.
4. The hard-news setting (None / Up to 3 / All) and the folded "N more hard-news stories" line.
5. Archive with a search term applied.

The current fastlane screenshots and metadata carry someone else's uncommitted edits. Coordinate with their owner; do not overwrite them from this workstream.

**Play feature graphic:** rebuild it from the new icon and the "First Light" palette. The bundled `store_feature_graphic.png` must not be reused.

**Review notes** (rewrite for this app only; drop the "2. DEVICES" skeleton and the simulator paragraph):
- "No account and no login. Install, choose a city, and the first edition builds. There is no demo account." Remove `demo_account_name`/`demo_account_required`.
- "Editions are built and stored on the device. The signature behaviour is visible from the second day of use. To see it in review: open the app, pull to refresh later in the day (adds 'Since this morning'), or open Archive."
- "This build has no hidden, switchable or region-specific features. Everything is reachable from the first screen."
- Intended audience, in place of the pasted subtitle: "People who read the news and check the weather every morning, already saw yesterday's headlines, and want one finished edition that shows only what changed, with a limit on hard news."
- External services: Open-Meteo (weather, air, city search), OSM Nominatim (only on "Use my location"), publisher RSS feeds, Google News and Bing News RSS (topics and local news), Yahoo Finance and CoinGecko (only if the user adds symbols), Google AdMob, Firebase Crashlytics. Remove Supabase, Sign in with Apple, Google Sign-In and DuckDuckGo.
- Devices: state only what was really tested. A physical-device run is a human step.
- The review contact name stays a founder item (`store/defaults.json` "App Reviewer").

**Privacy label** (proposed; currently the shared 13-app label):
- Remove EMAIL_ADDRESS, NAME and USER_ID (linked, app functionality). There are no accounts any more, and the onboarding name field is removed.
- Remaining: DEVICE_ID and ADVERTISING_DATA (not linked, third-party advertising), CRASH_DATA and PERFORMANCE_DATA (not linked), and PRODUCT_INTERACTION (not linked, analytics, only if `agl_observability` still sends Analytics).
- Coarse location is **not** collected: the position goes once to Nominatim and is not stored (current notes, §5). Store-compliance should confirm this against Apple's definitions.

**differentiation (store json):**
- §3 gap: the competitor paragraph in section 2, keeping its "descriptions only" caveat.
- §5/§6: "Not NewsBoard (retired into this app if D2 is approved) and not ApexMarketWatch: daily-pulse shows one delayed price line and no market screens."
- §4 (beta testing) remains a founder item.

## 6. Out of scope

- Accounts, sync between devices, Supabase.
- AI summaries or any LLM: none is keyless or free, and the signature does not need one.
- Stock charts, quote detail, filings and market news screens (ApexMarketWatch owns them; `overlap.md` G2).
- Turn-by-turn, traffic or hazard weather (iMaps). Calendar, commute, health data.
- Person Intelligence, Trending and the assistant: deleted, not deferred.
- Push notifications from a server. Background fetch.
- Full-text article extraction or reader mode: articles open at the publisher.
- New translations for new strings beyond English. The existing 12 ARB files must still compile; new keys may fall back to English per the `agl_i18n` rules.

## 7. Not verified

- Competitor behaviour: known from App Store descriptions only. WebSearch is disabled ("Internet mode is not enabled").
- About 35 of the ~40 RSS feeds, Google News and Bing News RSS, Nominatim, Yahoo chart and CoinGecko were not curled by me today. The office command reviewer refused a broader curl batch ("outside the office charter … clarify what feature this supports"). I then checked only BBC, Al Jazeera, NPR, DW and Sky. France 24 returned 403 to Python's default UA.
- The cause of the 2.1(a) launch crash: no crash log is in `rejections.json`, and this spec does not claim the removals fix it.
- Whether `agl_observability` activates Firebase Remote Config. The review notes list it, and `lib/` reads no Remote Config value (grep `remoteconfig`, 0 hits). If the package fetches values, store-compliance should confirm that nothing gates features (5.6).
- Physical-device behaviour, and whether Apple will accept the resubmission.

## 8. Founder questions (Charter decisions; the office does not take them)

- **Q1 Privacy policy text.** Removing accounts changes what the policy at `https://www.americangroup.ai/policy/dailypulse/` should say: no email, name or user ID collected; editions stored on the device. Legal text is Charter §6. Approve an updated policy draft?
- **Q2 Interstitial ads.** This spec removes the full-screen ad on tab switches and keeps at most two inline banners (after the end card and in Archive). Less revenue and less template feel. Keep or drop the interstitial (Charter §3)?
- **Q3 D2.** Retire NewsBoard into daily-pulse (C1)? This is a merge/unpublish decision (Charter §8). Without approval, daily-pulse ships without C1.
- **Q4 Name.** Keep "Daily Pulse: Morning Brief", or rename around the signature, for example "Daily Pulse: Since Yesterday"? Availability is not checked, and the bundle id `com.americangroupllc.dailypulse` is permanent either way.
- **Q5 Existing Supabase users of this app.** Guest and Apple sign-ins may exist in project `smvvjivvlprjhzhoizym` from TestFlight or QA. I have not queried production data. Should those rows be left alone or deleted? Production data is Charter §2.
- **Q6 Resubmission and reply** to Apple stay frozen under the 5.6 hold (MA-043, Charter §1). Differentiation §4 (beta testing) needs a true statement that only the founder can give.
