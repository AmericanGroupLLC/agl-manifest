---
name: release-train
description: "Get apps from code to TestFlight and Play internal testing through every gate, and prove they arrived. Use for release day or after a batch of fixes."
---

1. Gate (release-manager): `python3 scripts/preflight_version_codes.py --check`
   (`--bump` + commit if behind Play); `python3 scripts/apple_requirements.py`.
1a. **Only the current wave** (`ai-office/projects/release/waves.md`), and only apps that passed the **release-quality-gate** skill (dead code, privacy, hardening, listing, creatives, independent QA).
1b. **Pre-delivery checklist (mandatory, founder rule 2026-10-12)**: build the IPA
   (`python3 scripts/build_ipa.py <App>`), run `python3 scripts/predelivery.py <App>`,
   fix every ❌, and get every 👤 signed by the person who tested it on a device
   (`--sign <id> --by --device --evidence`). The upload gate refuses an IPA
   without a PASS for that exact file. After upload, `--after-upload` checks
   section 6 (processing, internal group, testers can install, What to Test).
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
