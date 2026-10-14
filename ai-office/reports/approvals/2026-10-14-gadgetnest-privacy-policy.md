# Approval: GadgetNest privacy policy must match the app that ships (AdMob, Crashlytics, local reminders)

- **Decision needed:** approve (or edit) the replacement text below for the GadgetNest privacy policy at `https://www.americangroup.ai/policy/gadgetnest/privacy.html` (source: `americangroup.ai/client/public/policy/gadgetnest/privacy.html` and the byte-identical `index.html`). This is Charter §6 (legal text).
- **Why now:** this is a must_fix from QA on the Real Apps run (`projects/real-apps/continue/GadgetNest.json`; spec `projects/real-apps/specs/GadgetNest.md` §7). The live page says the app shows no ads, sends no crash reports and declares only the INTERNET permission. The app on GadgetNest `main` ships Google AdMob, Firebase Crashlytics and, on Android, POST_NOTIFICATIONS and RECEIVE_BOOT_COMPLETED for local reminders. The policy has to match the binary before any resubmission.
- **This does not unblock resubmission on its own.** Founder question 1 (pivot / merge / retire, issue #25, Charter §8) is still unanswered. The pivot code is already on `main`, but nothing goes back to the stores until #25 is answered, and Apple submissions are frozen anyway (MA-043). If #25 ends in retire or merge, this text is not needed.
- **Exact action:** reply "approve GadgetNest policy" in the issue, or edit the wording here. The office will then edit `client/public/policy/gadgetnest/privacy.html` and `index.html` in `americangroup.ai`, deploy the site the usual way (push to main, never `--delete`) and check the live page with curl.
- **Risks / undo:** this changes text only. To undo, revert the website commit and redeploy.

## Evidence (files read and commands run on 2026-10-14)

`curl -s -w "%{http_code}" https://www.americangroup.ai/policy/gadgetnest/privacy.html` returned `200`, and the body is byte-identical to `client/public/policy/gadgetnest/privacy.html` (`cmp` printed nothing). `index.html` is byte-identical to `privacy.html`. The website checkout is level with `origin/main`.

| Live policy says | The app on GadgetNest `main` |
|---|---|
| "Android permissions declared: INTERNET." | `android/app/src/main/AndroidManifest.xml:4,11,12` declares INTERNET, POST_NOTIFICATIONS and RECEIVE_BOOT_COMPLETED. Lines 20-25 remove AD_ID, ACCESS_ADSERVICES_AD_ID and ACCESS_ADSERVICES_ATTRIBUTION with `tools:node="remove"`. The flutter_local_notifications 22.3.2 plugin manifest also adds VIBRATE. I did not build a merged Android manifest (Android does not build on this Mac), so any further permissions that Google's ads or Firebase libraries merge in are **not verified**. |
| "The app does not show advertisements and does not include an advertising SDK." | Google AdMob through `agl_ads` (`lib/main.dart:33-37`). One banner at the bottom of the home list only (`lib/features/home/home_screen.dart:157`); none on onboarding, the picker, device pages or Settings; no interstitial. UMP consent where required, and Settings has a "Privacy choices" entry (`lib/features/settings/settings_screen.dart:257`). iOS has no ATT prompt and no `NSUserTrackingUsageDescription` (`ios/Runner/Info.plist:40-44`). I watched the banner fill (Google test ad) at its own height on an iPhone 17 simulator today. |
| "This release sends no analytics and no crash reports to us." | `AglCrash.init` and `initCrashReporting()` (Firebase Crashlytics) run at launch (`lib/main.dart:19,26`). `GoogleService-Info.plist` and `google-services.json` are in the repo, so it is live. Analytics and Performance Monitoring are switched off permanently (`Info.plist` `FIREBASE_ANALYTICS_COLLECTION_DEACTIVATED`, `firebase_performance_collection_deactivated`; `AndroidManifest.xml:82-87`), and the app does not call `AglInsights` (`lib/main.dart:20-25`). |
| "The app requests no camera, microphone, location, photo, contact or health permissions." | Still true. The only runtime permission is notifications, asked when "Remind me" is first switched on (`lib/domain/reminders.dart:138,144`), never at launch. |
| "The app connects to the internet to provide its features." (no detail) | The app downloads whole public files from `https://endoflife.date/api/v1/` (`lib/data/eol_client.dart:40-58`): `products/<name>` and `categories/device`. The request carries no device list and no query string (`test/eol_parsing_test.dart`). This phone's model name is read on the device (`lib/core/state/app_state.dart:53-69`) and matched locally. |
| "Data the app stores lives on your device…" (no detail) | The household list (names, person, purchase date, notes), settings and the cached endoflife.date files are kept in the app's local preferences (`app_state.dart:112-114,166`, `lib/data/eol_repository.dart:43`). Reminders are local notifications scheduled on the device. The household report goes only where the user sends it from the share sheet (`app_state.dart:83`). |

Website PR #1 (issue #18, waiting for approval) already has a GadgetNest hunk. Its Advertising and Crashlytics paragraphs are right for this app. Its Android permission line is wrong: it lists `ACCESS_ADSERVICES_AD_ID, ACCESS_ADSERVICES_ATTRIBUTION, AD_ID, INTERNET`, three of which the app removes, and it omits POST_NOTIFICATIONS and RECEIVE_BOOT_COMPLETED. If both are approved, the text below should replace PR #1's GadgetNest hunk rather than sit on top of it.

## Proposed replacement (from "Device permissions" through "Data retention and deletion")

**Last updated:** set to the publication date.

**Device permissions**
> The app asks for one permission, notifications, and only when you first turn on **Remind me** for a device or in Settings. Reminders are scheduled on your device; no server sends them. You can decline and still use the rest of the app. The app requests no camera, microphone, location, photo, contact or health permissions.
>
> Android permissions declared: `INTERNET, POST_NOTIFICATIONS, RECEIVE_BOOT_COMPLETED` (so reminders survive a restart), `VIBRATE`, plus the network permissions that Google's ads and diagnostics components need.

**What the app stores on your device** (new section)
> The devices you add (their names, who they belong to, a purchase date and your notes), your settings, and a copy of the public support data downloaded from endoflife.date. All of it is kept in the app's own storage on your device and is never sent to us. If you share a household report, it goes only where you send it from your phone's share sheet. Uninstalling the app deletes everything.

**Advertising** (PR #1's text, with this app's placement)
> GadgetNest is free and shows a banner ad from Google AdMob, a service of Google LLC, at the bottom of the home list. In the EEA, the UK and Switzerland, Google's consent form is shown before any ad is requested, and you can change your choice at any time under Settings → Privacy choices. The app does not ask to track you across other companies' apps, and on Android it does not request the advertising-ID permission. To serve and measure ads, Google may use your IP address and information about your device, as described in [Google's privacy policy](https://policies.google.com/privacy). Your device list is never sent with an ad request. We do not sell your personal information.

**Purchases** (unchanged): The app has no in-app purchases.

**Analytics and crash reporting** (PR #1's text)
> To find and fix problems, the app sends crash reports through Google Firebase Crashlytics (the error, the device model, operating system and app version, and a random installation identifier). This data is not linked to your name or account, is not used for advertising, and is processed by Google under Firebase's privacy terms. The app does not use analytics.

**Network**
> The app downloads public support dates from endoflife.date (https://endoflife.date), a community-maintained record of manufacturer support policies. It downloads whole public lists and matches your devices on your phone, so your device list and this phone's model are never sent. The only other network traffic is the crash reports and Google AdMob requests described above. All connections use HTTPS.

**Data retention and deletion**
> Everything the app stores stays on your device and is removed when you uninstall the app. Crash reports are kept by Google under Firebase's retention terms.

The "Accounts", "Children", "Your rights", "Changes" and "Contact" sections stay as they are.

## Not verified
- The merged Android manifest was not built, so the full Android permission list (anything Google's ads or Firebase libraries merge in, e.g. ACCESS_NETWORK_STATE or WAKE_LOCK) is not confirmed. The "plus the network permissions…" clause covers that; the founder may prefer the exact list once a release AAB is built.
- Crashlytics retention wording follows Firebase's published terms; I did not open the Firebase console.
- I did not check the App Store privacy label or Play data safety form against this text (store-compliance's job; spec §7 says the label stays unchanged).

## Related
- Founder question 1, issue #25 (pivot / merge / retire): still open, no comments as of 2026-10-14 (`gh issue view 25`).
- Website PR #1 / issue #18.
