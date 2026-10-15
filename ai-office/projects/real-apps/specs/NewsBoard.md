# Spec: NewsBoard — a beat tracker: follow a story, see every piece of coverage and how it moves

Author: product-manager (AI office), 2026-10-12
Project: real-apps (`../plan.md`, criteria 1–7)
Repo: `/Users/spatchava/agl/NewsBoard`, Flutter app in `mobile/`
Base: `main` @ `a2eff87eb8029306e2c281628edc09c12291e3a6` (from `git rev-parse HEAD` and `git branch --show-current`, run 2026-10-12)
Baseline (run 2026-10-12 against that base, in `mobile/`):
- `flutter analyze` → "17 issues found": 16 × `prefer_const_constructors` and 1 × `prefer_const_constructors_in_immutables`, all `info`.
- `flutter test` → "+207: All tests passed!"

**Precondition: founder decision D2.** The portfolio recommendation is to merge NewsBoard into daily-pulse and retire it. This spec only applies if the founder decides to **keep** NewsBoard. If D2 is approved, do not build this spec; daily-pulse's conditional item C1 covers the port instead. See founder question Q1.

**Other people have uncommitted work in this repo. Do not touch it.** `git status --short` shows changes under `mobile/fastlane/**` (descriptions, `review_information/notes.txt`, screenshots, plus new untracked `04.png`/`05.png` screenshots) and to `mobile/ios/Podfile.lock`. Nothing in this spec needs any of those files changed. Store copy and screenshots are proposals in §5 for store-compliance to apply later. If a file this spec changes picks up someone else's edits before you start, stop and report it.

---

## 1. Problem

### Apple and Google state
- Apple: rejected under **5.6 Developer Code of Conduct** on 2026-10-08T14:19:47Z ("features that appear to have been intentionally hidden during the review process"; `/Users/spatchava/agl/.dist/rejections.json` → "NewsBoard", 1 message). The text is identical to the other 15 apps' 5.6 messages sent in the same minute, so Apple was judging the account, not this binary alone.
- Google Play: PRODUCTION_DRAFT_STAGED.
- I looked for anything in `lib/` that could read as a hidden feature: `kDebugMode`/`kReleaseMode` (only the error text in `main.dart:146` and `error_reporter.dart:47,79`), `onLongPress`/`onDoubleTap` (none), and Remote Config reads (none in `lib/`; `agl_observability` fetches Remote Config at `insights.dart:104-119`, but NewsBoard reads no value from it). I found no hidden feature. 5.6 is fixed on the account side (founder, MA-043). This spec's job is to make sure that what Apple sees is plainly a real, distinct app with nothing to hide.

### What works today (read in full; file references are under `mobile/lib/`)
- **Real articles.** 23 publisher RSS feeds (BBC News, BBC Sport, NPR, The Guardian; `core/data/feed_sources.dart:58-245`) are fetched concurrently. One feed failing does not break the load. If every feed fails, the app falls back to the last cached set, and with no cache it raises a retryable error (`core/data/article_feed_service.dart:107-138`). A freshness line says "Updated 5m ago", "Offline · showing stories saved 2h ago" or "N of 23 feeds did not respond" (`features/feed/feed_screen.dart:174-218`).
- **Cross-outlet detection.** `markCrossOutletStories` flags two stories from different publishers whose headlines share two or more distinctive keywords (`article_feed_service.dart:186-251`).
- **Following.** Topics and hashtags are matched by whole word or phrase against headline, summary and tags (`core/data/news_repository.dart:132-165`) and persisted (`core/storage/preferences_store.dart`).
- **Saved.** Bookmarks have a write lock, a 500-item cap, swipe to delete and clear all (`core/storage/bookmarks_store.dart`, `features/bookmarks/bookmarks_screen.dart`).
- **Search, share, read.** Search matches headline, summary, source and tag. Share uses the system sheet. "Read at <publisher>" opens the publisher's page.
- All 23 feeds answered **HTTP 200** to a curl on 2026-10-12 with the app's own User-Agent (`NewsBoard/1.0 (Flutter; RSS reader)`). Together they held **587 unique stories** (deduped by scheme+host+path, as the app does), all dated.

### What is shallow, dead or template
- **No memory.** The app only knows the last fetch, at most 30 items per feed (`maxItemsPerFeed`, `article_feed_service.dart:73`). Following, Search and the hashtag page see only those items. Once a story leaves a feed, it is gone. Following has no time dimension, and that is the one thing a person tracking a story needs.
- **Dead code that ships in the binary:**
  - The breaking-news ticker can never appear: nothing sets `isBreaking: true` (searched all of `lib/`). Affected: `widgets/breaking_ticker.dart` and `feed_screen.dart:87-88`.
  - The "⚡ AI SUMMARY" / "KEY FACTS" block renders only when `aiSummary` is non-null, and nothing ever sets it (`article_screen.dart:~180-245`). The literal "AI SUMMARY" is still compiled in.
  - "⚡ BREAKING" (`article_screen.dart:129`) and "👁 … views" (`:307`) are dead too, because `viewCount` is always 0.
  - `widgets/ad_banner.dart` is an unused house ad, "Try NewsBoard Premium … unlimited AI summaries" (`:119-184`).
  - `kSupportedLanguages`/`LanguageOption` in `shared/types.dart` are referenced nowhere else.
  - `NewsCategory.finance` has no feed.
- **Template skin.**
  - Neon cyan on near-black, "Dark-first … Neon cyan drives all primary brand actions … Magenta for monetization" (`core/theme/app_theme.dart:7-11`, primary `#00D4FF`/`#00B8DB`, background `#0A0A0F`).
  - 38 distinct `0xFF…` colour literals in `lib/`. Most are Tailwind defaults, for example the category colours in `shared/types.dart:11-22` (`6366F1`, `F97316`, `06B6D4`, `10B981`, `8B5CF6`, `EF4444`, `3B82F6`, `EC4899`, `F59E0B`, `14B8A6`, `64748B`, `22C55E`).
  - No typeface of its own: `Typography.material2021(platform: android)` (`app_theme.dart:215`).
  - The shared six-tab Material `NavigationBar` with agl_i18n nav keys, and the shared ad guard `if (_index != _profileIndex) const AglAdBanner()` (`features/shell/main_shell.dart:90,100-141`).
  - Emoji screen titles: '🔥 Trending' (`trending_screen.dart:52`), '⭐ Following' (`following_screen.dart:42`), '📰' (`profile_screen.dart:58`, `onboarding_screen.dart:59`).
  - Generic onboarding: "Welcome to NewsBoard" plus topic chips.
  - Shared copy: "Nothing saved yet" (`bookmarks_screen.dart:190`) and a "Your NewsBoard" stats header.
- **Shared launch assets.** `ios/Runner/Base.lproj/LaunchScreen.storyboard` has shasum `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, the same as in 37 apps, with a 540 px `LaunchImage@3x.png`. Android `drawable/launch_background.xml` is `@android:color/white`. The icon (`assets/icon/app_icon.png`, viewed) is a generic rounded "article" glyph in a gradient red on a dark-red gradient square: the portfolio's gradient-glyph formula, though NewsBoard is not listed in `generate_app_icons.py`.
- **Overlap.**
  - Its whole job today, publisher RSS by topic, is one tab of daily-pulse, and both read the BBC.
  - The daily-pulse spec (`specs/daily-pulse.md`, written today) takes "what changed since yesterday", cross-outlet story clustering ("BBC, NPR, DW +1") and "Day N" story threads. Its M6 "Topics" also offers saved Google News queries.
  - If NewsBoard is kept, it must own something daily-pulse does not: **long-running topic tracking with a memory**.

### Why Apple sees a template here
A reviewer opens a generic six-tab news reader in neon-on-black with emoji headers. It looks like many free RSS readers and like our own daily-pulse, and its listing spends 37% of its sentences on what it does not do. Nothing on screen is a capability you could not get from Google News or Apple News.

## 2. User and product

**User:** a person who follows two to five long-running stories closely and wants every new piece of coverage on them from established newsrooms, in dated order, without opening several news apps. Examples: a nursing student following "measles", a renter following "rent control", an engineer following "AI regulation", a parent following "school phones". Their complaints:
- general news apps bury their subject under everything else;
- a story drops out of the feed after a day;
- keyword tracking is a paid tier elsewhere.

**Core job (one, done well):** *Make a beat (a word or phrase you care about). NewsBoard collects every matching story from BBC News, BBC Sport, NPR and The Guardian, keeps it on your phone for 30 days, and shows it as one dated timeline with what is new since you last looked.*

**Signature feature: the Coverage Meter.** Every beat gets a 14-day, day-by-day bar chart of how many matching stories each publisher ran, plus one plain sentence: "This week: 12 stories · the week before: 4". The Desk shows each beat as a row with a 14-day mini-meter and an "N new" count. Everything is computed on the device from the app's own archive. It needs no key, server or account.

**Competitors.** Checked 2026-10-12 against their App Store listings via the keyless iTunes Lookup API (`itunes.apple.com/lookup?id=…`). I did not use the apps themselves. Web search was unavailable in this session (hook: "Internet mode is not enabled").
- **Google News** (id 459182288): "following the topics and sources you care about" and "Full Coverage … organizes everything online about a story". Its description does not mention a per-topic, day-by-day coverage chart.
- **Feedly** (id 396069556): "You will need a Feedly account to use this application", and "Feedly Pro unlocks … Track keywords, brands, & companies". Keyword tracking is behind an account plus a paid tier. NewsBoard does it free, with no account.
- **Inoreader** (id 892355414): "Inoreader Pro is available with a monthly or annual subscription"; "Highlight keywords".
- **Ground News** (id 1324203419): its angle is "bias, reliability and ownership of every source", with a subscription.

The honest angle against these listings: **free, no account, keyword beats with a 30-day on-device memory and a visible coverage trend per beat.** I have not verified whether any of these apps shows a per-topic coverage chart inside the app. Treat the claim as "not mentioned in their listings", not "they lack it".

**Evidence that the meter has real data from the first launch** (curl of all 23 feeds on 2026-10-12, parsed with a throwaway Python script in `/tmp/nbscripts/measure.py`; the numbers are measurements, not app copy):
- 587 unique stories in total.
- Per day, 09-29 → 10-12: 7, 6, 5, 2, 7, 0, 5, 23, 28, 43, 80, 47, 71, 177. A further 86 stories are older than 14 days.
- Beat matches using the app's whole-word rule:
  - "ukraine": 26 (BBC 6, NPR 6, Guardian 14) over 5 days
  - "trump": 44 (BBC 10, NPR 12, Guardian 22) over 7 days in the 14-day window
  - "climate": 15 (BBC 5, Guardian 10)
  - "artificial intelligence": 10
  - "measles": 1
  - "tariffs": 1
- So the newest 6–7 days are well covered on day 1, and older days are thin because feeds only list their latest items. The meter must mark those older days as partial (M3). It must not present them as quiet days.

## 3. Acceptance criteria

### MUST (what Apple has to see for this to be a real, distinct app)

**M1. Headline archive on the device (memory).**
- Every successful fetch upserts stories into a local archive, keyed by the existing link key (`ArticleFeedService._linkKey`, scheme+host+path).
- Stored per story: headline, summary, URL, image URL, publisher, section/category, tags, `publishedAt`, `firstSeenAt`.
- Retention is 30 days by `publishedAt` (or by `firstSeenAt` if undated), capped at 6,000 stories, oldest pruned first.
- Use a real store: `sqflite` (free, recommended) or a JSON file under the application-support directory via `path_provider`. Do not use `shared_preferences` for the archive.
- Record `archiveStartedAt` (the first successful fetch on this install).
- The existing 200-item `ArticleCache` may be replaced by the archive. Keep the offline fallback behaviour: with no network, every screen reads the archive and the freshness line says "Offline · last checked 2h ago".
- *Acceptance:*
  - a unit test fetches twice with overlapping fixtures, and the archive holds the union with no duplicates;
  - stories older than 30 days are pruned;
  - the cap holds;
  - closing and reopening the store keeps the data;
  - a corrupt or unreadable store gives an error state, not a crash and not a silent empty list.

**M2. Beats (the core job).**
- Create, edit, rename and delete a beat. A beat has a name, 1–5 "any of" terms and 0–5 "none of" terms.
- Matching reuses and extends `articleMatchesFollows` (`news_repository.dart:132-165`):
  - case-insensitive whole word or phrase over headline + summary;
  - exact match on publisher tags (`#` ignored);
  - a story matching any "none of" term is excluded.
- A beat page shows the M3 meter at the top. Below it is a timeline of matching archived stories, newest first, grouped under day headers ("Today", "Yesterday", "Thu 9 Oct"). Each row shows publisher, local time and headline (Spectral summary, 2 lines max). Tapping a row opens the article screen.
- **New since last visit:** each beat stores `lastOpenedAt`. Its page draws a divider "New since Tue 14:02" above the stories first seen after that time. The Desk row shows "5 new". Opening the beat clears the count.
- **Migration:** on first run of the new version, every existing followed topic and followed hashtag (`UserPreferences.followedTopics/followedHashtags`) becomes a beat with that single term. This runs once (flagged) and loses nothing. Bookmarks keep their storage key `@one_news_bookmarks`.
- Article screen:
  - add "Track as a beat" for a tag chip (pre-fills the term);
  - add "Add to a beat…" (pick an existing beat to add a term from the tag);
  - `HashtagScreen` gets a "Track as a beat" button instead of the old follow toggle.
- *Acceptance:*
  - "ai" does not match "said" or "Thai";
  - "rent control" matches "Rent  Control" across whitespace;
  - "none of" excludes;
  - a migration test turns stored follows into beats exactly once;
  - a widget test shows the "N new" badge and the divider after a second fetch that adds matching stories.

**M3. Coverage Meter (signature).**
- On the beat page:
  - a 14-column bar chart, one column per local calendar day ending today;
  - each column stacked by publisher: **BBC** (BBC News + BBC Sport), **NPR**, **The Guardian**;
  - colours from M6, with a legend.
- Counts are distinct archived stories matching the beat, by local `publishedAt` date. Undated stories are left out of the bars and stated under the chart: "2 undated stories not charted".
- **Honest history:** columns for days before `archiveStartedAt`'s local date are drawn in a hatched or 35%-opacity style, with one caption line: "Before 12 Oct, counts come only from what the publishers' feeds still listed and are incomplete." No column may imply zero coverage where the app simply has no record.
- Under the chart, one sentence:
  - "This week: N stories · the week before: M" (rolling 7 days vs. the prior 7);
  - if any day in the prior week is partial, append "(incomplete)";
  - if both are 0: "No coverage in the last 14 days."
  - Do not show arrows, "trending" or percentages computed against partial data.
- Accessibility: the chart has a semantics label that reads the counts, for example "Coverage, last 14 days: 9 Oct 3 stories, BBC 1, The Guardian 2; …". Tapping a column scrolls the timeline to that day.
- **Desk mini-meter:** each beat row on the Desk shows the same 14-day counts as 14 thin bars (single colour, no axis), plus "N new · M in 14 days".
- Draw it with `CustomPainter`. Add no chart package unless it is free and has no network or analytics.
- *Acceptance:*
  - a unit test computes per-day, per-publisher counts from a **committed fixture of real headlines** captured from the 23 feeds. The fixture file has the capture date and each item's source URL; never invented headlines. The counts must equal hand-checked expected values;
  - partial-day flagging is tested with an `archiveStartedAt` inside the window;
  - the summary sentence has golden-string tests for the normal, "(incomplete)" and zero cases;
  - a widget test finds 14 columns and the legend.

**M4. Home layout, navigation and onboarding of its own.**
- Replace the six-tab shell with four tabs:
  - **Desk** (home): your beats, each with a mini-meter and new count. "New beat" is at the top. A search icon sits in the app bar.
  - **Sections**: today's publisher sections, the current feed screen minus the hero card, the dead ticker and "For You". It has a horizontal section selector (Top stories, World, Politics, Business, Technology, Science, Health, Environment, Sport, Culture) built from `availableTopics()`.
  - **Saved**.
  - **Settings**.
- The Trending tab, the Following tab and the For You view are removed. Following becomes beats (M2). The cross-outlet flag stays, shown as a small "Also covered by NPR" line on rows where `isTrending` is true.
- Tab labels are the app's own strings, not `navHome`/`navProfile` from agl_i18n.
- **Onboarding = "Start your first beat":**
  - one screen with the prompt "What story are you following?", a text field, and up to 8 suggestion chips;
  - suggestions are computed from the live fetch: the most frequent `headlineKeywords` that appear in headlines from **at least two different publishers** in the current load. Real, not curated;
  - if the fetch failed, show no chips and say "Suggestions appear when the feeds load. You can type any word."
  - "Create beat" saves the beat and lands on its page with the meter. "Skip for now" goes to an empty Desk.
  - The old "Welcome to NewsBoard" + topic chips screen and the interests step are removed. Keep the existing onboarding flag key so updating users skip onboarding.
- *Acceptance:*
  - a widget test with a fake client completes onboarding by typing a term and lands on a beat page;
  - a widget test asserts exactly four destinations with labels Desk / Sections / Saved / Settings;
  - `grep -rn "navHome\|navProfile\|Welcome to NewsBoard" lib` → 0.

**M5. Depth: search, filter, share and export.**
- **Search** (from the Desk and Sections app bars) runs across the whole archive, not only the last fetch.
  - Filters: publisher (BBC / NPR / The Guardian), period (24 h / 7 days / 30 days), section.
  - Results show the match count. "Track as a beat" turns the query into a beat.
- **Saved:**
  - a filter field over saved headlines, and a publisher filter;
  - saved stories persist even after they leave the 30-day archive (they already live in the bookmarks store);
  - "Export saved": plain text through `share_plus` with headline, publisher, date and URL per item.
- **Share beat digest** from a beat page: plain text with the beat name, date range, the "This week / the week before" sentence, per-publisher counts, and up to 50 headlines with publisher, date and URL. Ends with "Collected by NewsBoard on my phone from BBC News, NPR and The Guardian feeds."
- *Acceptance:*
  - golden-string tests for the beat digest and the saved export;
  - a search test finds a fixture headline that is in the archive but not in the latest fetch;
  - a filter test narrows results by publisher and period.

**M6. Own identity: colour, type, shape, icon, splash.**
- **Palette ("press room": oxblood ink on cool newsprint).**
  - Light:
    - background `#F7F6F3`, surface `#FFFFFF`
    - ink `#1C1B1A`, muted text `#6B6660`, hairline rule `#D9D5CF`
    - seed/primary **oxblood `#8C1C13`**
  - Dark:
    - background `#161412`, surface `#201D1A`
    - text `#EDE8E3`, primary `#E07A6E`
  - Meter series:
    - BBC `#8C1C13` (dark `#E07A6E`)
    - NPR **slate teal `#2E6E73`**
    - The Guardian **ochre `#B07A1E`**
    - These are our colours, not imitations of the publishers' brand colours.
  - Delete the 12 Tailwind category colours from `NewsCategory` and every other Tailwind default hex.
  - I grepped every app's `lib/` and every spec in `specs/` for these 11 hexes on 2026-10-12: 0 hits each.
  - Theme follows the system by default. Settings offers System / Light / Dark. Today it is a stored boolean that defaults to light, and the old dark look was neon.
- **Typography:**
  - **Libre Franklin** (UI, headlines, and the masthead in ExtraBold, uppercase, +4% tracking);
  - **Spectral** (summaries, beat timeline excerpts, the meter sentence);
  - both SIL OFL, in `github.com/google/fonts` `ofl/librefranklin` (`LibreFranklin[wght].ttf`, `LibreFranklin-Italic[wght].ttf`, `OFL.txt`) and `ofl/spectral` (`Spectral-Regular/Medium/SemiBold/Bold/Italic.ttf`, `OFL.txt`); I listed both with `gh api` today;
  - bundle them under `assets/fonts/` with their `OFL.txt`, declared in `pubspec.yaml`. No `google_fonts` and no runtime download;
  - a grep today of every app's `lib/` and `pubspec.yaml` and of all specs found neither font. (Literata/Public Sans are taken by the MyFinance spec, Newsreader/Figtree by daily-pulse.)
- **Shape language: newspaper columns, not cards.**
  - List rows are flat, separated by 0.5 px rules (`#D9D5CF`), with no card elevation.
  - Corner radius is 2 px on buttons, chips and inputs. There is no 12/16 px radius anywhere in new code.
  - Section headers are small caps with a 2 px oxblood rule underneath.
  - No emoji in titles, chips or empty states. Remove the category emoji from `NewsCategory`.
- **Platform feel:**
  - on iOS, tab and action icons come from `CupertinoIcons` (already a dependency, `cupertino_icons: ^1.0.8`) through a small adaptive-icon helper; on Android, Material Symbols;
  - pushed routes use `CupertinoPageRoute` on iOS;
  - the bottom bar is a custom bar: label text in Libre Franklin 11 pt, an oxblood 2 px top marker on the selected tab, and no Material pill indicator.
- **Icon:**
  - hand-built art: five vertical bars of rising, uneven height on a short baseline rule (the Coverage Meter), in `#F7F6F3` on a flat oxblood `#8C1C13` square;
  - no gradient, no Material glyph, no newspaper or "article" glyph;
  - regenerate every `AppIcon.appiconset` size, the Android mipmaps and the adaptive icon (`flutter_launcher_icons`: `adaptive_icon_background: "#8C1C13"`), and keep NewsBoard out of `scripts/generate_app_icons.py`.
- **Splash:**
  - a new `LaunchScreen.storyboard` with background `#8C1C13` and the bar mark at its native size; its shasum must differ from `3f6a9b27…`;
  - `LaunchImage` assets replaced;
  - Android `launch_background.xml` and a `values-v31` splash use `#8C1C13`.
- *Acceptance:*
  - `grep -rniE "0xFF(6366F1|F97316|06B6D4|10B981|8B5CF6|EF4444|3B82F6|EC4899|F59E0B|14B8A6|64748B|22C55E|00D4FF|00B8DB|0A0A0F|FF006E|7C3AED|34D399|F87171|FBBF24|9F7AEA|FF1493)" lib` → 0;
  - `grep -rn "GoogleFonts\|google_fonts" lib pubspec.yaml` → 0;
  - both font families are declared in `pubspec.yaml` and the files exist;
  - `shasum ios/Runner/Base.lproj/LaunchScreen.storyboard` ≠ `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`;
  - `grep -rn "BorderRadius.circular(1[26])" lib` → 0;
  - a launch screenshot on a simulator shows the oxblood splash and the new icon (look at it, per the "build it and look at it" rule).

**M7. Honesty: dead and placeholder code removed.**
- Delete:
  - `widgets/ad_banner.dart`, `widgets/breaking_ticker.dart` and their use;
  - the AI summary / key facts / BREAKING / views blocks in `article_screen.dart`;
  - `aiSummary`, `aiKeyFacts`, `viewCount`, `isBreaking`, `readTimeMinutes` (always 0) from `NewsArticle`, keeping JSON reading tolerant of old cached payloads;
  - `kSupportedLanguages`/`LanguageOption`;
  - `NewsCategory.finance`, `forYou` and `trending`;
  - the leftover notification fields if they are unused.
- The stats header "Your NewsBoard / No account needed" in Profile goes.
- The meter says "stories NewsBoard has collected", never "coverage worldwide" or "trending".
- No Remote Config value is read, there are no demo logins, and nothing detects reviewer, region or date.
- *Acceptance:*
  - extend `test/honest_copy_test.dart` `kUnsupportedClaims` with "trending score", "most read", "worldwide coverage", "real-time alerts" and "AI";
  - `grep -rn "AI SUMMARY\|NewsBoard Premium\|isBreaking\|viewCount\|aiSummary" lib` → 0;
  - `grep -rn "AglInsights.remote\|RemoteConfig" lib` → 0.

**M8. Empty, error and offline states, each with its own copy (no shared furniture).**
- Desk with no beats: "No beats yet", the field plus the live suggestions from M4.
- Beat with zero matches: "Nothing in the last 30 days from BBC, NPR or The Guardian mentions "<term>". Try a broader word." with an "Edit beat" button.
- Every feed failed and the archive is empty: an error with "Try again". Some feeds failed: the existing partial line.
- Offline with an archive: a banner "Offline · last checked <time>", with the archive fully browsable.
- Saved empty: "Saved stories stay here even after they leave the 30-day archive." Not "Nothing saved yet".
- Search with no hits: "No collected story mentions "<q>" in this period." with a "Widen to 30 days" button.
- *Acceptance:*
  - a widget test per state, with the offline test using a fake HTTP client that throws `SocketException`;
  - `grep -rn "Nothing saved yet\|stateNothingSaved" lib` → 0.

**M9. Proven (plan criterion 6).**
- `flutter analyze` → "No issues found!" (fix today's 17 infos too).
- `flutter test` passes with at least as many tests as the baseline's 207 plus the new ones listed in M1–M8. No test is deleted or skipped to go green; tests for removed features are rewritten for their replacements.
- `test/ads_placement_test.dart` is updated to the new shell, not deleted.
- `integration_test/store_screenshots_test.dart` is rewritten to drive the new flow: create beats by typing real terms on a fresh install, live feeds, no persona, no seeded data.
- Commits are path-limited to `mobile/lib`, `mobile/test`, `mobile/integration_test`, `mobile/assets`, `mobile/pubspec.*`, `mobile/ios/Runner/Base.lproj/LaunchScreen.storyboard`, `mobile/ios/Runner/Assets.xcassets/**` and `mobile/android/app/src/main/res/**`, then pushed to `main`. Never `git add -A`. Never stage `fastlane/` or `Podfile.lock`.
- Build and launch on an iOS simulator, screenshot the Desk, a beat page with the meter, and the splash, and look at them before calling it done.

### SHOULD
- **S1. Ad placement that is not the shared shell guard.** Move the `AglAdBanner` out of the shell column. Put one inline banner after the 8th row of the Sections list and at the end of a beat timeline. No banner on the Desk, Settings or onboarding. Keep the `agl_ads` interstitial cap. This changes revenue, so the founder decides (Q4). Until then keep the current placement and its test.
- **S2. Publisher switches** in Settings → Sources: turn BBC, NPR or The Guardian off for Sections, beats and the meter, with an honest note that switched-off publishers' stories are still archived.
- **S3. "First covered by"** on the beat timeline. Within a beat, group stories that `markCrossOutletStories`' keyword rule pairs across publishers, and label the earliest one "First here: The Guardian, 09:14 Thu". Keep it inside beats only, so it does not become daily-pulse's front-page clustering.
- **S4.** Replace the duplicated `core/services/error_reporter.dart` (sha group shared by 13 apps) with direct `AglCrash` calls in `main.dart`, if this is safe. It is invisible in the UI, so it is low priority.
- **S5. Archive controls** in Settings: storage used, "Keep stories for 30 days" (fixed; shown, not configurable), and "Clear archive" with a confirmation. Clearing keeps beats and saved items.

## 4. Data source

| Data | Source | Verified |
|---|---|---|
| Headlines, summaries, tags, dates | The existing 23 publisher RSS feeds in `feed_sources.dart` (feeds.bbci.co.uk, feeds.npr.org, www.theguardian.com) | curl, 2026-10-12, NewsBoard UA: **23/23 HTTP 200**; 587 unique stories; Guardian items carry `<category>` tags (e.g. world 45/45, environment 34/34); BBC and NPR send none |
| Beats, archive, last-opened times, saved items | On device only (sqflite or a file; `shared_preferences` for small prefs) | n/a, no network |
| Coverage Meter, suggestions, digest | Computed on device from the archive | n/a |
| Ads, crash reports | `agl_ads`, `agl_observability` (unchanged infrastructure) | unchanged |

- No Supabase and no keys are needed. Run `scripts/verify_api_hosts.py` before the build, as the plan requires.
- **Considered and rejected for this build:**
  - **GDELT DOC 2.0** (`api.gdeltproject.org/api/v2/doc/doc`) is keyless and gives worldwide coverage volume. One `timelinevol` call answered HTTP 200, but with only 3 data points for 7 days of "climate change". The next calls returned **HTTP 429** ("Please limit requests to one every 5 seconds") even 8 s apart. Too unreliable for a reviewer's first launch.
  - **Google News RSS search** answered 200 with 100 items from 81 outlets for "climate change" `when:7d`. But daily-pulse's spec already uses it for Topics (more overlap), and its terms for commercial use are not verified.

## 5. Store impact (proposals; store-compliance applies them, the founder approves the name)

**Name.** "iNewsBoard" is a workaround for a 409 "name already being used", and the "i" prefix is a portfolio tell. Proposed: **"Beatdesk: News by Topic"** (23 characters). An iTunes Search for "beatdesk" on 2026-10-12 returned no app with that name, but App Store Connect availability is **not verified** (it only shows on save). Fallback: "NewsBoard Beats". If renamed, the home-screen name (`CFBundleDisplayName`, Android `label`) must match. That is a separate small code change, only after Q2. Founder decision.

**Subtitle (≤30):** "Follow a story across outlets" (29).

**Promotional / short description:** "Track the stories you care about across BBC News, NPR and The Guardian, and see how coverage rises and falls."

**Description** (replaces the current one: no "WHAT IT DOES NOT DO" section, no opening with the app name, negations kept to the required disclosures):
> Pick a story you're following, like "rent control", "measles" or "AI regulation", and Beatdesk turns it into a beat: every matching story from BBC News, BBC Sport, NPR and The Guardian, collected in one dated timeline.
>
> See coverage move. Each beat has a 14-day Coverage Meter: how many stories each publisher ran each day, and how this week compares with last week. Your Desk shows every beat at a glance with what's new since you last looked.
>
> A memory for the news. Stories stay on your phone for 30 days, even after they drop off the publishers' front pages. Search the whole archive by publisher and period, and save anything you want to keep.
>
> Share a beat digest, with the headlines, dates and links, or export your saved stories.
>
> Every headline and summary is the publisher's own, with a link to read the full story on their site. No account needed; your beats stay on your device.
>
> Free, with ads from Google AdMob. Where consent is required you choose first, and you can change it any time in Settings › Privacy choices.

**Keywords (≤100):** `news tracker,topic,follow story,keyword,beat,coverage,headlines,rss,bbc,npr,guardian,archive`

**Screenshots to retake** (fresh install, live feeds at capture time, beats created by typing real terms, no persona, no seeded data; iPhone 6.9", iPad 13", Play phone and 10" tablet):
1. The Desk with 3 real beats, each with its mini-meter and "N new". Caption: "Every story you follow, in one place".
2. A beat page with the Coverage Meter, legend and week sentence. Caption: "See how coverage rises and falls".
3. A beat timeline with the "New since…" divider. Caption: "Only what's new since you looked".
4. Archive search with publisher and period filters. Caption: "30 days of headlines, searchable".
5. Sections with the oxblood masthead. Caption: "Today's sections from BBC, NPR and The Guardian".
- Retake the Play feature graphic with the new icon and an oxblood background. No Flutter logo, no old monogram.

**Review notes** (replace the shared numbered skeleton; written for this app):
- *What it is and who it is for:* "A topic tracker for people who follow a few long-running stories, like a student tracking 'measles' or a renter tracking 'rent control', and want every story about them from BBC, NPR and The Guardian in one dated timeline, kept for 30 days, with a chart of how coverage changes." Not the pasted subtitle.
- *How to reach every feature, no login:* "First launch asks 'What story are you following?'. Type any word (for example 'Ukraine') or tap a suggestion, then tap Create beat. The beat page shows the Coverage Meter and the timeline. Tabs: Desk, Sections, Saved, Settings. The search icon is on Desk and Sections."
- *Nothing hidden:* "Every feature is in the binary and reachable without an account. There are no server-side switches, no region or date logic and no demo account. All beat data stays on the device."
- *Devices tested:* state only what was actually done. Do not repeat "simulators … a build that cannot start never ships". If a physical-device run happened, name the device and OS. If it did not, say nothing about devices rather than imply it.
- *External services:* the three publishers' RSS hosts, Google AdMob (with UMP consent), Firebase Crashlytics/Analytics/Performance. No backend, no account.
- *Third-party content:* every item is attributed to its publisher and links to the publisher's page. The app stores headlines and summaries on the device for 30 days for the user's own reading.

**Privacy label.** It stays as is (`store/privacy/NewsBoard.json`: device ID and advertising data for third-party advertising; crash, product interaction and performance data, all "not linked to you"). It matches the app's SDKs. Beats and the archive never leave the device, so nothing new is collected. The label is identical to other apps because they ship the same SDKs. Changing it to look different would make it untrue.

**Category:** NEWS (unchanged).

## 6. Out of scope
- Push or local notifications for beats, and background refresh. The app links no notification SDK today. A beat alert that cannot fire must not be promised.
- New publishers or sources, including GDELT and Google News (see §4), and any server or Supabase table. If the founder wants worldwide coverage later, that is a separate spec.
- Accounts, sync across devices, AI summaries or rewrites of any kind.
- Merging with or changing daily-pulse. That is the portfolio-director's job and the founder's decision (Q1, Q5).
- Editing `store/apps/NewsBoard.json`, `fastlane/**` or `docs/**` (owned by another workstream right now). Submitting, replying to Apple, or uploading builds to review.

## 7. Founder questions
- **Q1 (D2, Charter §8):** Keep NewsBoard as the beat tracker described here, or merge it into daily-pulse and retire it? This spec only applies if you keep it.
- **Q2:** Rename "iNewsBoard" to "Beatdesk: News by Topic" (fallback "NewsBoard Beats")? App Store Connect availability is not verified.
- **Q3 (content licensing, open since 2026-09-15):** BBC and NPR syndication terms separate personal from business use. This is an ad-supported company listing that would now also keep headlines and summaries on the device for 30 days. Is that permitted, or should the feed list change?
- **Q4 (money):** Move the AdMob banner from above the tab bar to inline in Sections and at the end of beat timelines (S1)? It probably lowers impressions.
- **Q5:** If NewsBoard is kept, should daily-pulse drop its M6 "Topics" (saved topic queries) and C1, so the two apps do not both offer topic following?
