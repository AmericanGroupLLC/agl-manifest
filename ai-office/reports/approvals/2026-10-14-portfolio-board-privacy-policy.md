# Approval: Portfolio Board v2 privacy policy (on-device case studies, Firebase, one AdMob banner)

- **Decision needed:** approve (or edit) the replacement text below for the policy at `https://www.americangroup.ai/policy/portfolio-board/` (source in the website repo: `client/public/policy/portfolio-board/index.html` and `privacy.html`). This is Charter §6 (legal text). Decision log 2026-10-14 says the office drafts and publishes it; this file is the draft.
- **Why now:** portfolio-board is rebuilt as v2 (spec `projects/real-apps/specs/portfolio-board-v2.md`, data list §10). The live page describes an app that no longer exists and contradicts the new one.
- **Exact action after approval:** replace the sections from "Accounts" through "Data retention and deletion" in both HTML files, deploy the site the usual way (push to main, never `--delete`), and check the live page with curl.
- **Risks / undo:** text only. Revert the website commit and redeploy to undo.
- **Does not unblock resubmission on its own:** the 5.6 freeze (MA-043) still holds, and resubmission is a founder action (spec §14 Q7).

## Evidence (read on 2026-10-14)

`curl -s https://www.americangroup.ai/policy/portfolio-board/` returned HTTP 200. What it says, against the v2 app (portfolio-board `mobile/`, this commit series):

| Live policy says | Portfolio Board v2 |
|---|---|
| Camera permission "for scanning and AR features"; location "to show nearby results" | No camera, location or photo permission. `ios/Runner/Info.plist` has no usage-description string (`test/release_config_test.dart` guards camera, location, photo library and microphone). |
| "Android permissions declared: ACCESS_COARSE_LOCATION, ACCESS_FINE_LOCATION, ACCESS_NETWORK_STATE, INTERNET" | `android/app/src/main/AndroidManifest.xml` declares `INTERNET` and `ACCESS_NETWORK_STATE` only. The merged manifest of a release build was **not** produced (see Not verified). |
| "The app does not show advertisements" | One Google AdMob banner, the last item of the Board (`lib/features/board/board_screen.dart`), no interstitial (`test/ads_placement_test.dart`). UMP consent where required; Settings has "Privacy choices". |
| "This release sends no analytics and no crash reports" | Firebase Crashlytics (`AglCrash.init`), Analytics (automatic screen views only) and Performance Monitoring (`AglInsights.init`) start in `lib/main.dart`. No custom events, no user id, no Remote Config reads (`test/honesty_guard_test.dart`). |
| "The app connects to the internet to provide its features" | The app's own code makes no network request (`test/honesty_guard_test.dart`, "no network calls of its own"). Network traffic comes only from Firebase, AdMob, and links the user opens in the system browser. |
| "Data the app stores lives on your device" | True, now in detail: JSON files under the app's support folder (`cases.v1.json`, `lanes.v1.jsonl`, `packs.v1.json`, `profile.v1.json`) and three flags in shared preferences. Nothing leaves except what the user exports or shares. |

## Proposed replacement (from "Accounts" through "Data retention and deletion")

**Last updated:** set to the publication date.

**Accounts**
> Portfolio Board has no accounts, no sign-in and no profiles on our side. There is nothing to register and nothing to delete on a server.

**What the app stores on your device**
> The case studies you write (titles, roles, organisations, dates, the text of each section, skills and the links you add), the lane history of each case study and any note you add to a move, the packs you save together with the job posting you pasted for them, and the optional details you enter for export headers (name, headline, email address and website). This is kept in the app's own storage on your device and is never sent to us.
>
> A job posting you paste into Fit check is held in memory while you work with it and is saved only if you save a pack. Fit check compares the posting with your case studies on your device; it does not use AI and sends nothing anywhere.
>
> Your data leaves your device only when you choose to share it: when you copy a case study as Markdown, share a PDF, or export a backup file, it goes to the app or place you pick in your phone's share sheet. Your phone's own backup (iCloud or Google) may include the app's files, under your phone's backup settings.

**Device permissions**
> The app asks for no permissions: no camera, microphone, location, photos, contacts or notifications. Restoring a backup opens the system file picker, which lets you choose one file and gives the app nothing else.
>
> Android permissions declared by the app: `INTERNET` and `ACCESS_NETWORK_STATE`, plus any that Google's advertising and Firebase components add to support the services described below.

**Advertising**
> Portfolio Board is free and shows one banner ad from Google AdMob, a service of Google LLC, at the bottom of your board. No ad is shown anywhere else in the app, including while you present. In the EEA, the UK and Switzerland, Google's consent form is shown before any ad is requested, and you can change your choice at any time under Settings → Privacy choices. The app does not ask to track you across other companies' apps. To serve and measure ads, Google may use your IP address and information about your device, as described in [Google's privacy policy](https://policies.google.com/privacy). Nothing you write in the app is sent with an ad request. We do not sell your personal information.

**Purchases**
> The app has no in-app purchases.

**Analytics and crash reporting**
> To keep the app working, it sends anonymous diagnostics to Google Firebase: crash reports (Firebase Crashlytics: the error, device model, operating system and app version, and a random installation identifier), performance data (Firebase Performance Monitoring), and usage statistics such as which screens are opened (Google Analytics for Firebase). These are not linked to your name, and none of them contains your case studies, packs, pasted postings or details. They are not used for advertising.

**Network**
> The app itself makes no network requests. The only network traffic is the Firebase diagnostics and the Google AdMob requests described above, and any link you choose to open, which opens in your browser. All connections use HTTPS.

**Data retention and deletion**
> Everything the app stores stays on your device. You can delete it at any time with Settings → Reset everything, or by uninstalling the app. Firebase diagnostics are kept by Google under Firebase's retention terms.

The "Children", "Your rights", "Changes" and "Contact" sections stay as they are.

## Matches the store label (spec §10)

Crash data, performance data and product interaction (Firebase), device ID and advertising data (AdMob), all not linked to the user; case studies, profile and flags not collected. Play Data safety: encrypted in transit yes; deletion requests not applicable (no account). store-compliance owns the label and the form (spec §9).

## Not verified

- The merged Android manifest of a release build was not produced in this run, so the exact extra permissions Google's ads and Firebase libraries merge in are not listed. The "plus any that…" clause covers that until a release AAB is checked.
- Firebase and AdMob retention and processing wording follows their published terms; no console was opened.
- The App Store privacy label and Play Data safety form were not compared with this text (store-compliance's job).
