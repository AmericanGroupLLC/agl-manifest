# Approval request — split the pre-delivery checklist into two stages so the pipeline can deliver to TestFlight

Date: 2026-10-14 · Prepared by: release-manager (AI office) · Founder rule of 2026-10-13: "without passing the checklist we can't deliver"

## Decision needed

Change **when** each pre-delivery check is enforced. The checks themselves don't change.

- **Stage A, before TestFlight (internal testers only).** Every automated pre-upload check (20) must PASS (the 8 post-upload checks in section 6 run after the upload, as now) on the exact IPA that is uploaded. CI runs `predelivery.py` on the IPA it just built, and the upload gate checks that IPA's sha256 as it does today.
- **Stage B, before App Store review submission.** The 18 checks only a person can do (1.1–1.6 core journeys, 2.4 prompt timing, 4.2/4.3/4.6 backend and accounts on a device, 5.1–5.7 physical-device testing) are signed against the **TestFlight build number** that was tested. A submission is refused until every Stage B check for that build is PASS or n/a.

## Why now

- Founder priority (2026-10-14): automate the pipeline before reworking apps one by one.
- Today the gate needs all 46 checks, including "5.1 Install and launch the release build on a physical iPhone", **before** the TestFlight upload. That install needs a TestFlight build, so it is circular. CI can never deliver: run 38553467641 uploaded **0**, refused **38** (35 had no checklist, 1 was bound to another IPA, 2 failed ITMS-90683).
- Two stages keep the founder's rule: nothing reaches users (App Store) without every check passing. They also let CI put builds on TestFlight, which is where people test them.

## Exact action

Answer "approve two-stage checklist" (or "no"). The office will then:
1. Change `scripts/predelivery.py` (a `--stage A|B` split and `gate_for_upload` for Stage A) and the submission scripts (`resolve_and_resubmit.rb`, `submit_production.rb`) to refuse any submission without Stage B for that build.
2. Add a predelivery step to `ship.yml` that runs on each CI-built IPA.
3. Prove it with one CI run that uploads to TestFlight internal only.

## Evidence

- Upload gate: `scripts/predelivery.py` `gate_for_upload` (needs a `deliverable` record bound to the IPA sha256). Sections 1–5 are required before upload (`PRE_UPLOAD_SECTIONS`).
- 18 checks are of kind "human" (`grep -c '"human"' scripts/predelivery.py`).
- CI result: the background pipeline report, scheduled run 38553467641, step "TestFlight": `uploaded: 0 failed: 38`.

## Risks / how to undo

- Internal testers could get a build a person hasn't touched yet. They are our own team, and every automated pre-upload check (privacy strings, signing, store-policy FAILs, pre-release SDK) still blocks.
- Undo: put `PRE_UPLOAD_SECTIONS` back to sections 1–5.
