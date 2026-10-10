# Monetization

- AdMob account pub-8528784688453695; ids in `docs/admob-ids.json`.
- `python3 scripts/admob_setup.py --dry-run` (reads); `--sync` copies real ids. Creating apps/units through the API is refused for this account — founder creates them (MA-047, list in `~/agl/.dist/admob-apps-to-create.csv`).
- Shared package `packages/agl_ads`: consent (UMP) first, test ads only in debug.
- iOS: never ship the AdMob SDK without the app's real `GADApplicationIdentifier` (launch crash).
- `https://www.americangroup.ai/app-ads.txt` is checked by the domain monitor.
