# Approval: EventSpark ads go to one Home banner, with no interstitial

- **Decision needed:** approve, or decline, the EventSpark ad layout that is now on `main`: **one AdMob banner at the foot of Home and nothing else**. That means no banner on any other screen and no interstitial anywhere. This is Charter §3 (money: it can change ad revenue) and EventSpark spec §8.3 (`projects/real-apps/specs/EventSpark.md`, M5 "Ads").
- **Why now:** this is a must_fix from QA on the Real Apps run (`projects/real-apps/continue/EventSpark.json`). The rebuilt app already ships the layout above (EventSpark `157ee7e3`, pushed). There is no founder record approving it. The old layout belonged to the guest marketplace, which is removed: five tabs, a shell banner on six screens, and an interstitial on tab change. That marketplace was what Apple called a template (4.3 / 4.2.6). The old layout cannot come back as it was, because the tabs no longer exist.
- **Exact action:** reply in issue #40 (https://github.com/AmericanGroupLLC/agl-manifest/issues/40) with one of:
  - **"approve EventSpark Home banner"**: nothing changes. The office records the decision and closes the issue.
  - **"decline EventSpark Home banner"**: the software-developer applies the spec's fallback. An interstitial (through `AglAds.onTransition()`) fires only when the host goes between Home and Settings, never on an event, door, ledger or close-out screen. The Home banner stays. It gets a test, analyze and the full suite, then a path-limited push to EventSpark `main`. This is about an hour of work, and nothing is uploaded or submitted (MA-043).
- **Risks / undo:** either choice can be reversed with one code change. Approving may lower EventSpark's ad impressions compared with the old marketplace layout. I have **no revenue figures** for EventSpark: the app is rejected on the App Store and only a Play draft exists (spec §0, `store/apps/EventSpark.json`). So any revenue effect is **not measured**. Declining puts full-screen ads back into a tool a host uses at the door of a live event. The fallback keeps them off the door screens, but they still interrupt Home ↔ Settings.

## Evidence (EventSpark repo, read and run on 2026-10-14)

| | Before the project (base `cb272a3`) | Now (`main` at `c82b9de5`) |
|---|---|---|
| Banner | `lib/core/router/app_router.dart:237` `if (showsAdBanner(location)) const AglAdBanner()` in the shell's `bottomNavigationBar`. `showsAdBanner` (`:59-64`) returned true on `/`, `/search`, `/nearby`, `/saved`, `/tickets`, `/host` and organiser pages | `lib/features/home/home_screen.dart`: one `const AglAdBanner()` at the end of the Home list, below the events and the search field. `rg -n "AglAdBanner" lib` finds only that line |
| Interstitial | `app_router.dart:248` `if (i != index) AglAds.onTransition();` on every tab change. The `agl_ads` cap is 3 minutes between interstitials (`minInterstitialInterval`) and 2 warm-up transitions (`agl_ads/lib/src/ads.dart:22,26`, ref `d5e5b72`) | none. `rg -n "onTransition" lib` finds nothing |
| Ads SDK and consent | `AglAds.configure` + `initialize` in `main.dart` | unchanged (`lib/main.dart:35-39`). UMP consent and Settings › Privacy choices are kept |
| Guards | none | `test/shell_test.dart:48` (banner only on Home), `:95` (no `AglAds.onTransition` in `lib/`), `:103` (no banner off Home). The full suite passes: `flutter test` gives `00:17 +316: All tests passed!` on 2026-10-14 |

## Not verified
- How either layout affects revenue. There is no EventSpark AdMob traffic to measure.
- Whether the banner fills on a device. Debug builds use Google's test units, and I did not check fill on a physical device.

## Related
- The store copy should say "ads on Home only" if this is approved (spec §6 review notes). store-compliance applies that afterwards. This request does not edit store metadata.
