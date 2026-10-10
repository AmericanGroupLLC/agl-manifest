# Release

| Step | Command | Verify |
| --- | --- | --- |
| Version codes ahead of Play | `python3 scripts/play_version_codes.py && python3 scripts/preflight_version_codes.py --check` (`--bump`, then commit the pubspec) | "Every app's build number is already past what Play holds." |
| Full pipeline | `gh workflow run ship.yml -R AmericanGroupLLC/agl-manifest` (stops at internal testing) | `gh run watch <id> --exit-status` |
| One app, locally | `. scripts/testflight/env.sh && python3 scripts/testflight/transporter_upload.py --build <App>` | pre-flight refusal or "uploaded" |
| Arrived at Apple | `bundle exec ruby scripts/testflight/check_build.rb <bundle> <build>` | `PRESENT … VALID` |
| Store state | `bundle exec ruby scripts/asc_build_state.rb` | docs/asc-build-state.json |

Never: submit for review / promote to production (founder; blocked while the 5.6 freeze is on).
