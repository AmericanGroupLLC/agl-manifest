---
name: release-quality-gate
description: "Per-app quality gate every delivery passes before the release train: dead code removed, privacy matched, hardened, listing and creatives ready, independently verified. Use for each app in the current delivery wave (ai-office/projects/release/waves.md)."
---

Founder rule (2026-10-13): every delivery is production quality, with
marketing-grade screenshots and a listing positioned against competitors.
Wave 1 = the apps that ship with AdMob IDs alone (`projects/release/waves.md`).

Per app, in this order — each step pushes its own commits after analyze + tests pass:

1. **code-hygiene** — remove dead code, dependencies, assets, routes, config.
2. **privacy-engineer** — data inventory from the code; label, privacy manifest,
   Data safety answers and policy match it; consent order; no personal data in logs.
3. **appsec-engineer** — no secrets in the binary, obfuscated release build,
   secure storage, ATS/cleartext off, Supabase RLS for the tables the app uses.
4. **aso-specialist** — listing copy against named competitors, within limits,
   only real features and real languages.
5. **store-creative** — captioned, branded screenshots of the real app for every
   size, feature graphic; `screenshot_audit.py` PASS.
6. **qa-reviewer** — independent re-check of 1–5 (default "not done" without
   evidence) plus `flutter analyze` / `flutter test`.
7. **release-manager** — build the IPA/AAB, `python3 scripts/predelivery.py <App>`;
   every ❌ fixed; the founder signs the 👤 device checks; then the release train.

Stop and raise an approval request for anything on the CHARTER list: privacy-policy
text, production database changes, removing a feature or an app, submissions.
