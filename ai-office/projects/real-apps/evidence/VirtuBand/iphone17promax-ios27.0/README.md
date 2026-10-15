# VirtuBand — M9 simulator evidence, 2026-10-14

Simulator `agl-qa-iphone-4`: iPhone 17 Pro Max, iOS 27.0. Microphone granted before install
(`scripts/sim_permissions.py` `grant`). App at **0fc1faa9**. The only change is the drive's
per-frame wait for the bounce dialog. Fresh install, debug,
`--dart-define=SCREENSHOT=true --dart-define=VB_DEV_SHOTS=true` →
`flutter: 01:27 +2: All tests passed!` (`drive.log`). Song typed in the run: "Amazing Grace"
(public domain), G major, 92 BPM. Each frame looked at:

| File | What it shows |
| --- | --- |
| 06_library_search.png | **Library**: Songs, search "Em", filters All / Has takes / No chords yet, "Recently edited", Amazing Grace · Key of G · 92 BPM · "2 takes · edited just now" |
| 01_chart_playing.png | **Chart during playback**: bar 2 (D) lit in brass, dock shows Stop, Verse 1 and Chorus with lyrics |
| 03_record_sheet.png | **Record sheet**: "Record a take", start from Chorus, headphones hint, count-in 1-2-3 lit, Stop |
| 04_takes_lane.png | Take 1 and Take 2 (0:06 each), recorded over the band in this run, in the Chorus |
| 05_share.png | Share: the fixed-format chord sheet, Share chord sheet / Copy, "Make demo audio" |
| 07_play_along.png | The piano over the looping band |
| 02_chord_palette.png | The palette for G major, open on bar 8 (D7) |
| dev_demo_progress.png | **Bounce progress**: "Making the demo" dialog with progress bar at 0% and Cancel, caught as it opened |
| host-demo-wav-share-sheet.png | Host `simctl io` screenshot from a run of the same drive (before the wait fix): the bounce finished and the iOS share sheet offers **"Amazing Grace (demo) — WAV · 3.8 MB"** |

Unit suite at 0fc1faa9: `flutter analyze` → No issues found; `flutter test` → `00:31 +307: All tests passed!`.

**Not verified (needs a physical iPhone):** that the band keeps sounding through the count-in and
8+ bars of a take, with and without headphones, and that a take plays back in time with the band.
`xcrun devicectl list devices` on 2026-10-14 lists SrikanthiPhone16ProMaX (00008140-001661C91AC2801C)
and an iPhone 13 Pro as **unavailable** (not connected), so this stays with a person.
