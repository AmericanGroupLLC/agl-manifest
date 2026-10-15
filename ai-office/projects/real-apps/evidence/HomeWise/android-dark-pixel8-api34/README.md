# HomeWise — Android dark retake (QA M7 must_fix), 2026-10-14

Emulator `Pixel_8_API_34` (Android 14), booted `-read-only` (the shared AVD is not modified),
`adb shell cmd uimode night yes` before the run, and `Night mode: yes` read back after it
(end of `drive.log`). App at HomeWise **f1f332e** (only change: the drive's opt-in
`HW_TYPED_RATE` path). Run: `flutter drive … --dart-define=SCREENSHOT=true
--dart-define=HW_TYPED_RATE=6.875 -d emulator-5580` → `01:04 +2: All tests passed!`.

The emulator has no HTTPS route on this Mac, so the live FRED average cannot load. The drive types a
lender's quote (6.875%) through the app's own "Couldn't reach Freddie Mac's weekly survey" path.
The five screens are the same ones the light run captured.

| File | sha1 | Looked at |
| --- | --- | --- |
| 01_budget.png | 8ac57aa0… | Dark: "You can offer up to $482,700", dimension line, "Your lender's rate: 6.875%", three homes Fits / A stretch / Over budget |
| 02_homes.png | 6d5fe537… | Dark: search, chips All/Fits/Stretch/Over/Toured, "3 of 3 · sorted by room to walk-away price" |
| 03_offer_check.png | c3748abf… | **Dark** (pushed route): "A STRETCH · Asking $505,000", offer up to $482,700, What it takes (extra deposit $11,100 / rate 6.19% / price reduction $22,300) |
| 04_loan.png | 454c0c70… | Dark: "$3,569 per month" ring, principal/interest/tax/insurance/PMI rows |
| 05_compare.png | 330ebba5… | Dark: Homes/Loan setups segment, three homes picked, "3 homes" table |

None of the five equals the old light hashes (29c03826…, fed2a46c…, 24320336… for 03/04/05).
**Conclusion:** Offer Check, Loan and Compare render dark on Android, so there is no Android theme defect.
The earlier `android-dark/03–05` files were byte-identical to the light ones, so they were never
dark captures; most likely files left over from the light run. That cannot be proven
after the fact. The 03 "renders light" finding came from those files, not from the app.

HomeWise unit suite at f1f332e: `flutter analyze` → No issues found; `flutter test` →
`01:47 +330: All tests passed!`.
