# TestFlight delivery, from this machine

One generic lane instead of 40 per-app Fastfiles. Proven 2026-09-13: CalcMaster
4.0.2 (2026091319) and AGCleaner 1.0.0 (2026091320) reached App Store Connect
with processing state VALID.

```sh
source scripts/testflight/env.sh                 # ASC key id / issuer / .p8 path, pinned Flutter, rbenv Ruby
cd scripts/testflight
python3 run_batch.py --wave records              # every app whose bundle id has an ASC record
python3 run_batch.py --apps BodyQuest,ChefCount
bundle exec ruby list_builds.rb com.americangroupllc.calcmaster   # what Apple has
```

What the `ship` lane does per app: App Store provisioning profile via the API
key (`get_provisioning_profile`), manual signing with the "Apple Distribution:
American Group LLC" identity already in the login keychain, `flutter build ipa
--export-method app-store`, `upload_to_testflight`. It rewrites the app's
`ios/Runner.xcodeproj` signing settings (same as CalcMaster's own lane) — do not
commit that churn from the app repos.

Facts about this network that shaped the code:

- altool logs "The network connection was lost … WILL RETRY PART n" on every
  upload and then reports failure — while Apple has usually accepted the build.
  Every attempt is therefore followed by polling App Store Connect for the
  build before retrying, and `run_batch.py` re-checks after any failure.
- Ruby's `Timeout` cannot interrupt a blocked altool; one upload sat for three
  hours. The wall-clock cap is in `run_batch.py` (kills the process group).
- Results: `~/agl/.dist/ios-batch/results.json`; logs: `~/agl/.dist/ios-logs/`.

`create_records.rb` registers missing bundle ids in the Developer Portal. It
**cannot** create App Store Connect app records — the API refuses `CREATE` on
`apps`, and fastlane `produce` needs an Apple ID password. See
`docs/MANUAL_ACTIONS.md` MA-008.
