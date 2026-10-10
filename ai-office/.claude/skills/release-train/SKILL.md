---
name: release-train
description: "Get apps from code to TestFlight and Play internal testing through every gate, and prove they arrived. Use for release day or after a batch of fixes."
---

1. Gate (release-manager): `python3 scripts/preflight_version_codes.py --check`
   (`--bump` + commit if behind Play); `python3 scripts/apple_requirements.py`.
2. Build and deliver: `gh workflow run ship.yml -R AmericanGroupLLC/agl-manifest`
   (default stops at internal testing), or locally
   `python3 scripts/testflight/transporter_upload.py --build <apps>` — its
   pre-flight refuses IPAs without UIScene, purpose strings or document config.
3. Watch: `gh run watch <id> --exit-status`; on failure read `--log-failed`,
   fix, re-run.
4. Prove arrival: `bundle exec ruby scripts/testflight/check_build.rb <bundle> <build>`
   until `VALID`; Play: `python3 scripts/play_version_codes.py`.
5. Report per app (iOS and Android separately). Submission for review is a
   founder decision and is blocked while the 5.6 freeze is on.
