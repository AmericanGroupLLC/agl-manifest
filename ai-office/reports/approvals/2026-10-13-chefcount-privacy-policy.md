# Approval: ChefCount privacy policy must match the rebuilt app

- **Decision needed:** approve (or edit) the replacement text below for the ChefCount privacy policy, published at `https://www.americangroup.ai/policy/chefcount/` (source: `americangroup.ai/client/public/policy/chefcount/index.html` and the identical `privacy.html`). Charter §6 (legal text).
- **Why now:** QA's must_fix on the Real Apps run (`projects/real-apps/continue/ChefCount.json`): the policy still describes camera and photo-library access for a fridge photo that the rebuilt app removed (ChefCount `584013d`; pushed HEAD now `75e7e2d`). It must match the binary before any resubmission. Reading the source page shows three more statements that are wrong for the app as it ships today (details under Evidence). Website PR #1 (issue #18, awaiting approval) fixes two of them but adds a claim that is wrong for ChefCount and keeps the camera/photo and network text.
- **Exact action:** reply "approve ChefCount policy" in the issue, or edit the wording here. The office then edits `client/public/policy/chefcount/index.html` and `privacy.html` in `americangroup.ai` (on top of, or instead of, PR #1's ChefCount hunk), deploys the site the usual way (push to main, never `--delete`), and checks the live page. Nothing is submitted to Apple (MA-043).
- **Risks / undo:** text only. Revert the website commit and redeploy to restore the old page.

## Evidence (all from files read on 2026-10-13)

| Live policy says (source file, lines 34-44) | The app as committed (ChefCount `75e7e2d`) |
|---|---|
| "Camera — ChefCount lets you take an optional photo of your fridge…" and "Photo library — … attach an optional photo of your fridge…" | Removed. No `image_picker`/`path_provider` in `pubspec.yaml`; `grep -n -E "NSCamera\|NSPhoto" ios/Runner/Info.plist` returns nothing; no camera permission in the merged Android manifest. On upgrade the app deletes the old `chefcount.fridge_photo_path` key and photo file. |
| "The app does not show advertisements and does not include an advertising SDK." | Includes Google Mobile Ads via `agl_ads` (`pubspec.yaml:32-36`, `lib/main.dart` `AglAds.configure`/`initialize`). Shows one banner at the end of the Kitchen list and one at the end of the Recipes list; no interstitial. UMP consent where required; Settings → Privacy choices is always visible. |
| "This release sends no analytics and no crash reports to us." | Sends crash reports through Firebase Crashlytics (`lib/main.dart` `AglCrash.init`; `GoogleService-Info.plist` and `google-services.json` are committed; `PrivacyInfo.xcprivacy` declares CrashData and OtherDiagnosticData). Firebase Analytics and Performance are linked by `agl_observability` but switched off in `Info.plist` (`FIREBASE_ANALYTICS_COLLECTION_DEACTIVATED`, `firebase_performance_collection_deactivated`) and `AndroidManifest.xml`. So PR #1's sentence about "anonymous usage statistics and performance measurements through Google Firebase Analytics and Performance Monitoring" is **not true for ChefCount**. |
| "The app declares no network permission on Android and works entirely on your device." | The merged Android manifest (debug build of `75e7e2d`, `build/app/intermediates/merged_manifest/...`) has `INTERNET`, `ACCESS_NETWORK_STATE`, `AD_ID`, `ACCESS_ADSERVICES_*` and `WAKE_LOCK`, all merged in from the Google ads and Firebase plugins. The app's own features (kitchen, recipes, cook log) make no network requests. |

Not verified: I could not fetch the live page from this machine (`curl https://www.americangroup.ai/policy/chefcount/` → "CONNECT tunnel failed, response 503"). The source file and `dist/public/policy/chefcount/index.html` are identical and the website checkout is level with `origin/main` (`git status -sb`: `## main...origin/main`), so the live page very likely matches. A person should open the URL to confirm.

## Proposed replacement (sections between "Accounts" and "Data retention and deletion")

**Last updated:** set to the publication date.

**Accounts** (unchanged): The app does not require registration and does not create user accounts or profiles.

**What the app stores on your device** (new section)
> Your kitchen list (items, amounts and use-by dates), the recipes you mark as cooked, whether you used or binned items you removed, the recipes you add yourself, your favourites and your settings. They are kept in the app's own storage on your device, are never sent to us, and are deleted when you uninstall the app.

**Device permissions** (replaces the Camera and Photo library list)
> ChefCount does not use your camera, photo library, location, contacts or microphone, and asks for no device permissions. On Android the app includes the internet and network-state permissions, which Google's ads and crash-reporting components need.

**Advertising** (replaces "does not show advertisements")
> ChefCount is free and shows ads from Google AdMob: one banner at the end of the Kitchen list and one at the end of the Recipes list. There are no full-screen ads. Google may use your device's advertising identifier to serve and measure ads, as described in [Google's privacy policy](https://policies.google.com/privacy). Where the law requires it (the EEA, the UK and Switzerland) Google asks for your consent before any ad is requested, and Settings → Privacy choices lets you change that choice at any time. Your kitchen list, recipes and history are never sent with an ad request. We do not sell your personal information.

**Purchases** (unchanged): The app has no in-app purchases.

**Crash reporting** (replaces "Analytics and crash reporting")
> If the app crashes, it sends a crash report through Google Firebase Crashlytics so we can fix the problem: the error, the device model, operating-system and app version, and a random installation identifier. It is not linked to your name, is not used for advertising, and is processed by Google under [Firebase's privacy terms](https://firebase.google.com/support/privacy). The app sends no usage analytics.

**Affiliate links** (new section; drop it if founder question 3 in the spec removes the links)
> Some recipe pages link to Amazon searches for ingredients or tools. These are affiliate links: if you buy through them we may earn a commission, at no extra cost to you. The page says so next to the links. Opening one takes you to Amazon in your browser; ChefCount sends Amazon nothing about your kitchen.

**Sharing** (new section)
> "Share recipe" hands the recipe text to your phone's share sheet. Nothing is sent unless you pick an app to share with.

**Network** (replaces "declares no network permission")
> The kitchen, recipes, swaps and cook log work offline and make no network requests. The only network traffic is Google's ads and crash reports, described above, and any Amazon link you choose to open.

The "Data retention and deletion", "Children", "Your rights", "Changes" and "Contact" sections stay as they are.

## Related
- Store-side counterpart (store-compliance, not done here): remove camera and photo-library from the App Store privacy answers and Play data safety; data collected stays crash data and AdMob device identifiers (spec §5, §8).
- Website PR #1 / issue #18: if both are approved, the ChefCount hunk of PR #1 should be replaced by this text, not stacked with it.
