# PilotEnRoute: Clear Skies design, end to end (2026-10-17)

Chain: founder request ("using AI-Office develope this applicaiton end to end
desgisn and make the applicaiton production ready", with the design kit) →
content researchers (4 agents, FAA sources) → independent answer re-check
(4 agents) → software-developer (main session) → qa-reviewer (1 high, 4
medium, 5 low; all addressed) → this report. Decisions: decision-log,
2026-10-17 entries 6-10.

## Shipped — PilotEnRoute master 78b57f5 (pushed)
- The kit's restyle patch, merged onto current master (3 conflicts kept both sides).
- Five tabs: Home · Learn · Practice · Plan · Logbook. Go Card and Weather are
  pushed screens; Kit is now the Plan hub.
- Home: legal-today line (legality engine), 61.109(a) progress, first-try
  practice score, last logged flight. No ad.
- Learn: FAA library (13 documents), six-pack trainer (PHAK 25C ch. 8, 56
  cited lines), airport operations (AIM 2-3 / 4-3, 34 cited lines).
- Practice: 40 FAA PAR sample questions. The FAA publishes no answer key; each
  answer is decided by a verbatim FAA quote (14 CFR, AIM, PHAK, AFH, AWH) and
  4 independent reviewers confirmed all 40 (same letter reached first,
  quote verbatim, cite right). 3 unproven + 18 figure questions left out.
- `content/*.json` (document, edition, URL, sha256) → `tools/gen_content.py`
  → `lib/content/*.g.dart`; a test fails if stale or uncited.

## Evidence (this Mac)
- `flutter analyze`: No issues found. `flutter test`: +932 all passed.
- `tools/verify.sh all`: pub, analyze, test, ios-build, ios-drive (13
  screenshots), android-build, android-launch, android-drive (12) PASS.
  ios-launch failed on a script bug (below), PASS twice after the fix.
- Screenshots looked at: Home, Go Card night window, quiz with FAA quote,
  six-pack, signs, library, practice, plan (build/verify/ios, android).

## QA findings → outcome
| # | Finding | Outcome |
|---|---|---|
| H1 | store_screenshots_test still drove the 4-tab app | rewritten for 5 tabs (not run: needs a fresh install + SCREENSHOT build) |
| M2 | green pill 4.40:1 on its tint | Sky.go #18773F → 4.89:1; tint test added |
| M3 | Home said "Last 40 answers" at 10 | replaced by first-try score |
| M4 | each Go Card visit saved a history record | identical auto checks not saved; test |
| M5 | readiness inflatable; 85–90% / 70% unsourced | first tries only; 70% removed (no FAA source on hand); 85–90% shown as the study-plan goal |
| L6 | result card showed edited airport | shows the checked airports |
| L7 | faint text 2.85:1; diagram label 4.47:1 | muted / inkSoft |
| L8 | ASI arcs look like a C172's | labelled "an example, not any particular airplane's" |
| L9 | generator did not cross-check reviewer letter | now required |
| L10 | Charts About unreachable; dial semantics; library wording | fixed |

Also found while verifying: `tools/verify.sh` used `cmd | grep -q` under
`pipefail` — a running iOS app was reported "not running", and an Android
`FATAL EXCEPTION` could have gone unreported. Fixed.

## Not built (decision-log): study plan, learning path, flashcards, radio
practice, Listen live (LiveATC link unverifiable here), practice flight,
charts/moving map, weather map, NOTAMs (FAA key), endorsements, backup, the
Clear Skies app icon. Hubs show only what exists.

## Not verified
- GitHub CI on 78b57f5: stops at step 1, `AGL_PACKAGES_TOKEN` not set (founder step, unchanged).
- store_screenshots_test was not run.
- The standalone ios-launch screenshot is black (headless simulator capture);
  rendering is proven by the ios-drive screenshots instead.
- The first ios-drive run timed out at the Paste CSV dialog once; the next
  two runs passed. Cause not found.
- Android Go Card live-weather/night steps (emulator has no internet here).
- No release-signed build; no TestFlight upload; no App Review (2026-10-15 hold).
