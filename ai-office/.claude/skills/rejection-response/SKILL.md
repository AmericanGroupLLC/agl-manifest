---
name: rejection-response
description: "Handle a new App Store or Google Play rejection end to end — read it, find the root cause, fix the app, verify, draft the reply. Use when a rejection email arrives or store watch reports a new hold."
---

1. **Read** (store-compliance): `bundle exec ruby scripts/testflight/rejection_reasons.rb --session-only`
   (never sign in with a password — that sends 2FA codes) → `python3 scripts/rejection_report.py`.
2. **Classify**: guideline, Apple's exact words, the build/version reviewed.
   5.6 or 4.3 findings are account-level: stop and escalate to the founder.
3. **Root cause** with evidence: reproduce on a simulator (test-engineer) or in
   the artefact Apple inspected (IPA via `privacy_scan.py`, screenshots via
   `asc_screenshots.rb` + `screenshot_audit.py`, live URLs).
4. **Fix** (software-developer / qa-screenshots / web-domains), then make sure a
   check enforces it from now on (`scripts/apple_requirements.py`); add one if
   none exists. ITMS upload warnings ("Although delivery was successful…")
   count as rejections: they get a row too, and anything Apple's upload scan
   decides goes into `transporter_upload.ipa_blocker`, which both upload paths
   (`transporter_upload.py`, and `run_batch.py` that CI uses) refuse on.
4b. **Sweep all 43 apps** with that check (`python3 scripts/apple_requirements.py`)
   and fix every app that fails — not only the one Apple named. Follow
   `docs/REJECTION_PLAYBOOK.md`.
5. **Verify** (qa-reviewer) — re-run the check on the new artefact.
6. **Rebuild and upload** to TestFlight (release-manager) if the binary changed.
7. **Draft the reply** in `store/replies/<App>-<date>.md` — only true statements.
8. Founder approves and sends the reply / submits (CHARTER item 1).
