# RideZap game: M1 evidence (Godot 4.7.2)

Spec: `../../../specs/RideZap-game.md` §8.4 M1 (spec commit `ebd0ad1` on agl-manifest master).
Code: `RideZap` repo, `main` @ `343440232a1d561b965af8e5e704fa13d7331e54` (`game/`, not pushed when this was written).
Machine: this Mac (Apple M1 Max, Xcode 27.1), 2026-10-15, load average between 250 and 675 throughout.
Engine: `~/agl/.tools/godot/4.7.2-stable/editor/Godot.app` (`--version` → `4.7.2.stable.official.ed1daf0bf`).

## M1 scope and status

| M1 item (spec §8.4) | Status |
|---|---|
| Drivable car | Done: custom raycast vehicle on `RigidBody3D` (Pipsqueak stats, Kenney `hatchback-sports` placeholder body) |
| Streamed 2 × 2 km slice | Done: 8 × 8 chunks of 256 m, 3 × 3 active / 5 × 5 preload, ≤ 25 resident; 61 chunk builds in one lap |
| One checkpoint race with lap timing | Done: 1,792 m circuit, 7 gates, laps timed in physics ticks |
| HUD: speed, lap, timer | Done (plus best lap, nitro bar, countdown, missed-checkpoint warning, results panel) |
| Touch controls: steer, throttle/brake, nitro | Done: multi-touch pads → InputMap (same path as keyboard and gamepad) |
| 60 fps target | Desktop only: mean 16.68 ms (see below). **Device not measured** |
| Headless GUT tests for lap timing and checkpoint order | **48/48 pass** (`gut-output.txt`, `gut-junit.xml`) |
| Look at it (desktop frames) | Done: `frames/` |
| iOS simulator | **Blocked** (see below). The Godot iOS export and an x86_64 simulator build succeed; the app cannot be installed on the available simulators |

## Tests

```bash
cd RideZap/game
G=~/agl/.tools/godot/4.7.2-stable/editor/Godot.app/Contents/MacOS/Godot
$G --headless --path . --import
$G --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://test/unit,res://test/smoke \
   -ginclude_subdirs -gexit -gjunit_xml_file=<this dir>/gut-junit.xml
```

Result (`gut-output.txt`): exit 0, `Scripts 9 / Tests 48 / Passing Tests 48 / Asserts 593 / Time 14.147s / All tests passed!`
- `test_checkpoints.gd` 12/12: forward-only crossing, crossing outside the gate, a 1.5 m step (89 m/s), landing exactly on the line counts once, the first start-line crossing starts lap 1, gates in order (a skipped gate gives MISSED and stays expected), a lap needs every gate, lap times in ticks, finish after the last lap, reversing over a gate, sprint = 1 lap, the M1 gates face along the route.
- `test_race_clock.gd` 5/5: ticks/60, no running before start or while paused, `m:ss.cc` truncation, split delta, reset.
- `test_chunk_index.gd` 5/5, `test_world_layout.gd` 6/6, `test_tire_model.gd` 9/9, `test_ip_names.gd` 1/1.
- Smoke: `test_race_scene_smoke.gd` 3/3 (real scene headless: 3 × 3 chunks loaded at spawn, no creep in the countdown, > 5 m forward and > 20 km/h after 2 s of throttle, upright, HUD shows real values, driving over the start line starts lap 1), `test_export_filter.gd` 2/2, `test_touch_controls.gd` 5/5.
- `-gexit` fails the process on a failing test: an earlier run with two failing smoke tests exited 1 (the car reversed during the countdown; fixed in the vehicle's parked state before the commit).

## Frames (`frames/`, 1280 × 720, macOS runtime, mobile renderer, Metal)

Captured with `tools/capture/capture_race.tscn` (not exported): the real `scenes/main.tscn` with `laps = 1`, an autopilot pressing the same InputMap actions the pads press, `--fixed-fps 60`. Two runs gave the same lap time, `1:35.63`, and the same positions at every shot (deterministic physics at a fixed step). Per-shot state is in `frames/stats_frames.json`.

| File | What it shows (read by the game developer) |
|---|---|
| `01_countdown.png` | Behind the green placeholder car on the start straight, "2" countdown in yellow, yellow start/finish arch ahead, street lights both sides, tall low-poly buildings with window grids, trees at the far end. HUD: `LAP 1 / 1`, `0:00.00`, `BEST --:--.--`, speed `0` `MPH` (the macOS locale is en_US, so mph is correct per spec §4.9), full cyan nitro bar; pads ◀ ▶ bottom-left, BRAKE / GAS / NITRO bottom-right as angled panels. |
| `02_go.png` | "GO!" over the arch, timer `0:00.50`, speed 4, GAS pad highlighted (the autopilot is pressing it). |
| `03_start_straight.png` | 7.00 s in, 39 mph (63 km/h per stats), past the start line; a park with cone trees on the left at the next junction, grey office blocks right. |
| `04_first_corner.png` | 13.83 s, at the first crossroad: Kenney crossroad tile with kerbs, a park to the left, buildings receding into the distance fog. |
| `05_mid_lap.png` | 30.00 s on the third straight, park with trees and shadows on the right, the next (yellow) gate visible far ahead. |
| `06_overview_slice.png` | A one-frame high camera over the car at 40 s: the block grid, parks, buildings of varying height, and the loaded 5 × 5 chunk area fading into fog; beyond it the unloaded area is empty grey (expected: those chunks are not built). The HUD stays on top. |
| `07_nitro.png` | 16.65 s, nitro active: NITRO pad lit, the nitro bar draining. |
| `08_results.png` | After the finish: results panel "FINISHED / LAP 1 1:35.63 BEST / TOTAL 1:35.63", `BEST 1:35.63` under the timer, the car rolling to a stop (13 mph). |

What the frames also show, honestly: the car is a stock Kenney model (placeholder until M2's original models); shadowed asphalt and kerbs take a strong blue tint from the sky ambient; the overview is washed out by fog; there are no AI rivals, traffic, audio or minimap yet (not M1 items in this brief).

## Performance (desktop only)

`fps/stats_fps.json`: the same scene **without** `--fixed-fps`, 60 s real time, autopilot driving, 1280 × 720, vsync on, `run/max_fps = 60`:
- frames 3,569; frame time mean **16.68 ms** (≈ 60 fps), p50 16.67, **p95 18.16, p99 19.79**, max 43.3 ms;
- draw calls p50 161, max 191 (budget ≤ 300); primitives p50 98,930, max 123,512 (budget ≤ 300 k).
- **Chunk build time breaks the 2 ms budget:** one chunk takes 15–113 ms on the main thread on this loaded machine (`max_chunk_build_ms`, three runs: 14.99, 59.58, 112.98). The streamer builds at most one preload chunk per frame, but that is not within budget. M2 must move the mesh/transform generation to `WorkerThreadPool` as the spec (§5.3) says.
- These numbers come from an M1 Max under a load average of 466–675, not from a phone. **iPhone 11 / mid-range Android performance is not verified** (R9).

## iOS export and simulator

1. `Godot --headless --path game --export-debug "iOS" ../build/ios/RideZap.ipa` with `application/export_project_only=true` → exit 0, Xcode project `RideZap.xcodeproj`, `RideZap.pck` 631,680 bytes, `PrivacyInfo.xcprivacy` generated (`logs/ios-export-tail.txt`).
2. `xcodebuild … -sdk iphonesimulator ARCHS=arm64` → **BUILD FAILED**: `Undefined symbols for architecture arm64: "_main"`. The linker ignored every object in the simulator `libgodot.a` because they are x86_64.
3. `lipo -info`: the official 4.7.2 templates' simulator slice (`ios-arm64_x86_64-simulator/libgodot.a`, both debug and release, checked from `ios.zip`) is **x86_64 only**, although the folder name says arm64_x86_64.
4. `xcodebuild … ARCHS=x86_64` → **BUILD SUCCEEDED** (`Mach-O 64-bit executable x86_64`).
5. `xcrun simctl install` on two iPhone 17 Pro Max simulators, iOS 26.4 (`C8780642…`) and iOS 26.5 (`17BB409D…`), both booted by this run and shut down afterwards → **"App installation failed: RideZap Needs to Be Updated … Failed to find matching arch for input file"**. These simulator runtimes do not run x86_64 apps.

So no iOS simulator frame exists for M1. The way forward is an arm64 simulator export template built from the 4.7.2 source (`scons platform=ios ios_simulator=yes arch=arm64`), or a device build (needs signing). Neither was attempted: `scons` is not installed and the machine was at load average 500–675. Logged as a risk in the spec.

## Not verified

- Any frame on an iOS simulator or device; any Android build (the Android export and AAB signing were not run: the coordinator asked to keep heavy exports for when the load drops).
- Device frame rate, memory, battery (no iPhone 11 / mid-range Android).
- Store download size: the 94 MB simulator `.app` is an unthinned x86_64 debug build and says nothing about the App Store size.
- Feel of the handling with a human on touch: only the autopilot and the headless tests drove the car.
