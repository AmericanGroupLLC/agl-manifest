# Uscis-Case — M9 "look at it", 2026-10-14

Simulator `agl-qa-iphone-4`: iPhone 17 Pro Max, iOS 27.0. App at **5a50564**. The only change is the
drive's opt-in `M9_SHOTS` frames; the store run is unchanged. Fresh install, debug,
`--dart-define=SCREENSHOT=true --dart-define=M9_SHOTS=true` →
`flutter: 02:45 +2: All tests passed!` (`drive.log`). Everything on screen was typed through
the UI in this run (receipt, two cards, resident-since date, two trips, two statuses, the
posted processing time). Frames 1320×2868, each looked at:

| File | What it shows |
| --- | --- |
| 01_docket.png | Docket "Today Oct 14, 2026"; Now open: Remove conditions (I-751), Ana, 52 days left; Next 90 days: Renew work permit (I-765), Luis, opens in 60 days; Cases 1 tracked; non-affiliation card |
| 02_window_detail.png | **Window detail with its uscis.gov quote**: I-751 window Sep 6 – Dec 5, 2026, "You must file your Form I-751 during the 90-day period immediately before your conditional residence expires.", https://www.uscis.gov/i-751, "Quote checked on Oct 14, 2026" |
| 03_citizenship_clock.png | **Citizenship clock with two trips, one flagged**: earliest N-400 filing date Jan 18, 2027, physical presence 1504 of 913 days; Lisbon 13 days; Manila 219 days "More than 6 months: may break continuous residence" |
| m9_04a_plan_trip_before.png | **Plan a trip, before**: both dates empty, "Pick both dates to see the effect." |
| 04_plan_trip.png | **Plan a trip, after**: Nov 13, 2026 – Jun 11, 2027; presence 1504 → 1439 / 913; "This trip would be flagged: More than 6 months" |
| 05_case.png | **Case with status log and processing-time bar**: IOE 092 551 4876; "Case Is Being Actively Reviewed" 61 days so far; "Case Was Received" 145 days in this stage; "Month 7 of 6.5 — posted by USCIS for Potomac Service Center"; Federal Register list below |
| 06_federal_register.png | Federal Register: Form I-765, paperwork notices hidden, live documents (May 29, 2026 Lebanon TPS …) |
| m9_docket_rtl_ar.png | **Arabic (RTL) Docket**: whole layout mirrored, headings, groups and chips in Arabic. The non-affiliation card stays in English (minor: not translated) |
| m9_docket_text_200.png | **Docket at 200% system text**: rows reflow (title wraps to three lines, chips grow), no overflow stripes |

Unit suite at 5a50564: `flutter analyze` → No issues found; `flutter test` → `00:32 +280: All tests passed!`.

Note on the run: the first attempt's nine frames were all the launch image, because a camera
permission alert left over from an earlier GroceryMatch run sat on top of every app. After
rebooting the simulator, all nine frames show the app (these files).
