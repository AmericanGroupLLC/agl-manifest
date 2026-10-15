# Spec: PlantPulse → a local-network remote for the TV and lights you already own, with one-tap scenes across brands

Author: product-manager (AI office), 2026-10-12
Project: real-apps (`../plan.md`, criteria 1–7)
Repo: `/Users/spatchava/agl/PlantPulse` (app in `mobile/`)
Base: `main` @ `ccabdbb38fce5a2cd598787958877b85ca11602e`. Source: `git -C /Users/spatchava/agl/PlantPulse rev-parse HEAD` and `git branch --show-current` (→ `main`), run 2026-10-12.
Baseline, run 2026-10-12 in `mobile/` against that base with `/Users/spatchava/agl/.flutter-sdk/bin/flutter`:
- `flutter analyze` → "No issues found! (ran in 11.2s)"
- `flutter test` → "00:14 +367: All tests passed!"

**Other people's uncommitted work is in this repo. Do not touch it.** `git status --short` shows:
- changes under `mobile/fastlane/**`: `metadata/android/en-US/full_description.txt`, every Play phone/tablet screenshot, `metadata/en-US/description.txt`, `metadata/review_information/notes.txt`, every iPhone/iPad screenshot;
- `mobile/ios/Podfile.lock`. Its diff is one line: `COCOAPODS: 1.16.2` → `1.17.0`.

Nothing under `lib/`, `test/`, `integration_test/`, `android/`, `ios/Runner/` or `pubspec.yaml` is dirty (`git status --short` on those paths printed nothing). This spec changes none of the dirty files.

**Trap.** A native plugin makes CocoaPods rewrite `Podfile.lock`. **Every MUST below needs no new plugin**: networking uses the `http` package already in `pubspec.yaml` plus `dart:io` (`NetworkInterface`, `HttpClient`); export uses Flutter's `Clipboard`; tests use `package:http/testing.dart` (`MockClient`), which ships inside `http`. If a SHOULD needs a plugin, run `git diff mobile/ios/Podfile.lock` first. If the other edit is still there, do not commit `Podfile.lock`; report it.

---

## 1. Problem

**Apple's state.** Not rejected. `/Users/spatchava/agl/.dist/rejections.json` has no "PlantPulse" key (42 keys; checked with `'PlantPulse' in d` → `False`). `status.csv`: `apple: state` UPLOADED, `apple: review_state` PREPARE_FOR_SUBMISSION, build 2 uploaded 2026-10-04, `apple: apple_id` 6817405301. Google Play: PRODUCTION_DRAFT_STAGED. Identifiers in `status.csv`: `com.americangroupllc.plantpulse` on both stores. They are permanent and this spec does not change them.

PlantPulse has not been judged yet. It will be judged under the same account-level scrutiny (4.3 batch on 2026-10-05, 5.6 batch on 2026-10-08). As it stands, it would fail on four separate counts.

**What the app is today (read 2026-10-12; 22,601 lines in `lib/`, including generated l10n).** It is a port of a web prototype called "OmniControl" (`pubspec.yaml:4` `description: "OmniControl — universal remote…"`, `main.dart:64` `OmniControlApp`). It has four tabs (`app/shell.dart:17-21`): Hub, TV, Lights, Pad.

What is good and stays:
- **Honest plumbing.** Every press goes through one `DeviceTransport` seam (`services/device_transport.dart`). A rejected command rolls the UI back to the last accepted state (`tv_controller.dart:30-63`, `command_rollback_test.dart`). Nothing is seeded (`device_repository.dart:24-27`). Corrupt storage decodes to empty instead of crashing.
- **Tactile widgets worth keeping.** `widgets/d_pad.dart`, `rocker.dart`, `color_wheel.dart`, `glow_slider.dart`, `tactile.dart`, `core/haptics.dart`.
- 12 shipped languages, enforced by `test/l10n_test.dart:107,122` (every key present, actually translated).

What is wrong:
- **It controls nothing real.**
  - Out of the box every page drives `SimulatedTransport` (`core/providers.dart:59-70`). The hero says "Simulator mode" (`app_en.arb:24`). The banner says "No hub is configured, so nothing is transmitted… no TV, bridge or console is connected" (`simulatorBannerBody`). Store screenshot 01 shows exactly that.
  - The only real transport, `HttpHubTransport`, POSTs `{deviceId, action, payload}` to `<url>/remote/command` and probes `<url>/health` (`http_hub_transport.dart:74,90`). That contract was invented from the prototype's own tRPC server. The file itself says: "Unverified: this has not been exercised against a live hub, because there is no hub on this network. The request shape is derived from the source" (`http_hub_transport.dart:22-24`). No TV, light or hub product on the market speaks it. In practice a user can control **nothing**.
- **Dead and pretend controls.**
  - **Game pad.** PlayStation-style Triangle/Circle/Cross/Square, "Party chat", "Record clip" (`app_en.arb` `pad*`). "Pair" only flips a flag: "Controller marked as paired" (`padMarkedPaired`). No protocol exists that would let a phone act as a console controller through a "hub".
  - **Streaming tiles.** Netflix, YouTube, Disney+, Prime and Spotify, drawn in their brand colours with initials (`models/tv_state.dart:28-33`). They send `tv.app` to the invented hub and nothing else. They also use third-party marks (5.2.1).
  - **Light "zones".** Free-floating rooms, not bound to any device (`models/light_room.dart`). Six hard-coded scenes with Tailwind gradients (`light_room.dart` `kLightScenes`). A wattage "estimate" derived from slider position ("~{watts}W est., not metered", `lightsDrawEstimate`). That is a made-up number, even though it is labelled.
  - **TV keys no target supports in this form**: number pad, Guide, Subtitles, Voice, Source.
- **Listing honesty.**
  - The store and home-screen name is "iPlantPulse" (`app.dart:16`, `Info.plist:10`, `AndroidManifest.xml:3`), which reads as a plant-care app. The product is a TV and light remote. The store JSON's own `_drafted.drawn_from` says "this app has nothing to do with plants".
  - The Play feature graphic shows an "OC" monogram and "PlantPulse", with the subtitle cut off mid-sentence. I viewed `fastlane/metadata/android/en-US/images/featureGraphic.png`.
  - `status.csv` `measured: ios_bundle_display_name` says "PlantPulse", but `Info.plist:10` says "iPlantPulse". The measurement is stale.
- **Saturated category.** The iTunes Search API (keyless) was run 2026-10-12 for "roku remote" and "universal smart home remote":
  - Roku Remote (Official) (id482066631, 6,266,838 ratings).
  - Rokie (id1016562846, 711,863).
  - TV Remote – Universal Control (id1539090879, 621,629).
  - TV Remote & Universal Control™ (id6458692724, 149,563).
  - Plus many more "Remote for Roku" clones.

  A generic TV remote is the definition of 4.3(b) "already widely available". The app needs an angle the big remotes lack (§2).
- **Skin tells:**
  - The icon comes from the generator: `agl-manifest/scripts/generate_app_icons.py:75` `"PlantPulse": ("local_florist", "#1B5E20", "#7CB342")`. That is a flower glyph on a remote control. The older generator gave it "OC": `generate_launcher_icon.py:42`.
  - The splash is shared: `ios/Runner/Base.lproj/LaunchScreen.storyboard` shasum `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`, the same as 37 apps.
  - Dark-only near-black + neon: `themeMode: ThemeMode.dark` (`app.dart:38`); `OmniColors` `base 080B14`, `blue 3B82F6`, `violet 8B5CF6`, `amber F59E0B`, `rose F43F5E`, `green 22C55E`, `cyan 22D3EE`, `pink F472B6` (`theme.dart:12-26`). 22 distinct Tailwind hexes are in `lib/` (grep count).
  - No typeface: `pubspec.yaml` has no `fonts:`. `theme.dart:64` says Space Grotesk + Inter were rejected, and mono falls back to `'monospace'` (`theme.dart:120`).
  - Stock icons: 99 `Icons.` uses, 0 `CupertinoIcons` (grep).
  - Bottom-nav shell, plus `AglAdBanner` on two tabs (`home_page.dart:86`, `lights_page.dart:93`), plus an interstitial on **every tab switch** (`shell.dart:49-56` `AglAds.onTransition()`). That last one means an interstitial can cover the remote just as the user goes to press a key.
- **Store tells:**
  - The privacy label is the shared 20-app label. It declares `PRODUCT_INTERACTION/ANALYTICS` and `PERFORMANCE_DATA` (`store/privacy/PlantPulse.json`), but the binary deactivates both: `Info.plist:310-313`, `AndroidManifest.xml:43,46`, and `main.dart:22-28` deliberately has no `AglInsights.init`. The label over-declares.
  - The review notes use the portfolio skeleton: "2. DEVICES…", "Intended audience: Remote for your own hub" (the subtitle pasted in), and the simulator / "a build that cannot start never ships" paragraph.

## 2. User, core job, signature

**User.** Someone with a Roku TV or Roku streaming stick in the living room, plus WLED LED strips (behind the TV, on a shelf, on a desk), and possibly Home Assistant, Node-RED or Homebridge on a Raspberry Pi. They are tired of opening three apps for one evening routine: the Roku app to start a show, the WLED app to dim the bias light, Home Assistant to close the blinds. They want it to work on the home Wi-Fi with no cloud account.

**Honest product.** A **local-network remote** for gear with **real, published, keyless local APIs**:
- **Roku TVs and players** through Roku External Control Protocol (ECP). Port 8060, plain HTTP, no auth. As of Roku OS 14.1 it needs Settings › System › Advanced system settings › **Control by mobile apps = Enabled**. Verified 2026-10-12 in `https://developer.roku.com/docs/developer-program/dev-tools/external-control-api.md` (curl -L with a browser UA → 200, 969,698 B). I read: the `keypress/<KEY>` key list, `launch/<appId>`, `query/device-info` with a sample XML, `query/icon/<APP_ID>`, `query/media-player`, and the Control-by-mobile-apps requirement.
- **WLED** LED controllers through the WLED JSON API: `GET /json/info`, `GET|POST /json/state`, `/json/eff`, `/json/pal`, with fields `on`, `bri`, `seg[].col`, `fx`, `ps` (preset), `nl` (nightlight), `transition`, and `info.leds.pwr` (device-reported current). Verified 2026-10-12: `https://kno.wled.ge/interfaces/json-api/` → 200, 137,427 B, including the sample response.
- **Webhooks** for a hub the user runs. Home Assistant's webhook trigger is `POST http://<ha>:8123/api/webhook/<webhook_id>`, with no token needed (`local_only`, `allowed_methods`). Verified 2026-10-12: `https://www.home-assistant.io/docs/automation/trigger/` → 200. The same step type covers Node-RED or any HTTP endpoint the user types. This replaces the invented `/remote/command` contract, so "a hub you run yourself" becomes true.

**Core job: control the living room from the phone, for real.**
1. **Find** Roku and WLED devices on the same Wi-Fi (§4 M2).
2. **Remote** a Roku. It shows only the keys that model supports, it can type with the phone keyboard into Roku search fields, and it reads the real power mode.
3. **Light panel** for each WLED. It reads the device's real state, then offers on/off, brightness, colour (the existing colour wheel), effects listed by the device itself, presets, and a nightlight fade-off timer.

**Signature feature: Scenes across brands.** A scene is an ordered list of steps across different devices, run with one tap from the home screen. For example, "Movie night":
1. WLED "TV backlight" → preset 3;
2. WLED "Shelf" → brightness 40, transition 2 s;
3. webhook → `POST http://homeassistant.local:8123/api/webhook/close_blinds`;
4. wait 2 s;
5. Roku "Living room" → `launch/<channel id>`.

Each run produces a **run report** built from the real HTTP results ("WLED Shelf · 200 · 84 ms ✓", "Roku · timed out after 4 s ✗"). It is saved to history and can be copied. Everything goes phone → device on the LAN. There is no server, account or cloud of ours.

**Competitor check** (iTunes Search API, keyless, 2026-10-12; descriptions only, no app was run. WebSearch and WebFetch are unavailable in this session: the hook returned "Internet mode is not enabled".)

| App (id, ratings) | What it controls | Cross-brand scenes without running a server? |
|---|---|---|
| Roku Remote (Official) (482066631, 6,266,838) | Roku only | No (Roku only) |
| Rokie (1016562846, 711,863) | Roku only, per its description | No |
| WLED – Official App (6446207239, 11); WLED+ (6474789652, 13); WLED Max; WLED Hub; WLED Pro | WLED only | No |
| Philips Hue (1055281310, 115,979) | Hue only | No |
| Home Assistant (1099568401, 3,967) | Everything, Roku/Hue/WLED named in its description | Yes, **but only with a Home Assistant server the user installs and maintains** |
| Apple Home (1110145103) | HomeKit accessories | WLED and plain Roku players are not HomeKit by default. **Not verified** |

**Claimed gap, stated narrowly.** Among the descriptions read, no app combines a Roku remote, WLED control and arbitrary webhooks into one-tap, ordered, timed scenes that run straight from the phone, with no server and no account. Home Assistant does it, but only after the user installs and maintains a server. **Competitor behaviour beyond these descriptions is not verified.** The scene, not the remote, must lead the screenshots and the copy (§5), because the remote alone is 4.3(b).

**Must not duplicate.** No other portfolio app controls devices (per the brief: "No overlap with any other app"). The lights here are WLED hardware control, not a lamp or plant timer.

## 3. Data sources

**Everything is the user's own devices on their own network, plus on-device storage.** No Supabase, no public API of ours, no account, no key.

| Data | Source | Notes |
|---|---|---|
| Roku identity and capabilities | `GET http://<ip>:8060/query/device-info` (XML) | Read: `user-device-name`, `model-name`, `vendor-name`, `power-mode`, `supports-find-remote`, and on Roku OS 15+ `supports-tv-power-control` and `supports-audio-volume-control`. All appear in the doc's text or sample. A missing field means unsupported, not guessed. **Test fixture = the doc's own sample XML, copied verbatim and cited in the fixture header** |
| Roku keys | `POST http://<ip>:8060/keypress/<KEY>` | Only the documented names: Home Rev Fwd Play Select Left Right Down Up Back InstantReplay Info Backspace Search Enter; FindRemote (if `supports-find-remote`); VolumeDown VolumeMute VolumeUp PowerOff (Roku TVs / supported players); ChannelUp ChannelDown InputTuner InputHDMI1–4 InputAV1 (Roku TV). Keyboard: `Lit_<url-encoded char>` |
| Roku channel launch | `POST http://<ip>:8060/launch/<appId>` | The doc says production app IDs come from Roku's deep-link test tools. The user types the ID. No channel names or logos are shipped |
| Roku installed channels | `GET /query/apps` | **Not in the current Roku doc** (the doc lists `query/icon`, `query/device-info`, `query/media-player`, `query/tv-channels`… but not `query/apps`; `grep -o 'query/[a-z0-9-]*'` on the fetched page). **SHOULD only (S2)**, with an honest fallback |
| WLED identity and state | `GET http://<ip>/json/info`, `GET /json/state`, `GET /json/eff` | `info.name`, `info.ver`, `info.leds.count`, `info.leds.pwr` (mA, device-reported), `state.on/bri/ps/seg[0].col/fx`, effect names. **Test fixture = the doc's sample response, cited** |
| WLED control | `POST http://<ip>/json/state` | `{"on":…}`, `{"bri":0-255}`, `{"seg":[{"col":[[r,g,b]]}]}`, `{"fx":id}`, `{"ps":1-250}`, `{"nl":{"on":true,"dur":min,"mode":1}}`, `"transition"` (all in the doc) |
| Webhook | URL typed by the user, `POST`/`PUT`/`GET`, optional JSON body | http allowed only for private/LAN hosts (`10/8`, `172.16/12`, `192.168/16`, `*.local`); public hosts need https with a valid certificate |
| Devices, rooms, scenes, run history, last-answered times | `SharedPreferences` (existing `DeviceRepository` pattern) | New keys `couchdeck.devices.v2`, `.scenes.v1`, `.runs.v1` (last 100 runs), migration from `omnicontrol.devices.v1` / `.rooms.v1` / `.hub_url.v1` (M1). Key prefix follows `kAppName` once Q1 is decided; "couchdeck" is a placeholder |
| Discovery subnet | `dart:io` `NetworkInterface.list()` → the phone's private IPv4 | `dart:io` exposes no netmask, so the scan assumes the phone's `/24` and says so on screen. Other subnets are added by typing an IP |

**No seeded devices, channels, scenes, wattage or state.** A fresh install shows real empty states.

## 4. Acceptance criteria

### MUST (what Apple has to see to judge this a real, distinct app)

**M1. Remove the fiction and dead controls (criteria 1, 5).**
- **Remove the simulator as a user-facing mode.** `SimulatedTransport` may survive only inside `test/`. No screen may say "Simulator", "Simulated", "not transmitted", "No hub is configured" or "nothing is sent". With no devices, the controller screens are unreachable and Home shows the setup state instead (M6).
- **Remove the invented hub contract.** That means `HttpHubTransport`'s `/remote/command` + `/health` endpoints, the Settings "Protocol" block (`settingsProtocol*`) and the hub-address field. **Migration:** if `omnicontrol.hub_url.v1` is set, create one Webhook device "My hub (from earlier version)" with `POST <url>/remote/command`, and show a one-time Home note that says so.
- **Remove the game pad tab** entirely: `features/gamepad/*`, `models/gamepad_state.dart`, `widgets/analog_stick.dart` if unused elsewhere, and all `pad*` strings.
- **Remove the streaming-brand tiles** (`tv_state.dart:28-33`), plus the number pad, Guide, Subtitles, Voice, Source, Stop and Previous-channel keys. None of them is in the Roku ECP key list.
- **Remove** the free-floating light zones and `kLightScenes` (`light_room.dart`), and the wattage estimate (`estimatedWatts`, `lightsDrawEstimate`, `lightsEstimateNote`).
- **Legacy data migration** (`devices.v1`, `rooms.v1`):
  - `tv` devices with a host become Roku candidates;
  - `light` devices with a host become WLED candidates;
  - both are re-checked on first open (M2), and a candidate that does not answer as Roku or WLED shows "Didn't answer as a Roku or WLED device" with Edit and Remove;
  - `console` devices and zones are dropped, and a one-time note lists their names.
  - Nothing is silently lost.
- **Tests removed with their code** (`gamepad_state_test.dart`, `gamepad_page_test.dart`, the simulator/hub parts of `transport_test.dart` and `app_smoke_test.dart:217`) are named in the commit message. No other test is deleted or skipped.
- **Acceptance:**
  - `grep -rniE "simulat|not transmitted|no hub|coming soon|in this build|not connected|unavailable|demo|sample|Netflix|YouTube|Disney|Spotify|Prime|Triangle|Party chat|est\., not metered|OmniControl" mobile/lib --include=*.dart --include=*.arb` → 0 hits. Exception: generated l10n is regenerated, so it carries no hits either.
  - `grep -rn "remote/command\|'health'" mobile/lib` → only the migration's literal (1 hit).
  - Migration unit tests cover all four legacy shapes.

**M2. Core job part 1: find and add real devices.**
- **Before the first scan**, an explainer: "Couchdeck looks for Roku and WLED devices on this Wi-Fi. iOS will ask to allow Local Network access." Then a **Scan** button. Reword the existing `NSLocalNetworkUsageDescription` (`Info.plist:303-304`) to: "Finds and controls your Roku and WLED devices, and sends your webhook steps, on your home network."
- **Scan.**
  - From `NetworkInterface.list()`, take the first private IPv4 and probe `.1`–`.254` of its `/24`.
  - Each host gets `GET :8060/query/device-info` and `GET :80/json/info`, with a 600 ms timeout and at most 24 requests in flight. Show progress ("Checked 120 of 254") and a Cancel button.
  - Results list as "Roku · Living Room TV · Roku Ultra" or "WLED · Shelf · 60 LEDs · v0.15.0", from the real responses, each with **Add** and a room picker.
  - Pure-Dart parse functions, unit-tested against the doc fixtures.
- **Not on Wi-Fi** (no private IPv4): "Your phone isn't on a home network. Connect to the Wi-Fi your TV and lights use, then scan again." No scan runs.
- **Nothing found:** "No Roku or WLED answered on 192.168.1.x." Then three checks: Roku: Settings › System › Advanced system settings › Control by mobile apps must be **Enabled**; WLED: same Wi-Fi as this phone; or **Add by IP address**.
- **Add by IP / Add webhook.** Manual forms. An IP must answer the matching probe before it saves as Roku/WLED. A webhook validates URL shape and the LAN-or-https rule (§3), plus an optional **Send test** that shows the real status code.
- **Multicast SSDP/mDNS is out of scope.** iOS requires the `com.apple.developer.networking.multicast` entitlement, which Apple must grant (per Apple documentation as I know it; not re-fetched today). That is a credentials step for the founder.
- **Platform.**
  - iOS: add `NSAppTransportSecurity › NSAllowsLocalNetworking = true` to `Info.plist`.
  - Android: add `<uses-permission android:name="android.permission.INTERNET"/>` explicitly. Today's main manifest declares no permissions; INTERNET probably arrives only through AdMob's manifest merge. **Not verified.** Also add a `network_security_config.xml` that permits cleartext. Neither file is dirty.
  - **Verify cleartext LAN HTTP on the Android emulator** against the local harness at `10.0.2.2`.
- **Acceptance:** unit tests for subnet derivation, the private-IP and LAN-or-https rules, device-info and json/info parsing (doc fixtures), and scan concurrency/timeout/cancel with `MockClient`. Widget tests for not-on-Wi-Fi, nothing-found and add-by-IP rejecting a non-answering host.

**M3. Core job part 2: the Roku remote and the WLED panel, driven by the real device.**
- **Transport.** Introduce `RokuEcpTransport` and `WledTransport` behind the existing `DeviceTransport` seam (keep the seam, `CommandResult` and the `CommandBus` rollback). `CommandResult` drops `TransportKind.simulator`, and `reachedHardware` becomes "2xx from the device".
  - Roku 403: "Roku refused. Turn on Settings › System › Advanced system settings › Control by mobile apps." The 403 status itself is **not verified** against a device; show this hint for any 401/403.
  - Timeout: "Living Room TV didn't answer in 4 s."
- **Remote screen** (one Roku per screen; a device picker if there are several):
  - D-pad + OK, Back, Home, Instant Replay, Info, Rev/Play/Fwd.
  - Volume rocker and Mute only when `supports-audio-volume-control` is true or the device is a Roku TV (TV: `supports-tv-power-control` present, or a `model-name` reported by device-info containing "TV"; rule unit-tested).
  - Power off only when `supports-tv-power-control` is true. There is **no Power on**: it is not in the documented key list.
  - Channel and Input keys only for Roku TVs. Find Remote only when `supports-find-remote` is true.
  - A **Type** sheet: the phone keyboard sends `Lit_` per character, plus Backspace and Enter.
  - The header shows `user-device-name`, `model-name` and `power-mode` as read ("PowerOn", "DisplayOff"…), re-read on open and on pull-down. Never assumed.
  - Existing volume and channel number tracking (`TvState.volume/channel`) is removed: ECP does not report them, so any number shown would be invented.
- **WLED panel:**
  - On first open, state comes from `GET /json/state`. If the GET fails, show "Couldn't read Shelf" with Retry; no controls are shown until a read succeeds.
  - Controls: power, brightness (existing `glow_slider`), colour (existing `color_wheel`), effect list from `/json/eff` with search, preset number 1–250, and a **Nightlight** off-timer (`nl`, 5–120 min, fade).
  - Shows `info.leds.pwr` as "Drawing about 1.2 A (reported by WLED)" only when > 0. No other power figure.
  - After each POST, re-read state with `"v":true` in the body; the response is the authoritative state, and rollback applies on failure.
- **Acceptance:**
  - `MockClient` tests assert the exact method, URL and body for every Roku key and WLED control.
  - Tests for capability gating with three fixtures: doc sample (no volume or power fields → no volume rocker and no power key); a TV fixture with `supports-tv-power-control`; a fixture with `supports-find-remote=true`.
  - Tests for `Lit_` encoding (`é` → `Lit_%C3%A9`), WLED state parse and the pwr display rule.
  - Rollback tests are kept, re-pointed at the new transports.

**M4. Signature: Scenes across brands.**
- **Model.** `Scene {id, name, glyph (one of 12 drawn glyphs), steps[], stopOnFailure=false}`. Step is one of:
  - `rokuKey {deviceId, key}`
  - `rokuLaunch {deviceId, appId, label}`
  - `wledState {deviceId, on?, bri?, rgb?, fx?, preset?, nightlightMin?, transitionDs?}`
  - `webhook {deviceId(webhook), method, body?}`
  - `wait {ms 250–30000}`
- **Editor.** Add, reorder (drag) and delete steps. Each step's editor only offers what that device supports, using the M3 capability rules and the WLED effect list read live. If the device is offline, the editor allows the raw value and marks it "not checked".
  - **Test step** runs that step alone and shows the result.
  - A scene with 0 steps cannot be saved.
- **Run.** Steps run **sequentially** with a 4 s timeout each. Live progress shows a ✓/✗ per step with the status code and ms, and a Cancel button. Then a **run report** (plain text): scene name, start time, every step "Device · action · result · ms", and "Ran from this phone over the local network." Reports are saved to history (last 100) and offered as **Copy report**.
- **Home.** Scene buttons are the first thing on Home (M6) and run on tap; long-press opens the editor. Both actions are also on a visible "⋯" button, so nothing is gesture-only. The last run's outcome shows on the button ("2 min ago · 5/5" or "1 failed").
- **No ads** on the editor, the run sheet or the report. **No interstitial** is ever triggered by running a scene.
- **Acceptance:**
  - Unit tests: step JSON round trip, ordering, `stopOnFailure` both ways, wait timing with a fake clock, cancel mid-run, report text, and the history cap of 100.
  - A widget test runs a 3-step scene (WLED + webhook + Roku launch) against `MockClient`, with one step returning 500. It asserts the report says "2 of 3 succeeded", relaunches on the same prefs, and asserts the run is in history.

**M5. Depth: rooms, history with filter, export/import, empty/error/offline states.**
- **Rooms.** Every device has a room (free text with suggestions from rooms already used). Home groups devices by room. Each device row shows a status dot from a real probe on Home open and on pull-to-refresh: "Answered 2 min ago" / "Not answering". The time is persisted, and labelled as the last answer, never "online".
- **History screen** (Settings › History). Scene runs and the session's manual commands (the existing `CommandBus` log, now persisted, capped at 200). Filters: by device, by scene, **Failures only**; text search over scene and device names. Each run opens its report.
- **Export / import setup** (moving to a new phone, or sharing with a housemate).
  - **Copy setup** puts a JSON document (`{"format":"couchdeck-setup","version":1,devices,scenes}`) on the clipboard after the warning "Includes device addresses and webhook URLs. Share only with people in your home."
  - **Paste setup** validates the document, merges by id (incoming wins only if it is newer; `updatedAt` on devices and scenes) and shows "Added 3 devices and 2 scenes, 1 already here".
  - Malformed input → "That isn't a Couchdeck setup." Nothing changes.
- **Forget everything** (Settings), behind a confirmation. It clears devices, scenes and history.
- **Acceptance:** unit tests for the export round trip, merge rules, malformed and wrong-version input, history filters and cap, and status-dot age text. A widget test for **Failures only**.

**M6. Own identity: home layout, onboarding, palette, type, shape, icon, splash, iOS feel.**
- **No bottom tab bar.** The four-tab shell (`app/shell.dart`, `_OmniNavBar`) is removed. **Home** is one scrolling page:
  1. App bar: product name, **Scan**, Settings (gear).
  2. **Scenes**: a 2-column grid of large "keycap" buttons (M4), plus a dashed "New scene" key.
  3. **Rooms**: per-room cards listing devices with status dots. Tapping a Roku opens the Remote, a WLED opens its panel, a webhook offers **Send**.
  4. The single banner ad at the end of the scroll (see Ads).

  Empty Home (no devices) is the setup state, not an empty list: "Couchdeck runs your Roku, WLED lights and home webhooks from one place, over your Wi-Fi.", then **Scan this network** and **Add by IP**.
- **Remote screen design: a physical handset.** Portrait, a bone-coloured "body" with the D-pad as a raised ring. A small **signal LED** at the top blinks signal-orange when a command leaves and turns teal on a 2xx, red on failure. The LED shows the real HTTP outcome, so the metaphor is also the honest status indicator.
- **Palette "Bone & signal".** Hand-built `ColorScheme`, not `fromSeed`, with `ThemeMode.system` (replaces dark-only `app.dart:38`).
  - **Light:** surface `#ECE8DF`, cards/keys `#FAF8F4`, text `#1E1C19`, **primary signal orange `#A8431A`** (on-primary `#FFFFFF`), secondary teal `#2F5D50` (on-secondary `#FFFFFF`; "answered" dots, success LED), danger `#A3161B`, muted `#5C574F`, LED-send `#C8321E`.
  - **Dark:** surface `#141311`, cards/keys `#201E1B`, text `#EEE9E0`, primary `#F28C55` (on-primary `#141311`), teal `#7FB8A6` (on `#141311`), danger `#F2766B`, muted `#A8A196`, LED-send `#FF5A3C`.
  - **Contrast, computed 2026-10-12 with the WCAG relative-luminance formula:**
    - Light: text/surface 13.90, text/card 16.03, on-primary/primary 6.03, primary/surface 4.93, primary/card 5.68, on-secondary/secondary 7.49, danger/card 7.37, muted/surface 5.86, LED/card 5.04.
    - Dark: text/surface 15.36, text/card 13.75, on-primary/primary 7.66, primary/surface 7.66, primary/card 6.86, on-secondary/secondary 8.23, danger/card 6.00, muted/surface 7.25, LED/card 5.37.
    - Assert all ≥ 4.5 in a test with `computeLuminance`.
  - **Uniqueness.** `grep -rliI` of all 16 hexes over `/Users/spatchava/agl` (`*.dart`, `*.md`, excluding the SDK and build output) found none in any app or spec.
  - **Acceptance:** `grep -rhoiE "3B82F6|60A5FA|8B5CF6|A78BFA|F59E0B|FBBF24|F43F5E|FB7185|22C55E|4ADE80|22D3EE|F472B6|EC4899|D97706|1D4ED8|1E1B4B|312E81|4C1D95|7C3AED|080B14|0D1220|0B1020|05070E" mobile/lib` → 0. `OmniColors.backdrop` and the gradient backdrop are removed.
- **Typography.**
  - **Saira** (variable `wdth,wght`) for all UI. Use the condensed width (`FontVariation('wdth', 87.5)`) for key legends and scene names, and normal width for body.
  - **Space Mono** (Regular + Bold) for IP addresses, status codes, ms timings, channel IDs and webhook URLs. This replaces `'monospace'` at `theme.dart:120`.
  - Bundle the fonts under `assets/fonts/` with both `OFL.txt` files and declare them in `pubspec.yaml`. No `google_fonts`, no runtime fetch.
  - Sources verified 2026-10-12 with curl: `github.com/google/fonts/raw/main/ofl/saira/Saira%5Bwdth,wght%5D.ttf` 200 (483,700 B), `ofl/saira/OFL.txt` 200 (4,386 B), `ofl/spacemono/SpaceMono-Regular.ttf` 200 (99,356 B), `SpaceMono-Bold.ttf` 200 (98,232 B), `ofl/spacemono/OFL.txt` 200 (4,392 B).
  - `grep -rlI "Saira"` and `"Space Mono"` over `/Users/spatchava/agl` (`*.dart`, `*.md`, `pubspec.yaml`) returned nothing.
- **Shape language: "keycaps".**
  - Keys and scene buttons use a **10 px** radius, a 1 px top highlight and a 3 px darker bottom bevel (a pressed state removes the bevel and shifts 2 px). Reuse the existing `tactile.dart` press physics.
  - Cards, sheets and fields use **6 px** corners. No 12/13/16/20/26 px.
  - Acceptance: `grep -rnE "circular\((11|12|13|14|16|20|26)\)|OmniRadius" mobile/lib` → 0.
- **Onboarding** (3 pages, shown once, Skip on each, re-openable from Settings › "How Couchdeck works"):
  1. "Your remote, your lights, one place". It works with Roku TVs and players, WLED light strips and webhooks.
  2. "Stays on your Wi-Fi". It talks to your devices directly: no account, no cloud, nothing to sign up for.
  3. "Make a scene". One tap can dim the lights, start your channel and trigger your hub.

  Final button: **Scan this network**. No "Get started", "Welcome" or sign-in. Drawings are `CustomPainter` line art in the palette.
- **iOS feel.** On iOS: `CupertinoPageTransitionsBuilder`, `CupertinoIcons` for app-bar and navigation actions, `.adaptive` switches and dialogs, `CupertinoSlidingSegmentedControl` for the WLED Colour/White/Effects switch. Material stays on Android. Acceptance: `grep -rc CupertinoIcons mobile/lib` totals ≥ 6, and a test asserts the iOS page-transition builder.
- **Icon.**
  - Hand-built, flat, no gradient: a bone-coloured remote seen from above with a D-pad ring and one signal-orange LED dot, on `#141311`.
  - **Not from a generator.** Ask store-compliance to delete `generate_app_icons.py:75` and `generate_launcher_icon.py:42` (in `agl-manifest`, not this repo) so a rerun cannot overwrite it.
  - Regenerate every `AppIcon.appiconset` size and the Android mipmaps.
- **Splash.** A new `LaunchScreen.storyboard`: background `#141311` and the mark. Android `launch_background.xml` matches. Replace `LaunchImage.imageset`. Acceptance: shasum ≠ `3f6a9b27d80dda327ce7df82d4887e3adbac50e4`.
- **Ads.**
  - **Exactly one `AglAdBanner`**, at the end of the Home scroll. The Lights banner (`lights_page.dart:93`) goes.
  - None on onboarding, scan, Remote, WLED panel, scene editor, run sheet, report or Settings.
  - **Interstitial:** the tab-switch call (`shell.dart:55`) goes with the shell. Until the founder answers Q3, call `AglAds.onTransition()` **only** when the user closes the scene editor back to Home. Never from the Remote, the WLED panel or a scene run.
  - Acceptance: `grep -rn "AglAdBanner(" mobile/lib` → 1 hit and `grep -rn "onTransition" mobile/lib` → 1 hit. `ads_placement_test.dart` is updated, not deleted, and asserts no banner on Remote, WLED panel and run sheet.
- **Names.** `kAppName` (`app.dart:16`), `CFBundleDisplayName` (`Info.plist:10`), `android:label` (`AndroidManifest.xml:3`), `MaterialApp.title` and the pubspec `description` all come from one value.
  - Rename the internal `OmniControlApp`/`Omni*` identifiers.
  - **The visible name stays "iPlantPulse" until the founder answers Q1.** The copy in this spec uses "Couchdeck" as the working name; the developer substitutes `kAppName` everywhere it appears, so no string hard-codes a name.
  - A test reads `Info.plist` and asserts the display name equals `kAppName`.

**M7. Settings and copy that belong to this app.**

Settings, in this order:
- **Devices**: list, edit, room, remove, re-check.
- **Scan this network**.
- **History** (M5).
- **Setup**: Copy setup, Paste setup.
- **Feel**: Haptic feedback (existing).
- **What leaves this phone**: rewritten. "Commands go from this phone straight to the devices and webhook addresses you added. Couchdeck has no server and no account. If the app crashes, a crash report (stack trace, device model, OS version) goes to Firebase Crashlytics. Ads come from Google AdMob, which may use device identifiers to serve and measure them, subject to your consent where the law requires it."
- **Privacy choices**: UMP row kept as is; legally required.
- **How Couchdeck works**.
- **Forget everything**.
- **About**: name, version, "American Group LLC".

No "Get started", "Your data", "Nothing saved yet" or other shared portfolio copy. Every new string goes into all 12 ARB files with real translations, because `l10n_test.dart:107,122` enforces it and the test is not weakened.

**M8. Proven.**
- `flutter analyze` is clean and `flutter test` passes, with the count reported against the baseline of 367. The gamepad/simulator tests removed with their code are listed in the commit.
- **New tests:** everything under M1–M7 acceptance, plus:
  - an identity test: fonts declared and present on disk, no `google_fonts`, palette contrast, storyboard shasum, display name = `kAppName`;
  - a source-grep test for the M1 banned strings and the M6 banned hexes and radii.
- **Tests that change:**
  - `transport_test.dart` and `command_rollback_test.dart` (new transports);
  - `home_page_test.dart`, `lights_page_test.dart` (now the WLED panel) and `tv_remote_page_test.dart` (capability gating);
  - `ads_placement_test.dart`;
  - `foldable_layout_test.dart` and `app_smoke_test.dart`, rewritten for Home, Remote, WLED panel, scene editor and Settings at the same sizes and text scales they test now;
  - `l10n_test.dart` (unchanged rules, new screens).
- **Look at it.**
  - Launch on the iOS simulator from a fresh install and screenshot: onboarding page 1, empty Home, scan in progress, nothing-found, Remote, WLED panel, scene editor, run sheet mid-run, report, History with **Failures only**, dark mode. No white screen and no overflow.
  - **Local harness for development only.** A script under `mobile/tool/lan_harness.py`, **not bundled and not used for store screenshots**, answers `127.0.0.1:8060` with the Roku doc's sample device-info and `127.0.0.1:8080` with the WLED doc's sample `/json`, and logs every request. Use it to prove that taps send the exact requests (quote the log in the commit message).
  - Repeat one Remote key and one WLED change on the Android emulator via `10.0.2.2` to prove cleartext works.
- **Real hardware is a human step.** A run against a real Roku and a real WLED is **not verified** until someone with the hardware does it (Q2).
- **Commit and push.** Commit path-limited: never `fastlane/`, never `Podfile.lock` while it carries the other edit. Push to `main`. `integration_test/store_screenshots_test.dart` drives the game pad and simulator today; update it to the new flow, or state in the commit that it was not updated.

### SHOULD (if time allows, in this order)

- **S1. Philips Hue bridge** (local API): `POST /api {"devicetype":"couchdeck#iphone"}` after the user presses the bridge's link button, then `PUT /api/<username>/lights/<id>/state`. Verified 2026-10-12 in `developers.meethue.com/develop/get-started-2/` (200). Discovery via `https://discovery.meethue.com/` (keyless; curl → 200, `[]` from this network). Plus manual IP. Whether the bridge needs HTTPS with a self-signed certificate is **not verified**; any certificate exception must be pinned to that bridge's IP, never global. Hue steps then join scenes.
- **S2. Installed Roku channels.** Try `GET /query/apps`. If it answers with parseable XML, offer a picker of installed channels with icons from `query/icon/<id>` (documented) for `rokuLaunch` steps. Otherwise keep typed IDs, with no message implying failure. `query/apps` is not in today's doc, so it must never be required.
- **S3. Now playing.** `GET query/media-player` on the Remote header: state and position, as reported.
- **S4. Siri Shortcuts / home-screen widget to run a scene.** Needs a native extension/plugin. Same Podfile.lock rule.

## 5. Store impact (proposed; store-compliance applies it later. Nothing was written to `store/` or `fastlane/`)

**Name (founder decision Q1).**
- "iPlantPulse" misdescribes the product, which risks 2.3.7 / 2.3 accurate metadata on top of 4.3.
- Working name **"Couchdeck"**, store name **"Couchdeck: TV & Light Scenes"** (28 chars).
- An iTunes Search for "couchdeck" (2026-10-12) returned only furniture and unrelated apps, no app of that name. **App Store Connect name availability is not checked.**
- Do not put "Roku" in the name, subtitle or icon (third-party mark, 5.2.1). Use "Works with Roku TV and Roku streaming players" in the description only, as nominative use.
- Bundle id and package stay `com.americangroupllc.plantpulse` (`status.csv`). Only the display name changes, so no store record breaks.

**Category.** Primary `UTILITIES` (unchanged), or `LIFESTYLE`, where Apple Home, Hue and Home Assistant usually list. The office has not verified those apps' categories. Recommend `LIFESTYLE` primary, `UTILITIES` secondary. Founder or store-compliance confirms.

**Subtitle (≤30):** `Your TV and lights, one tap` (27)

**Play short description (≤80):** `TV remote, LED-strip control and one-tap scenes that run on your own Wi-Fi.` (75)

**Promotional text (≤170):** `Movie night in one tap: the TV goes to your channel, the LED strip dims to amber and your Home Assistant automation runs, straight over your Wi-Fi.` (147)

**Description.** Draft. No ALL-CAPS headings, no opening "<Name> is…", no simulator paragraph:
> Make a scene once and run it with one tap: the LED strip behind the TV fades to amber, the shelf lights drop to 40%, your Home Assistant closes the blinds, and the TV opens the channel you picked. Each step goes from your phone straight to the device on your Wi-Fi, and you see exactly which steps worked.
>
> Works with Roku TV and Roku streaming players (turn on "Control by mobile apps" in the Roku's advanced system settings), WLED light controllers, and any webhook — Home Assistant, Node-RED or your own server.
>
> The remote shows only the buttons your Roku supports and lets you type into search with your phone's keyboard. The light panel reads each WLED's real state, lists its own effects and presets, and can fade the lights off on a timer.
>
> Find devices with one scan of your network, group them by room, and keep a history of every scene run. Copy your setup to move it to a new phone.
>
> No account, no cloud, no subscription. Couchdeck shows one Google AdMob banner at the bottom of the home screen, never on the remote or the light controls. Where the law requires it you choose about ad personalisation first, and you can change it in Settings. Crash reports never contain your device addresses or webhook URLs.

The crash-report claim needs a check by the developer: `AglCrash` must not attach breadcrumbs containing URLs. **Not verified**; drop the sentence if it can't be confirmed.

**Keywords (≤100):** `remote,scenes,wled,led strip,home assistant,webhook,tv remote,local,no account,lights` (85)

**Screenshots to retake.** **These need real hardware (Q2). Never the dev harness, which would show devices that don't exist.** iPhone 6.9", iPad 13", Play phone/tablet:
1. Home with three scene keys and two rooms, real devices.
2. A scene run sheet with every step ✓ and its timings.
3. The scene editor across Roku + WLED + webhook steps.
4. The Remote with the signal LED.
5. The WLED panel with the device's own effect list.

If no hardware is available, do not ship screenshots of empty states as the product. Hold submission instead. The current fastlane screenshots carry someone else's uncommitted edits; coordinate with their owner.

**Play feature graphic.** Rebuild from the new icon and a Saira wordmark on `#141311`, replacing "OC" / "PlantPulse" and the truncated subtitle.

**Review notes** (rewrite for this app only; drop the "2. DEVICES…" skeleton, the simulator paragraph and the "a build that cannot start never ships" line):
- **What it is and for whom:** "Couchdeck controls a Roku TV or player and WLED LED lights on the user's own Wi-Fi, and runs one-tap scenes across them and Home Assistant/Node-RED webhooks. For people who already own this hardware and want one app instead of three, with no account or cloud." This replaces the pasted subtitle.
- **Hardware dependency, stated plainly:** "The app needs a Roku device and/or a WLED controller on the same network. A screen recording on a physical iPhone with real devices is attached." That recording is a human step, Q2.
  - Also: "Without hardware you can still see every screen except the controls: onboarding, the network scan, add-by-IP, a webhook device (any reachable URL works, for example a local Home Assistant), the scene editor and History."
- **Nothing hidden:** "No login, no hidden, remote-switched, date- or region-dependent features. Every feature is reachable from Home or Settings."
- **External services:** the user's own devices and webhook URLs; Firebase Crashlytics (crash reports); Google AdMob (one banner, plus an interstitial only when leaving the scene editor, pending Q3; UMP consent; no ATT prompt). Firebase Analytics and Performance are linked through a shared library but deactivated and never started. No server of ours.
- **Local Network permission:** asked when the user taps Scan, after an explainer screen.
- **Test devices:** list only devices actually used. A physical-device run is **not verified** here.

**Privacy label.** Give the app **its own** label instead of the shared 20-app one:
- `DEVICE_ID` and `ADVERTISING_DATA` (third-party advertising, not linked);
- `CRASH_DATA` (app functionality, not linked);
- **remove `PRODUCT_INTERACTION/ANALYTICS` and `PERFORMANCE_DATA`.** Both are deactivated (`Info.plist:310-313`, `AndroidManifest.xml:43,46`) and `AglInsights.init` is not called (`main.dart:22-28`).

Device names, IPs, scenes and webhook URLs stay on the phone and are not collected. Exported setups are user-initiated clipboard text, not collection.

**differentiation (store json):**
- §1: the new screens.
- §2: the user paragraph from §2 of this spec.
- §3: the competitor table and its "descriptions only" caveat. The gap is the cross-brand scenes without a server.
- §6: "Not a feature of any other utility in the account. None of them controls devices."
- §4 beta and §9 client stay founder items.

## 6. Out of scope

- Samsung, LG, Sony, Android TV / Google TV, Fire TV, Apple TV control (pairing handshakes or undocumented protocols), and IR blasting.
- SSDP/mDNS multicast discovery (needs Apple's multicast entitlement, a founder credentials step).
- Any cloud relay, remote access from outside the home, accounts, Supabase.
- Game controller emulation of any kind.
- Schedules and automations that run while the app is closed (that is the hub's job; webhooks call into it).
- Plant care, in any form, unless the founder picks the alternative in Q1.

## 7. Not verified

- Every behaviour against **real** Roku or WLED hardware. There is none on this network, so the office can only test against doc-sample fixtures and the dev harness.
- The Roku HTTP status when Control by mobile apps is off (the spec handles 401/403 generically).
- `query/apps` (absent from today's Roku doc); Hue HTTPS/certificate behaviour (S1).
- Android cleartext to LAN through `dart:io`, and whether INTERNET reaches the release manifest today only via AdMob's merge. M2 adds both explicitly and requires an emulator check.
- That iOS ATS does not affect `dart:io` sockets. `NSAllowsLocalNetworking` is added anyway.
- Competitor behaviour beyond App Store descriptions; WebSearch and WebFetch were unavailable. Apple Home's support for these devices.
- App Store Connect availability of "Couchdeck"; the categories of the comparison apps.
- Whether Apple accepts a hardware-dependent app on a video, and any resubmission outcome.

## 8. Founder questions (Charter decisions; the office does not take them)

- **Q1. Name and direction.** "iPlantPulse" says plants; the app is a TV and light remote. Options:
  - (a) rename to "Couchdeck: TV & Light Scenes" (recommended; availability not checked);
  - (b) another name;
  - (c) keep the name and rebuild as a plant-care app. That throws away all of this code and enters another crowded category (Planta, Greg; **competitors not verified**). It is effectively a new product (Charter §8).
- **Q2. Hardware for proof.** Real screenshots, the review video and QA all need a Roku device and a WLED controller (for example an ESP32 with an LED strip). Buying them is money (Charter §3). Without them the app cannot honestly be shown working, and submission should wait.
- **Q3. Interstitial ads.** Today an interstitial can fire on every tab switch, including onto the remote. The spec keeps one trigger only (closing the scene editor). Should interstitials go entirely from a remote-control app? This affects revenue (Charter §3).
- **Q4. Dropping the game pad and the generic hub contract.** The portfolio brief listed "gamepad" and `http_hub_transport.dart` under what this app must own. This spec removes the game pad (no real protocol) and replaces the invented hub contract with webhooks, with existing hub URLs migrated. Confirm.
- **Q5. Submission and Apple contact.** Resubmission and any review-notes reply remain frozen under the 5.6 hold (MA-043, Charter §1).
- **Q6. Beta statement.** differentiation §4 needs a true account of testing. Only you can give it.
