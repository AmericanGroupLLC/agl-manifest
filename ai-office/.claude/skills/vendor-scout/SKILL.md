---
name: vendor-scout
description: "Keep adding vendors — affiliate programmes, data APIs and partners — per app to the vendor registry, from code and from official sources. Use weekly, after feature work, or when the founder names new vendors."
---

Founder standing goal (2026-10-12): "we have to keep adding all the vendors."
The registry is `store/vendors/registry.json` (append-only; never delete — mark
`rejected` with the reason).

1. **Code first** (no web needed): `python3 scripts/api_vendor_audit.py` then
   `python3 scripts/vendor_registry.py --from-code`. This records every vendor an
   app already names (status `in-code`) and which of its keys are empty in release.
2. **Research** (market-researcher, needs web tools): run workflow `vendor-scout`
   (`.claude/workflows/vendor-scout.js`, args `{domains: [...]}` — reuse the seven
   domains in its last run). Each vendor needs its official signup page and an
   independent verify pass; anything unconfirmed is `not verified`, never filled
   from memory. If WebSearch/WebFetch are blocked ("Internet mode is not
   enabled"), stop and say so — do not work around it with curl.
3. **Merge**: save the workflow's returned JSON and run
   `python3 scripts/vendor_registry.py --import-research <file> --label research-<date>`.
4. **Founder-reported states**: when the founder signs up or goes live,
   `python3 scripts/vendor_registry.py --set <App> "<Vendor>" signed-up|live`.
   Signing up is a founder action (Charter §4); credentials never go in the
   registry or the workbook — vault references only.
5. **Publish**: `.venv/bin/python3 scripts/vendor_registry.py --workbook`
   regenerates `AGL_43_App_Vendor_API_Affiliate_Master.measured.xlsx`
   (gitignored), then commit `store/vendors/registry.json` and the docs it reads.
6. Report: new pairs, rejected pairs, and the sign-up list ordered by money
   (affiliate programmes whose links are already in code come first).
