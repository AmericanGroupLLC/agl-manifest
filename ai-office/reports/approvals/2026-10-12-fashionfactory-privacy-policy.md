# Approval: Fashion Factory privacy policy for 3.0.0 (size & returns)

- **Decision needed:** approve the replacement text below for `FashionFactory/docs/privacy-policy.html` (and the published page `https://www.americangroup.ai/policy/fashionfactory/`). Founder question 6 in `projects/real-apps/specs/FashionFactory.md`. Charter §6 (legal text).
- **Why now:** the 3.0.0 code (FashionFactory commit listed in the developer report) stores orders instead of a saved-products list, schedules local reminders, and adds one Android permission. The current policy describes the 2.x price-comparison app. `test/security/privacy_policy_test.dart` pins the policy to the code and fails 3 tests until the page matches: `every persisted key is documented on the page`, `the page documents no key the app does not actually store`, `Android requests only INTERNET, as the policy states`. Those assertions were deliberately left in place (spec M6). The release is blocked on this approval.
- **Exact action:** reply "approve FashionFactory policy" (or edit the wording). The office then applies it to `docs/privacy-policy.html` in the app repo and regenerates/deploys the website page, re-runs `flutter test`, and pushes.
- **Correction (2026-10-13, software-developer):** the earlier line "expected: all pass" was wrong, as QA found. Applying the page alone still fails `Android requests only INTERNET` (it hard-codes `{'INTERNET'}`), and would add failures in tests that assert the old gateway host and affiliate wording. The policy and the coupled assertions must change in one commit. That commit is prepared, **not pushed**: local branch `pending/privacy-policy-3.0.0` (commit `efb379d`) in `/Users/spatchava/agl/FashionFactory`, and the same change as `2026-10-13-fashionfactory-privacy-policy.patch` next to this file (`git apply --check` on main f087bd7: clean). On that branch `flutter analyze` printed "No issues found!" and `flutter test` printed "+460: All tests passed!". Wording it adds beyond the draft, for the founder to see: header subtitle "Your clothing orders, sizes and return dates" (was "Fashion, bags & footwear deals"); the orders row also names the exchanged-from link; "Settings → Return reminders → Off" (the UI's real label, not "Reminder timing"); "Settings → Delete all data removes your orders, your settings and any scheduled reminders" (it does not clear Google's consent keys, so "does the same" was dropped). The "Effective 12 October 2026" date is unchanged in the patch; set it to the publication date when applying.
- **Evidence:** facts below come from the code as committed: `lib/data/shared_preferences_store.dart` (keys), `android/app/src/main/AndroidManifest.xml` (permissions), `pubspec.yaml` (dependencies), `lib/ui/app.dart` (the only hardcoded host). `flutter_local_notifications` 22.x merges `POST_NOTIFICATIONS` and `VIBRATE` from its own manifest (`~/.pub-cache/hosted/pub.dev/flutter_local_notifications-22.1.0/android/src/main/AndroidManifest.xml`).
- **Risks / undo:** text only; revert the commit / redeploy the previous page.

## Proposed changes (section by section)

**Lead paragraph** — replace "The handful of things the app remembers — your saved items, your alert switches and the category you last chose — stay on your device" with:
> Everything you enter — your orders, their sizes, prices, return dates and whether you kept them — stays on your device and is not sent to us. Return reminders are scheduled on your device too.

**"What the app stores on your device"** — replace the three-row table and the `styleradar.v1.` paragraph with:

| What | Why | Stored as |
|---|---|---|
| Your orders | So your size at each brand, and every return-by date, survive closing the app | `fashionfactory.orders.v1` — for each order: brand, category, size as typed (and shoe size system), optional cut note, store, optional product link, optional price and currency, order date, return-by date, kept / returned / exchanged and the reason, and the date you recorded it |
| Your settings | So the app remembers your choices | `fashionfactory.settings.v1` — whether the introduction was shown, reminder timing (3 days, 1 day or off), default currency, and whether the reminder permission has been asked |
| Scheduled reminders | To remind you before a return window closes | Held by your phone's own notification scheduler (not by the app's storage): at most two per order, cancelled when you record a verdict or delete the order |

> Earlier versions stored a saved-products list, alert switches and a category under keys beginning `fashionfactory.v2.` and `styleradar.v1.`. Version 3.0.0 deletes those keys the first time it opens; nothing is carried across.

Keep the paragraphs "None of it identifies you…" and the `IABTCF_` paragraph unchanged.

**"What the app never does"** — replace the component list with:
> The app's entire set of third-party components is: a local-storage plugin, a local-notifications plugin with its time-zone database, a component that opens links in your browser, a component that opens your phone's share sheet, a component that opens the app's page in system settings, an icon font, and Google's Mobile Ads SDK…

(the rest of that bullet unchanged).

**"Advertising"** — replace the first paragraph's placement sentence with:
> Fashion Factory shows ads from Google AdMob: one banner at the end of the home screen and one at the end of a brand page. There are no full-screen ads, and no ads on the order form or in Settings.

and "a **Privacy choices** row on the Profile screen" → "a **Privacy choices** row in Settings, always visible".

**"Affiliate links"** — delete the section (the app no longer links to products it lists; it has no affiliate tags).

**"Network activity"** — replace with:
> Fashion Factory's own features make no network requests: orders, sizes and reminders never leave your device. The only network activity is the Google ads described above.
>
> If you paste a product link into an order, the store's name is recognised from the link's address on your device; the page is never requested. Tapping **Open** on a saved link, or **Privacy policy** in Settings, hands that address to your own browser and leaves Fashion Factory. From that point you are on that website, under its privacy policy.
>
> The app refuses unencrypted connections outright.

**"Permissions"** — replace with:
> On Android the app requests `INTERNET` (used only by the ads above) and `RECEIVE_BOOT_COMPLETED` (so your return reminders are put back after the phone restarts). The notifications component adds `POST_NOTIFICATIONS` — on Android 13 and later you are asked, once, when you first save an order with a return date — and `VIBRATE`. Google's Mobile Ads SDK adds permissions granted without a prompt, including `ACCESS_NETWORK_STATE` and Android's ad-services permissions; the advertising-ID permission (`AD_ID`) is removed. On iOS the app asks only for permission to show notifications, at the same moment, and never shows the tracking prompt. No location, camera, contacts, storage, microphone or phone permissions.

**"Children"** — "a shopping-comparison app" → "an app for keeping track of your own clothing orders".

**"Your choices and your data"** — replace the first two bullets with:
> - **Delete an order** — Delete on the order removes it and its reminders.
> - **Turn reminders off** — Settings → Reminder timing → Off, or in your phone's notification settings.
> - **Export or share** — Settings → Export orders (CSV) and Share my sizes hand a file or text to your share sheet; you choose where it goes.

and in "Delete everything": "removes all three stored values" → "removes your orders, your settings and any scheduled reminders"; add "Settings → Delete all data does the same without uninstalling."

**HTML comment at the top** — update the checked facts list to the 3.0.0 dependencies, the two permissions and the two keys.
