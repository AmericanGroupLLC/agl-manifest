# Spec: BuddyPlay — board games for two, with a rivalry book that remembers every game

Author: product-manager (AI office) · Date: 2026-10-12 · Project: `real-apps` (plan.md, criteria 1–7)
Repo: `/Users/spatchava/agl/BuddyPlay` (app in `mobile/`) · Branch: `main` · Base SHA: `317bc56a4af6851f561b8799cdf3746a05425099`
Store record: App Store "iBuddyPlay" (rejected 5.6, 2026-10-08T14:19:43Z) · Google Play: PRODUCTION_DRAFT_STAGED

This spec is for the software-developer. The developer changes code. This document does not.

---

## 0. What I read, and what the evidence shows (baseline at 317bc56)

Commands run:
- `git -C /Users/spatchava/agl/BuddyPlay rev-parse HEAD` gave `317bc56a4af6851f561b8799cdf3746a05425099`. `git branch --show-current` gave `main`.
- `flutter analyze` (in `mobile/`) gave `No issues found! (ran in 154.1s)`.
- `flutter test` gave `00:14 +306: All tests passed!` (18 test files).
- `git status --short` after the test run showed only the changes that were already there before me (listed in §9). The test run added nothing.

**What works today. I read the code; I did not run the app on a device.**
- 23 games in `lib/models/game_kind.dart`, each with a rules reducer in `lib/core/games/*.dart` and a screen in `lib/features/games/*_screen.dart`. They are real games, not shells. Chess has castling, en passant and under-promotion, and ends on check/mate/stalemate, the fifty-move rule and threefold repetition (`core/games/chess.dart:234`, endings at `:316-331`, resign at `:366`). Battleship has a hand-over screen in pass-and-play (`features/games/battleship_screen.dart:357-378`). Mastermind has Peek/Hide (`mastermind_screen.dart:150`). Hangman hides the word as you type it (`hangman_screen.dart:69`).
- Two phones play over the LAN: UDP multicast plus Bonjour/NSD discovery, with TCP frames carrying the moves (`services/lan_transport.dart`, `services/service_discovery.dart`). The host orders every input and checks the guest's moves with the same reducer (`services/match_controller.dart:24-40, 206-214`). 17 of the 23 games can do this (`features/games/game_registry.dart:41-59`).
- A rivalry ledger. Each finished match adds one W/L/D, stored per opponent id and per game in SharedPreferences under `buddyplay.rivalries` (`services/rivalry_store.dart`, written from `match_controller.dart:236-260`).
- Settings cover the two names, a default game, sound, haptics, theme and the connectivity preference. Ads use agl_ads with UMP. Crash reporting uses agl_observability. Analytics are deactivated natively (`ios/Runner/Info.plist:80-83`, `android/app/src/main/AndroidManifest.xml:47-51`).

**What is shallow, misleading or dead**
1. **Copy about connections contradicts the code.** The Home section header says `'Tier 2 · Wi-Fi · Hotspot'` (`features/home/home_screen.dart:165`) and the filter chip says `'Tier 2 · Wi-Fi'` (`:14`). But Pong, Air Hockey, Racer, Snake Battle and Tank Battle, all in tier 2, are excluded from two-phone play (`game_registry.dart:35-40, 70-71`). Their own card says "One phone". So the header promises a feature the reviewer cannot reach. "Tier" is developer jargon in the UI.
2. **The game count is inconsistent.** The enum has 23 values and the UI says `'All 23'` / `'23 games'` (`home_screen.dart:12, 128`). The store copy says "22 two-player games" (`store/apps/BuddyPlay.json` subtitle and description).
3. **"In this build" copy, which reads as a feature withheld from this build (5.6):** `game_registry.dart:71` `'… which is not in this build'`; `settings_screen.dart:156` `'… phone-to-phone in this build'`; `:178` `'Crash reporting is off in this build.'`; `:309` `'Bluetooth pairing is not in this build'` (the whole `_BleNotice`, `:284-330`); `features/lobby/join_lobby_screen.dart:93` `'… which this build cannot play over a link.'`
4. **Rivalries cannot tell people apart on one phone.** The pass-and-play opponent id comes from the device id (`services/settings_service.dart:115-121`). Renaming "Second player" from "Sam" to "Alex" keeps the same id, and `RivalryStore.record` overwrites the name (`rivalry_store.dart:52-54`). Sam's record becomes Alex's. A family sharing one phone has exactly one rivalry. The Rivalries tab is just a list of totals: no match history, no dates per game, no detail screen, no filter, no share.
5. **Trivia Battle has 15 questions** (`core/games/trivia_battle.dart:110-166`, `grep -c "text:"` = 15). A few matches in, the questions repeat. Word Duel has 30 words and Pictionary 40 prompts.
6. **Developer furniture in Settings:** a raw "Device ID" UUID row (`settings_screen.dart:139`), a "Two-device play: N of M games … in this build" row (`:153`), and a Bluetooth disclaimer.
7. **There is no onboarding.** On first launch the names default to "Player" / "Player 2" (`settings_service.dart:140-141`), so the first rivalry is "Player 2".
8. **A host with only one device waits forever.** "Host for a nearby buddy" opens a lobby that waits for a second phone, and nothing explains that this is expected with one device or how to test it. Two-phone features that a single-device reviewer cannot reach are one plausible way to read "features hidden during review". I cannot prove that was the cause: all 16 identical 5.6 messages arrived within one minute (`.dist/rejections.json`, 2026-10-08T14:19-14:20Z), which points to an account-level judgement.

**Template tells in this app (from the task brief; the bracketed ones I checked myself)**
- Generated glyph icon: `agl-manifest/scripts/generate_app_icons.py:65` `"BuddyPlay": ("sports_esports", "#1A237E", "#5C6BC0")` [read].
- Shared splash: `shasum ios/Runner/Base.lproj/LaunchScreen.storyboard` = `3f6a9b27d80dda327ce7df82d4887e3adbac50e4` [ran; same hash prefix as the 37-app group].
- Banner guard identical to AeroSwift: `lib/app/app.dart:71` `if (_index != _settingsIndex) const AglAdBanner(),` above a stock Material `NavigationBar` [read].
- Tailwind palette with a neon-on-near-black look: `lib/app/theme.dart:6-23` uses 7C3AED, A78BFA, 06B6D4, 67E8F9, F43F5E, FB7185, 10B981, FBBF24, 111827, 1F2937, 374151, F9FAFB, 9CA3AF and 6B7280, all Tailwind defaults [read]. Every game is forced onto that dark "arena" theme (`widgets/game_scaffold.dart:45`), and the default theme is dark (`settings_service.dart:147`).
- No typeface of its own: `pubspec.yaml` has no `fonts:` section [read]. No Cupertino anywhere.
- Emoji used as game icons (`game_kind.dart:85-109`).
- Play feature graphic is a "BP" monogram. Privacy label is the shared 20-app body. Store name has the "i" prefix. One of the 5 screenshots is Settings.

**Competitors (checked against the keyless iTunes Search/Lookup API, `itunes.apple.com/search` and `/lookup`; web search is disabled in this session. I read the listing text only. I have not verified how any of these apps behave.)**

| App (seller, App Store id) | Ratings | What the listing says |
|---|---|---|
| 2 Player Games : Offline Games (Jindoblu Limited, 1465731199) | 420,752 | Arcade minigames on the same device or vs AI. Saves scores between matches for a "2 player cup". Chess listed among "much more". |
| 2 Player Games - Pastimes (Tellmewow Studios, 1496783791) | 16,655 | Same-device minigames, achievements, championship mode. |
| Multiplayer Board Games (CANDYBLOCKS INC., 1547677867) | 2,009 | Online "LIVE" games: chess, checkers, hangman, 4 in a row. "More games coming soon!" |
| Plato: Fun Multiplayer Games (Plato Team Inc., 1054747306) | 287,170 | Online games plus chat with friends. |

None of these four listings describes (a) two phones playing each other directly over the same Wi-Fi with no server and no account, or (b) a running per-person head-to-head history kept across many different games. That is what makes BuddyPlay different. One single-game app (Checkers by Optime Software, 294664915) does list "configurable player names and score tracking", so the spec does not claim that named scores alone are new.

---

## 1. Problem

Two people in the same room, such as a couple, siblings, a parent and child, or roommates, want to play a proper classic board game against each other. Often there is no internet (a cabin, a flight, a hotel). The big "2 player games" apps are arcade minigame collections played on one screen or against an AI. The online board-game apps need accounts and a connection. Neither remembers that *you and your sister* have played 41 games of chess, checkers and Battleship over the last year, or who is ahead.

Today BuddyPlay has the hard parts: full rules and a direct phone-to-phone link. But it presents itself as a generic neon "23 games" grid with jargon tiers, contradictory connection labels, "not in this build" copy and a one-row rivalry list. That is the crowded compilation look Apple calls indistinguishable.

## 2. User

**Primary:** two people who play together often, in person, at the same table: partners, siblings, a parent and a school-age child, roommates. They want classic games with correct rules (chess, checkers, reversi, Connect Four, mancala, Battleship) and a running score of "who's winning this year". Sometimes each has a phone, sometimes they share one.

**Not the user:** solo players wanting an AI opponent, online matchmaking, or a health-trivia audience (that belongs to BodyQuest; see the Trivia must-not below).

**Core job:** start a two-person classic game in two taps or fewer, play it to a correct finish on one phone or on two, and have the result recorded against the right person, for good.

**Signature feature: the Rivalry Book.** A named roster of the people you play. Every finished game goes into a permanent match log per pair, across every game. Each rivalry gets a detail page with the per-game record, streaks and a last-10 form strip. When two phones connect, both show the pair's record before the first move, and both log the match under the same match id, so their books agree. All of it is on-device, with no account and no server.

---

## 3. Acceptance criteria

### MUST (what Apple has to see to judge this a real, distinct app). Each item is testable.

**M1. One honest catalogue and a "game table" home (plan criteria 1 and 4)**
- No user-visible string uses the word "Tier". Group the games by how they are played:
  - **Board classics**: Chess, Checkers, Reversi, Connect Four, Mancala, Nim, Tic-Tac-Toe, Ultimate TTT, Dots & Boxes, Ludo.
  - **Secret-hand games, best on two phones**: Battleship, Mastermind, Hangman, 20 Questions, Word Duel.
  - **Quick duels**: Pong, Air Hockey, Racer, Snake Battle and Tank Battle (one phone only), plus Trivia Battle (two phones possible). The header must not say "one phone", because Trivia Battle is in `networkable`.
  - **Table tools**: Coin & Dice, Pictionary Timer.
  - The exact grouping may change. The rule may not: each card's two-phone badge comes only from `GameRegistry.supportsTwoDevices`, so no section header or filter can claim more.
- The count of games is computed from `GameKind.values`. No literal "23" or "22" appears in `lib/`. The store copy uses the same number (see §6).
- The home screen opens with a **"Tonight's rivalry" card**: the last pair who played, their lifetime record (for example "Sam 12 – 9 – 2 You"), the last game played, and a **Rematch** button that opens that game with those two seats. Below it come a search field that filters the games by name and the grouped game list. The full-width "Join nearby game" pill floating over the grid moves to a "Two phones" action in the app bar or into the start sheet.
- Game cards show a small drawn mini-board for the board classics (a CustomPainter of the starting position) instead of an emoji. Emoji may stay on the table tools.

**M2. The Rivalry Book (signature feature; plan criteria 2 and 3)**
- **Roster.** Settings → Players becomes a roster on this phone. You can add, rename and delete players. One roster player is marked "me" (this phone's owner). Renaming a player keeps their history. Deleting one asks for confirmation and removes their matches.
- **Seat picker.** "Play on this phone" asks who is playing: two chips picked from the roster, defaulting to the last pair, with "+ New player" inline. Each player gets a stable roster id. This fixes defect 4: Sam and Alex each get their own record.
- **Match log.** Every finished match (a non-null `GameOutcome` from `MatchController`) is added to an on-device log with these fields: match id (= `GameSession.id`), game wire id, seat A id and name, seat B id and name, winner id or draw, ending text where the rules expose it (chess `ChessEnding`: checkmate, stalemate, resignation, fifty-move, repetition, insufficient material), start and end timestamps, and one-phone or two-phone. A write with an existing match id is ignored. Store it as JSON in the existing `KeyValueStore` under a new key with a schema version. There is no new database dependency.
- **Migration.** On first launch after upgrade, existing `buddyplay.rivalries` records become roster players plus aggregate-only history rows labelled "Before match history". The old W/L/D totals are kept exactly. No invented per-match rows.
- **Rivalries tab = the Rivalry Book.** One row per pair: names, lifetime W–L–D and the last played date. Tapping a row opens a **Rivalry detail** screen with:
  - lifetime record;
  - a per-game record table;
  - current streak ("Sam has won 3 in a row") and longest streak for each side;
  - a last-10 form strip;
  - the full match log, newest first, filterable by game (chips) and searchable by player name on the list screen.
- **Two-phone handshake.** When the lobby connects, each phone looks up its own log for that peer id and shows the record on a "You vs <name>" interstitial before the board opens. Both phones log the finished match under the shared session id. No log data is sent over the wire for this MUST. A cross-phone comparison is S3.

**M3. Share and export without new native plugins (plan criterion 3)**
- The Rivalry detail screen has **Copy summary**, which puts a plain-text card on the clipboard through `Clipboard.setData`, for example: "BuddyPlay rivalry · Sam vs Priya · 41 games since 2026-03-02 · Sam 22 – 17 – 2 · Chess 9–6 · Battleship 5–7 …". A snackbar confirms it.
- The Rivalry Book has **Copy match log as CSV**: header row, RFC 4180 quoting, every logged match.
- **Do not add `share_plus`, `path_provider` or any other plugin with native iOS code.** It would rewrite `ios/Podfile.lock`, which already has someone else's uncommitted edits (§9). The system share sheet is S4, blocked until that file is free.
- **Erase:** per-rival "Erase this rivalry" and the existing "Erase all", each with confirmation.

**M4. Real empty, error and offline states (plan criterion 3)**
- Rivalry Book empty state: "No games logged yet. Pick two players and play anything; the result lands here." It has a button to Home.
- Rivalry detail filtered to a game with no matches shows "No <game> games between you two yet."
- Host lobby:
  - It states what is happening ("Waiting for a second phone on this Wi-Fi network") and shows the pairing code and address.
  - After 20 s with no peer it shows a help card: both phones on the same Wi-Fi or hotspot; on iPhone, Settings → BuddyPlay → Local Network must be on; join by typing the address shown; or play on this phone instead (a button that opens the same game in pass-and-play).
- Join lobby has the same help card after 20 s with no host found, and a clear message when there is no Wi-Fi or hotspot address (`LanTransport.localAddress()` returns null).
- Corrupt log JSON keeps the current behaviour (`rivalry_store.dart:24-29` returns an empty list instead of crashing). The UI also shows a one-time notice: "Your match history couldn't be read and was reset."
- The app needs no internet for any feature. There is no "offline" banner, because nothing is online apart from ads, which already take no space until they fill.

**M5. Its own identity: palette, type, shape, shell (plan criterion 4)**
- **Palette, "Game table".** Replace every Tailwind hex in `lib/app/theme.dart`:
  - Seed and primary: **felt green `0xFF0E4D3A`**. Accent: **brass `0xFFC9A227`**.
  - Light background: **scorecard paper `0xFFF3EBDD`**. Dark background: **walnut `0xFF2B2118`**.
  - Seats: host = **ink navy `0xFF1F3A5F`**, guest = **brick `0xFFB23A48`**. These replace neon cyan and coral everywhere through `BuddyColors.host/guest` and `seatColor`.
  - Board surfaces are felt green with a brass hairline frame.
  - I grepped all portfolio `lib/` trees for these six hexes and found none in any other app.
- Text on every surface meets 4.5:1 contrast (text-on-paper and text-on-felt pairs). Add a test that checks it.
- **Typography.** Bundle **Fraunces** for display (screen titles, scores, the rivalry numbers, the result banner) and **Instrument Sans** for body text. Both are SIL OFL files from `github.com/google/fonts`: `ofl/fraunces/Fraunces[SOFT,WONK,opsz,wght].ttf` and `ofl/instrumentsans/InstrumentSans[wdth,wght].ttf`. I confirmed both URLs return HTTP 200. Bundle them under `mobile/assets/fonts/` with their `OFL.txt`, declare them in `pubspec.yaml`, and use no `google_fonts` runtime fetch. Neither family is used by any other portfolio app (I grepped `GoogleFonts.*`, `fontFamily:` and `family:` across all repos: the others use Inter, Nunito, Roboto, Poppins, Satoshi, JetBrains Mono and Orbitron).
- **Shape language.** "Scorecard" panels: 6 px radius, a 1 px ruled border in brass at 40 %, and tabular figures for every score. This replaces the 12/14/16 px rounded neon-bordered cards. Pieces are drawn with a slight bevel. The result banner looks like a scorecard line ("Sam wins · Checkmate · 34 moves").
- **Games follow the theme.** Remove the forced dark `arenaTheme` (`game_scaffold.dart:45`). Boards are felt in both themes. The default theme becomes System, not Dark.
- **Shell.**
  - On iOS use `CupertinoTabBar` with `CupertinoIcons`. On Android keep a NavigationBar restyled to the palette.
  - Rename the tabs **Play · Rivalry Book · Settings**.
  - The `AglAdBanner` leaves the shell `Column` above the tab bar (remove `app.dart:71`). It moves to one inline slot inside the Home scroll (after the Board classics section) and one in the Rivalry Book list footer.
  - Still no ads on games, lobbies or Settings.
  - agl_ads itself is not changed.

**M6. Icon and launch screen of its own (plan criterion 4)**
- **New app icon, not produced by `generate_app_icons.py`.** Two facing pawns, ink navy and brick, on a felt-green rounded square with a brass ring. No Material glyph, no diagonal gradient.
  - Draw it with a BuddyPlay-specific script committed in the BuddyPlay repo (for example `mobile/tool/draw_icon.py`, Pillow, run with `python3 -I`).
  - Output every iOS `AppIcon.appiconset` size and every Android mipmap/adaptive density. iOS 1024 has no alpha.
  - Remove the `"BuddyPlay"` row from the DESIGN table at `agl-manifest/scripts/generate_app_icons.py:65`, so a later run cannot overwrite the new icon. Tell the chief-of-staff about it, because that script is shared.
- **Launch screen.** `LaunchScreen.storyboard` background becomes felt green `0E4D3A` (red 0.055, green 0.302, blue 0.227) with the new mark centred. `LaunchImage` is regenerated from the new mark. The storyboard shasum must no longer be `3f6a9b27…`. The Android `launch_background.xml` and `values-v31` splash use the same colour and mark.
- Neither file currently has someone else's edits (`git status` at base shows only `fastlane/` and `ios/Podfile.lock`). Do not touch `ios/Runner.xcodeproj/project.pbxproj`. Replacing images inside existing asset catalogs does not need it.

**M7. Onboarding and Settings copy of its own (plan criteria 1 and 4)**
- First launch shows a short two-step onboarding, skippable, with no account:
  1. "Who's playing?": your name and the first person you play with. This creates the first two roster entries.
  2. "Same table or two phones?": one paragraph each. It explains that two-phone play uses the local network, and that iPhone will ask for Local Network permission the first time you host or join, never before.
- Do not show the iOS permission prompt during onboarding.
- Settings sections become **Players** (the roster), **At the table** (default game, sound, haptics, theme), **Two phones** (automatic or join-by-address only, plus a plain sentence on how it works), and **Privacy** (existing text, rewritten without "in this build"; the Privacy choices tile stays).
- Remove the raw Device ID row. Its reset action moves into Players as "Start a fresh identity on this phone", with the existing confirmation copy reworded. Remove the "Two-device play: N of M" row and the whole Bluetooth notice.

**M8. Honesty: banned phrases and truthful labels (plan criterion 5)**
- No user-visible string in `lib/` contains: "in this build", "this build", "not in this build", "coming soon", "not available yet", "Simulator", "Tier ".
- Rewrites:
  - `game_registry.dart:70-71` → "A real-time game: play it on one phone, each player on their own end of the screen."
  - `join_lobby_screen.dart:93` → 'That phone is offering "<game>", which is played on one phone. Ask them to host one of the two-phone games.'
  - `settings_screen.dart:178` → 'Crash reporting is switched off.'
- Comments may still mention BLE. The UI may not.
- No demo data, no seeded rivalries, no fake opponents, no remote config, no reviewer, region or date detection, no hidden gestures. Every feature is reachable from the first screen on a single device. Two-phone play also needs a second device, and the lobby and review notes say so.

**M9. Trivia depth without stepping on BodyQuest (plan criteria 1 and 5)**
- Expand Trivia Battle's bundled bank from 15 to **at least 120 original general-knowledge questions** in at least 6 categories: geography, science (physical sciences only), history, language and words, sport and games, arts and music.
- **No health, medical, nutrition, fitness or anatomy questions.** That job belongs to BodyQuest.
- Each answer must be a stable, checkable fact. qa-reviewer spot-checks 20 at random against a public reference.
- No question repeats within a match. The next match favours questions not seen recently on this phone (the recent-question ids are persisted).
- Both phones must draw the same questions: selection stays deterministic from the session seed (`SeededRules`).
- Fallback if it cannot be written to that standard in this session: remove Trivia Battle from the catalogue rather than ship 15 repeating questions. Report which option was taken.

**M10. Proven (plan criterion 6)**
- `flutter analyze` is clean and every test passes. No test is deleted or skipped to go green. Tests that assert old strings ("Tier", "All 23") are updated to the new copy, and the change is listed in the commit message.
- New tests, at minimum:
  - Match-log store: append; idempotent on duplicate match id; migration from a v1 `buddyplay.rivalries` blob keeps totals exactly; rename keeps history; delete removes it; corrupt JSON gives an empty list plus the notice flag.
  - Streak and last-10 maths, including draws breaking a streak.
  - CSV export quoting (names with commas and quotes).
  - Seat picker: picking two roster players records the result against those two ids, and Sam and Alex stay separate (a regression test for defect 4).
  - Home: every card in "two phones" sections is in `GameRegistry.networkable`; search filters by name; the game count equals `GameKind.values.length`; the Tonight's-rivalry Rematch opens the right game with the right seats.
  - A banned-phrase test that scans string literals in `lib/**/*.dart` for the M8 list.
  - A theme test: none of the Tailwind hexes listed in §0 appear in `lib/app/theme.dart`; the seed is `0xFF0E4D3A`; the text theme's font families are Fraunces and Instrument Sans.
  - Lobby: with a fake transport and no peer, the help card appears after the timeout, and "Play on this phone instead" opens pass-and-play.
  - Trivia: bank size of 120 or more, no duplicate question text, a health keyword list finds no match, no repeat within a match, and two seeded states with the same seed produce the same question order.
- The developer launches the app on the iOS simulator and takes screenshots of Home, a chess game, the Rivalry detail and onboarding (memory: "build it and look at it"), and attaches them to the report. Commits are path-limited (never `git add -A`; §9) and pushed to `main`.

### SHOULD (valuable; build after the MUSTs)
- **S1. Resume an unfinished game.** For turn-based games, persist the session seed plus the encoded input list after each move (`rules.encodeInput` already exists, `match_controller.dart:176-181`). Replaying through the deterministic reducer restores the game after the app is killed. Home shows "Unfinished: Chess, Sam vs You, move 23 · Resume".
- **S2. Chess PGN.** "Copy PGN" on a finished chess game (clipboard). Store the move list with the log entry.
- **S3. Two-phone book comparison.** After the lobby handshake, exchange the pair's match-id set (a small `lobby` frame) and show "Your books agree: 14 games" or "3 games are only on one phone". Display only; never overwrite either log.
- **S4. System share sheet** for the rivalry card and CSV via `share_plus`, once `ios/Podfile.lock` no longer has someone else's uncommitted edits.
- **S5. Best-of series** (3/5/7) from the start sheet, with the series score in the seat bar and the series result logged. This is not a differentiator (Jindoblu and Tellmewow listings describe cups and championships), but players will expect it.
- **S6. Word banks.** Grow the Word Duel bank (30) and the Pictionary prompts (40) to 150 or more each.
- **S7. Localise the new strings** through `agl_i18n` keys, and widen `supportedLocales` only when the screens are actually translated (`app.dart:22-26`).

### MUST NOT
- No health trivia (BodyQuest owns it). No AI chat or assistant. No accounts, sign-in, Supabase or server of any kind: "no server" is part of the product's promise and of the privacy text.
- No fabricated opponents, sample rivalries or "example" match logs, not even in screenshots. Screenshots are taken from real matches played in the screenshot integration test.

---

## 4. Data source
- **All data is on-device**: game state in memory; settings, roster, match log and recent trivia ids in SharedPreferences through the existing `KeyValueStore` (`services/key_value_store.dart`).
- **Two-phone play**: a direct LAN socket between the two devices (`services/lan_transport.dart`). Nothing goes through a server.
- **No Supabase and no public API.** None is needed. Trivia questions are original content bundled in the app.
- Fonts are bundled OFL files (source URLs verified HTTP 200 on 2026-10-12, §M5).
- Only ad requests (agl_ads, after UMP consent where required) and anonymous Crashlytics reports leave the phone. That is unchanged.

---

## 5. Out of scope
- An AI opponent or single-player mode.
- Online or internet play, matchmaking, accounts, cloud sync, leaderboards.
- Bluetooth transport.
- Two-phone play for the real-time games (needs state snapshots and interpolation; `game_registry.dart:35-40`).
- Changes to the agl_ads, agl_i18n or agl_observability packages.
- Editing `store/apps/BuddyPlay.json`, `store/privacy/*.json`, anything under `agl-manifest/docs`, or anything under `mobile/fastlane/` (another workstream and other people's uncommitted edits). Proposed changes are in §6 for store-compliance to apply.
- Replying to Apple or resubmitting (Charter §1, 5.6 freeze MA-043).

---

## 6. Store impact (proposals for store-compliance to apply after the build. Nothing here has been applied.)

**Name.** "iBuddyPlay" carries the portfolio-wide "i" prefix (overlap.md tell 1). The plain "BuddyPlay" is registered to another developer (`_name_note`). I cannot check App Store name availability from here. Proposed candidates in order: "BuddyPlay: Rivalry Board Games", "BuddyPlay Game Table", "Rivalry Book: Games for Two". The founder picks (§8). The home-screen name stays "BuddyPlay" (`Info.plist:10`).

**Subtitle (30 characters or fewer):** "Board games for two, scored" (27).

**Promotional text (new):** "Chess, checkers, Battleship and more, for two people at one table or on two phones, with a rivalry book that remembers every game you play."

**Description: rewrite.** Do not open with the app name. Do not use the ALL-CAPS heading skeleton or the shared ads paragraph wording. Suggested opening: "Keep score with the people you actually play. Pick two players, play a classic game to a proper finish, and the result goes into your rivalry book: every game, every streak, every rematch, kept on your phone." Then, in plain sentences:
- the games, grouped as in M1, with the count taken from the code;
- how two phones connect (same Wi-Fi or hotspot, no server, no account);
- the Rivalry Book (roster, per-game record, streaks, copy summary or CSV);
- one honest sentence on ads and crash reports.
Remove "22" unless the final count is 22. Keywords: drop "multiplayer". Add "rivalry,score,board games for two,battleship,mancala,reversi".

**Screenshots (retake all; none of Settings).** Use the existing `integration_test/store_screenshots_test.dart` flow, extended. All data must come from matches actually played in the test.
1. Home: the Tonight's-rivalry card plus Board classics.
2. Chess mid-game on the felt board.
3. Battleship hand-over or secret board ("Pass the phone to Sam").
4. Rivalry detail: per-game table, streak, form strip.
5. The two-phone lobby with its pairing code, or the seat picker.

Play feature graphic: new art from the new icon and palette, replacing the "BP" monogram. Do not reuse the generated layout.

**Review notes.** Write them for this app only. Do not use the "2. DEVICES…" skeleton, and do not paste the subtitle as the audience. Content:
- Who it is for: two people who play classic board games together in person and want a running head-to-head record.
- Everything works on one device with no login: choose a game, then "Play on this phone".
- Two-phone play needs two devices on the same Wi-Fi or hotspot: Host on one, "Two phones → Join" on the other. iPhone asks for Local Network permission at that moment.
- A host lobby with no second phone waits and then shows a help card. That is expected, not a hidden feature.
- No features are gated, remotely switched, region-dependent or time-dependent.
- Devices tested: list **only** physical devices a human actually used. If none, say simulator only. Never repeat the old "a build that cannot start never ships" line.
- A screen recording of two physical phones playing would help 5.6. Only a human with two devices can make it (§8).

**Privacy label.** BuddyPlay currently carries the shared 20-app label (`store/privacy/BuddyPlay.json`). It declares PRODUCT_INTERACTION / ANALYTICS and PERFORMANCE_DATA, and its `_derived_from` has `"analytics": true`. But the app never starts AglInsights (`lib/main.dart:24-31`) and deactivates Analytics and Performance natively (`Info.plist:80-83`, `AndroidManifest.xml:47-51`). Proposed label of its own:
- DEVICE_ID + ADVERTISING_DATA: third-party advertising, not linked;
- CRASH_DATA: app functionality, not linked;
- nothing else.
Play Data safety to match. This needs a legal or founder sign-off if wording on the policy page changes (Charter §6).

**Category.** Primary GAMES › Board, secondary GAMES › Family. Currently ENTERTAINMENT / UTILITIES. This is a founder decision (§8).

---

## 7. Files the developer will touch (expected; for review routing)
`lib/app/{theme,app,providers}.dart`, `lib/features/home/home_screen.dart`, `lib/features/rivalries/*` (Rivalry Book, detail), new `lib/features/onboarding/*`, `lib/features/players/*` (roster, seat picker), `lib/features/settings/settings_screen.dart`, `lib/features/lobby/{host,join}_lobby_screen.dart`, `lib/features/games/game_registry.dart`, `lib/widgets/game_scaffold.dart`, `lib/services/{rivalry_store,settings_service,match_controller}.dart` plus a new `match_log_store.dart`, `lib/core/games/trivia_battle.dart`, `pubspec.yaml` (fonts and assets only; no new plugin), `mobile/assets/fonts/*`, `ios/Runner/Assets.xcassets/{AppIcon.appiconset,LaunchImage.imageset}`, `ios/Runner/Base.lproj/LaunchScreen.storyboard`, `android/app/src/main/res/{mipmap-*,drawable*/launch_background.xml,values*/styles.xml}`, `test/**`, `integration_test/store_screenshots_test.dart`, and `agl-manifest/scripts/generate_app_icons.py` (delete one row; coordinate).

## 8. Founder decisions (not taken by the office)
1. App Store name to replace "iBuddyPlay". Candidates in §6. Availability can only be checked in App Store Connect.
2. Category change to Games › Board / Family.
3. Ad placement moving from the shell banner to two inline slots (M5). This may change ad revenue (Charter §3, money).
4. Catalogue scope. The Quick duels (Pong, Air Hockey, Racer, Snake, Tank) are what make BuddyPlay resemble the Jindoblu minigame compilations. Should they stay, grouped below the board classics (the spec default), or be cut so the app is purely board games for two? Cutting is a product-scope change, not a product removal.
5. A human screen recording of two physical phones in a two-phone match, for the 5.6 reply. Only someone with two devices can make it.
6. Privacy label and policy wording change (§6), which touches legal text (Charter §6).

## 9. Other people's uncommitted work in this repo (do not touch)
`git status --short` at base `317bc56`:
- modified: `mobile/fastlane/metadata/android/en-US/images/{phoneScreenshots,tenInchScreenshots}/0{1,2,3}.png`, `mobile/fastlane/metadata/review_information/notes.txt`, `mobile/fastlane/screenshots/en-US/{ipadpro13,iphone69}-0{1,2,3}.png`, `mobile/ios/Podfile.lock`;
- untracked: `mobile/fastlane/metadata/android/en-US/images/phoneScreenshots/0{4,5}.png`, `.../tenInchScreenshots/04.png`, `mobile/fastlane/screenshots/en-US/ipadpro13-04.png`, `iphone69-0{4,5}.png`.

Never commit, revert, stash or overwrite them. Commit with explicit paths only. Because `Podfile.lock` belongs to someone else, this spec forbids new native plugins (M3).
