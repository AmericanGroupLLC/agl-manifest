# NexusTransferPay — QA evidence, 2026-10-14 (pushed head 05a3ebe, no code change)

## M8: launch with the network really off (airplane mode)

Device: Android emulator `Pixel_8_API_34` (Android 14), booted `-read-only` so the
shared AVD was not changed. App: `flutter build apk --debug --dart-define=SCREENSHOT=true`
from `flutter-mobile-app/` at 05a3ebe, installed fresh (no previous data).

Airplane mode was switched on **before the first launch**:

```
$ adb shell cmd connectivity airplane-mode enable
$ adb shell settings get global airplane_mode_on   -> 1
$ adb shell cmd connectivity airplane-mode         -> enabled
$ adb shell ping -c1 -W2 8.8.8.8                   -> connect: Network is unreachable
$ adb shell am start -W -n com.americangroupllc.nexustransferpay.debug/com.americangroupllc.nexustransferpay.MainActivity
  Status: ok  LaunchState: COLD  TotalTime: 3728
```

| File | What it shows (looked at) |
| --- | --- |
| `airplane-01-launch-onboarding.png` | Cold launch, airplane icon in the status bar. Onboarding card 1 "Your receipt, decoded" (airmail stripe, receipt with You send / Fee / Rate you got / Reference rate / Margin / They get). No error page. |
| `airplane-02-ledger.png` | After Skip: Ledger home. "Offline · showing what's saved on this phone", the airmail "Check a transfer" card and the empty state "No transfers yet. Check a quote before you send, or add a past transfer from its receipt." No error page. |
| `airplane-03-check-result.png` | Check a transfer with USD 500, fee 3.99, they get INR 47,300, today. The result prices what needs no network ("You got 93.8511 INR per USD", "The fee is 0.79% of what you paid") and says "The ECB reference rate didn't load. Try again." with Retry. The offline banner stays at the top. |

The earlier o01/o02 frames (HttpOverrides pointed at a closed port) are superseded by these.

## M1(c): release-binary strings check

`flutter build ios --release --no-codesign` at 05a3ebe (DEVELOPER_DIR = Xcode_27.1.0):
`✓ Built build/ios/iphoneos/Runner.app (33.5MB)`. App.framework/App sha1
`b2c11c54d67a12c0b1be2defd653549fc824424c`. Then `sh tool/release_strings_check.sh`:

```
spec literal (grep -ciE): 1
  hit: Naskenovat text
whole word (grep -ciwE): 0
other removed names (NexusPay, Get Started, AI Assistant, kIsDemoMode, API_BASE_URL, SENTRY_DSN): 0
exit=0
```

**Result recorded: whole-word count 0.** The spec's literal (non-word) command returns 1,
and the only hit is `Naskenovat text`. That is Flutter's own Czech Material label for "Scan text"
(`scanTextButtonLabel` in flutter_localizations, `material_cs.arb`), where "Nova" is part
of the word "Naskenovat". No code in `lib/` produces it, and removing it would mean dropping Czech
framework localisation. Every name from the deleted account product has 0 hits, whole-word or not.
`strings App | grep -ciE "NexusPay|not connected|Service Unavailable|Demo|Get Started|AI Assistant"` → 0.

## Hosts

`scripts/verify_api_hosts.py` was **not run**: it always rewrites `docs/api-hosts.json`, and
that file has someone else's uncommitted edits. The app's three hosts were checked by hand
instead (`grep -rhoE "https://[a-zA-Z0-9.-]+" lib`):
- `api.frankfurter.dev`: `/v1/2026-09-15?base=USD&symbols=INR` → `{"date":"2026-09-15","rates":{"INR":95.96}}`
- `api.worldbank.org`: `/v2/country/IND/indicator/SI.RMT.COST.IB.ZS?format=json` → data, lastupdated 2026-10-08
- `www.americangroup.ai` → HTTP 200
