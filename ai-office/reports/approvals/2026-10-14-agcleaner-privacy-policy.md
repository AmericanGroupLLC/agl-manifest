# Approval: AGCleaner privacy policy must match the merge-and-restore app

- **Decision needed:** approve (or edit) the replacement text below for the AGCleaner privacy policy at `https://www.americangroup.ai/policy/agcleaner/` (source: `americangroup.ai/client/public/policy/agcleaner/index.html` and the byte-identical `privacy.html`). This is Charter §6 (legal text). Approving it also answers founder question 2 in the spec (`projects/real-apps/specs/AGCleaner.md` §7): the app now writes contacts, but only when the user taps Merge or Restore.
- **Why now:** this is a must_fix from QA on the Real Apps run (`projects/real-apps/continue/AGCleaner.json`). The rebuilt app merges and deletes contact cards after saving the originals to a restore point (AGCleaner `fd4091c`, `6453793`, `18abcbe`; pushed HEAD is `18abcbe`). The live policy still says the app "never edits, deletes or uploads a contact." The policy has to match the binary before any resubmission. Reading the source page turned up four more statements that are wrong for the app as it ships (see Evidence).
- **Exact action:** reply "approve AGCleaner policy" in the issue, or edit the wording here. The office will then edit `client/public/policy/agcleaner/index.html` and `privacy.html` in `americangroup.ai`, deploy the site the usual way (push to main, never `--delete`) and check the live page with curl. Nothing gets submitted to Apple (MA-043).
- **Risks / undo:** this changes text only. To undo, revert the website commit and redeploy.

## Evidence (files read and commands run on 2026-10-14)

`curl -s -w "%{http_code}" https://www.americangroup.ai/policy/agcleaner/` returned `200`. The response contains `never edits, deletes or uploads a contact.` and has no `WRITE_CONTACTS`. It is byte-identical to `client/public/policy/agcleaner/index.html` (`cmp` printed nothing). The website checkout is level with `origin/main`.

| Live policy says | The app as committed (AGCleaner `18abcbe`) |
|---|---|
| "NSContactsUsageDescription — AGCleaner reads your contacts to find entries that describe the same person. It never edits, deletes or uploads a contact." | `ios/Runner/Info.plist:33-34` now says: "AGCleaner reads your contacts to find cards for the same person, and changes them only when you tap Merge. Originals are saved on this iPhone first so you can restore them." Merge updates the kept card and deletes the others. Restore re-creates the originals. |
| "Android permissions declared: READ_CONTACTS, READ_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, WRITE_EXTERNAL_STORAGE." | `android/app/src/main/AndroidManifest.xml:7-20` declares READ_CONTACTS, **WRITE_CONTACTS**, READ_MEDIA_IMAGES, READ_EXTERNAL_STORAGE (max SDK 32) and WRITE_EXTERNAL_STORAGE (max SDK 29). AD_ID and the two ACCESS_ADSERVICES permissions are removed with `tools:node="remove"` (lines 32-37). INTERNET and ACCESS_NETWORK_STATE come in through the Firebase and ads plugins (I did not build a merged manifest today, so this is **not verified** for `18abcbe`). |
| "The app does not show advertisements and does not include an advertising SDK." | Uses Google AdMob through `agl_ads` (`lib/main.dart:28-32`). There is a banner at the foot of Home, Contacts and Photos, hidden while a scan or delete is running (`home_screen.dart:50`, `contacts_screen.dart:102`, `photos_screen.dart:105`). An interstitial can show when the user returns to Home from a pushed page (`app.dart:137`), at most once every 3 minutes (`agl_ads/lib/src/ads.dart:22`). UMP consent applies where required, and Settings > Privacy choices is always visible. |
| "This release sends no analytics and no crash reports to us." | `AglCrash.init` (Crashlytics) and `AglInsights.init` (Analytics, Performance Monitoring and a Remote Config fetch) run at launch (`lib/main.dart:18,22`). In release builds collection is on (`agl_observability/lib/src/insights.dart:73-95`). The app reads no Remote Config value, and `test/no_remote_switches_test.dart` guards that. Analytics ad-ID collection and ad-personalisation signals are off (`AndroidManifest.xml:75-80`). |
| "The app declares no network permission on Android and works entirely on your device." | Matching, hashing, merging and restore points all run on the device. The only network traffic is the Firebase diagnostics and the AdMob requests above. |
| "Data the app stores lives on your device…" (no detail) | The app writes `agcleaner_state.json` (scan history, "Not the same person" decisions and the restore-point index) and one `restore_points/<UTC time>.vcf` per merge. Both live in the app's Application Support folder (`lib/domain/app_state.dart:364`, `lib/domain/contact_merger.dart:104-109`, `lib/data/device_sources.dart:333,366`). Share sends a restore point to the system share sheet (`device_sources.dart:393`). |

Website PR #1 (issue #18, waiting for approval) already has an AGCleaner hunk. It fixes Advertising, Analytics and Network. It keeps "never edits, deletes or uploads a contact." and the old Android permission list. If both are approved, the text below should replace PR #1's AGCleaner hunk rather than sit on top of it. Its Advertising and Analytics paragraphs are reused below, with the ad placement corrected for this app.

## Proposed replacement (from "Device permissions" through "Data retention and deletion")

**Last updated:** set to the publication date.

**Device permissions**
> The app asks for these permissions only when you use the related feature. You can decline either one and still use the rest of the app.
> - **Contacts.** AGCleaner reads your contacts to find cards that describe the same person, including cards saved in different accounts (iCloud, Google, Exchange or on the phone). It changes your contacts only when you tap **Merge** or **Restore**. Before a merge changes anything, the original cards are saved as a vCard file inside the app on your device. If that save fails, nothing is changed. A merge updates the card you keep and deletes the others. **Restore** puts the originals back. Contacts are never uploaded.
> - **Photo library.** AGCleaner reads your photo library to find byte-for-byte identical copies. Nothing is uploaded, and copies are deleted only when you confirm.
>
> Android permissions declared: `READ_CONTACTS, WRITE_CONTACTS, READ_MEDIA_IMAGES, READ_EXTERNAL_STORAGE (Android 12 and earlier), WRITE_EXTERNAL_STORAGE (Android 10 and earlier)`, plus the internet and network-state permissions that Google's ads and diagnostics components need.

**What the app stores on your device** (new section)
> Your scan history, the groups you marked "Not the same person", and a restore point for each merge: a vCard file with the original cards, and the date. These files are kept in the app's own storage on your device and are never sent to us. You can share a restore point yourself from the Restore points screen, which opens your phone's share sheet. Uninstalling the app deletes them.

**Advertising** (PR #1's text, with this app's placement)
> AGCleaner is free and shows ads from Google AdMob, a service of Google LLC. There is a banner at the bottom of the main screens and, occasionally, a full-screen ad when you return to the home screen (at most one every three minutes). In the EEA, the UK and Switzerland, Google's consent form is shown before any ad is requested, and you can change your choice at any time under Settings → Privacy choices. To serve and measure ads, Google may use your device's advertising identifier and IP address, as described in [Google's privacy policy](https://policies.google.com/privacy). Your contacts and photos are never sent with an ad request. We do not sell your personal information.

**Purchases** (unchanged): The app has no in-app purchases.

**Analytics and crash reporting**: use PR #1's AGCleaner text as written (Crashlytics, Analytics, Performance Monitoring and Remote Config, no contacts, photos or file contents, Analytics' advertising-ID collection switched off).

**Network**
> Finding duplicates, hashing, merging and restore points all run on your device. No contact, photo or file content is ever sent anywhere. The only network traffic is the Firebase diagnostics and the Google AdMob ad requests described above, sent over HTTPS.

**Data retention and deletion**
> Everything the app stores, including restore points, stays on your device. Uninstalling the app removes it. Contacts that you merged or restored stay in your address book, because they are your contacts and not app data.

The "Accounts", "Children", "Your rights", "Changes" and "Contact" sections stay as they are.

## Not verified
- The merged Android manifest for `18abcbe` was not built today, so I have not confirmed it contains INTERNET and ACCESS_NETWORK_STATE.
- I did not watch the interstitial cadence on a device. The text describes the code: `app.dart:131-137` fires only after a page is popped back to Home, and `ads.dart:22` sets the 3-minute cap. I left out a "never during a scan" promise because a scan started on the Contacts screen may still be running after the user goes back to Home.

## Related
- Store-side counterpart (store-compliance, not done here): App Store privacy answers and Play data safety need contacts as read **and write**, plus the WRITE_CONTACTS permission (spec §5 and §8).
