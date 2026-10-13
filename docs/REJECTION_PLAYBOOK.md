# Rejection and upload-warning playbook — every app, every time

The founder's rule (2026-10-12): every rejection or warning Apple or Google
sends is handled for **all 43 apps**, not only the one named, and becomes a
check so it cannot come back. This is the checklist. The AI office runs it as
the `rejection-response` skill.

## The checklist (per finding)

1. **Capture it.** App, build number, guideline or ITMS code, Apple's exact
   words. Upload warnings that arrive by email ("Although delivery was
   successful, you may want to correct the following issues…") count — they
   are tomorrow's rejections.
2. **Root cause on the artefact Apple saw** — the IPA (`privacy_scan.py`,
   `ipa_blocker`), the screenshots App Store Connect holds
   (`asc_screenshots.rb` + `screenshot_audit.py`), the live URL — not on a
   guess from source.
3. **Make it a check.** Add or extend a row in `scripts/apple_requirements.py`
   (`REQUIREMENTS`: guideline, Apple's words, apps it was raised against, the
   check function). If Apple's *upload scan* decides it, also make
   `scripts/testflight/transporter_upload.py: ipa_blocker()` refuse it — both
   upload paths call that function, CI included (`run_batch.py --prebuilt`).
4. **Sweep all 43.** `python3 scripts/apple_requirements.py` → every FAIL is
   fixed, in every app, with the honest fix (declare what the app really does;
   strip what it does not use — never a purpose string for a feature the app
   lacks).
5. **Rebuild and re-check the artefact.** `build_ipa.py <App>` then the check
   again on the new IPA. A green source check is not proof.
6. **Upload** to TestFlight / Play internal (office authority). The gate blocks
   anything still failing.
7. **Reply / resubmit** — founder only (Charter §1), and never while a 5.6 hold
   is on (MA-043). Draft replies go in `store/replies/`.
8. **Record** — commit the check and the fixes; the generated
   `docs/APPLE_REQUIREMENTS.md` then lists the finding, Apple's words, and how
   many apps pass.

## Every finding so far

The live, generated list is `docs/APPLE_REQUIREMENTS.md` (one row per finding,
with PASS/FAIL counts across the 43 apps). Do not maintain a copy here.

Added 2026-10-12: **ITMS-90683 — missing purpose string** (CalcMaster, then
MileMaster: `NSLocationAlwaysAndWhenInUseUsageDescription`, because
`geolocator`'s iOS code references `requestAlwaysAuthorization`). Check
`purpose_strings_90683`. Root cause of the repeat: CI uploaded through
`run_batch.py`, which did not run the scan; it now refuses a flagged IPA.
Sweep result the same day: IPAs for MileMaster, AGStudio and AGRecorder, and
the source of iMaps, Kinnav, WiFiTrail and PilotEnRoute, were short a key.

## Upload warnings not received yet — coverage

Known Apple upload-scan warnings, and whether a check exists. A gap here is
work for the office, not something to wait for Apple to email.

| Code | What Apple flags | Check today |
| --- | --- | --- |
| ITMS-90683 | Purpose string missing for an API the binary references | **Yes** — `privacy_scan.py`, `ipa_blocker`, `purpose_strings_90683` |
| ITMS-90737 | Document types declared without `LSSupportsOpeningDocumentsInPlace`/`UISupportsDocumentBrowser` | **Yes** — `upload_scan_plist` |
| ITMS-91053 | Required-reason API used (UserDefaults, file timestamps, system boot time, disk space) without a declared reason in `PrivacyInfo.xcprivacy` | **Partial** — the store checklist only checks the manifest file exists, not the declared reasons |
| ITMS-91061 | Listed third-party SDK shipped without its own privacy manifest/signature | **No** |
| ITMS-90078 | Push used without the `aps-environment` entitlement | **No** |
| ITMS-90725 / SDK minimums | Built with an Xcode/SDK older than Apple's current minimum | **No** (builds use the machine's Xcode) |
