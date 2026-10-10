# Every API action lives here

**Rule: `agl-manifest` owns every action that talks to an external API.** If a
task needs App Store Connect, Google Play, Firebase, AdMob or GitHub, the script
belongs in `agl-manifest/scripts/` — committed, reviewed, and listed below.

Nothing ad-hoc. Scripts were previously scattered in an untracked
`~/agl/.sweep/` directory: 27 of them, including the only working iOS IPA
builder. None was version-controlled, none was discoverable, and several
silently duplicated a script that already existed here. That is what this rule
exists to prevent.

## Where things go

| | |
| --- | --- |
| Scripts | `agl-manifest/scripts/` — the only home |
| Run artifacts (logs, evidence JSON, built binaries) | `~/agl/.dist/` |
| Measured outputs that are committed | `agl-manifest/docs/` |
| Credentials | `~/agl/.secrets/` — **never** committed, see MA-001 |

A script writes evidence to `~/agl/.dist/`; a script that produces a *measured
fact about the portfolio* writes it to `docs/` and that file is committed. Never
hand-edit the second kind — change the script and re-run it, or the file starts
lying.

## App Store Connect

Auth: `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_PATH` — load with
`source scripts/testflight/env.sh`.

| Script | What it does |
| --- | --- |
| `sync_testflight_testers.rb` | Mirrors Users and Access into every app's **internal** beta group, creating the group when absent with auto-distribute on |
| `asc_build_state.rb` | Asks Apple which apps really have a usable build **and where each one stands in review**. Writes `docs/asc-build-state.json`, which is committed and readable in CI; it used to write only `~/agl/.sweep/asc_upload.psv`, outside the repo, which went stale and made the checklist report 14 apps with no build when Apple had 38 |
| `testflight/asc_screenshots.rb` | Downloads the screenshots App Store Connect **actually holds** for each app's newest version into `<DIST>/asc-screenshots/`. Read-only. Written because six 2.3.3 rejections passed a gate that judged the PNGs on this laptop |
| `screenshot_audit.py` | Reads every uploaded screenshot with OCR (RapidOCR in `<DIST>/ocr-venv`; macOS Vision fails here with an e5rt compile error) and fails login forms, system prompts, keyboards, onboarding, test-account/demo buttons, SAMPLE DATA banners, the iOS home screen and other apps. Writes `docs/screenshot-audit.json` |
| `testflight/iap_readiness.rb` | Per app: billing plugin in the binary versus IAP/subscription products in App Store Connect, with state and missing metadata. Read-only by default; never submits. Writes `<DIST>/iap-readiness.json` |
| `apple_requirements.py` | The catalogue of every requirement App Review has raised against our apps, each with the check that enforces it; folded into the submission gate. Writes `docs/apple-requirements.json` and `docs/APPLE_REQUIREMENTS.md` |
| `domain_cutover.py` | Moves every store listing to americangroup.ai the moment the domain serves the site: merge + deploy the website branch, verify the 301 and the policy pages, then App Store Connect metadata (`deliver_metadata.py`) and Play contact details (`play_gap_audit.py --fix --domain`). `--watch` polls every 10 min |
| `testflight/asc_urls.rb` | Sets every app's App Store privacy / support / marketing URL in every localization to the pages `verify_policy_urls.py` proved live on www.americangroup.ai, and reads them back; `--check` reports only. Written because `deliver` reported ok for 43 apps while 28 still carried safecodeg.com |
| `cloudflare_dns.py` | Keeps the americangroup.ai Cloudflare zone safe for the site and its mail: website (@, www) proxied, every other host DNS-only, MX on DNS-only names, SSL Full (strict), Always Use HTTPS. Report by default, `--apply` to fix. Token: `~/agl/.secrets/cloudflare-token` |
| `testflight/account_freeze.rb` | Makes `submit_production.rb` and `resubmit_rejected.rb` exit 4 while any app holds a Guideline 5.6 finding (MA-043) |
| `appstore_records.rb` | Reports the app records that exist |
| `testflight/run_batch.py` | Builds and uploads to TestFlight |
| `testflight/build_only.py` | Builds a signed IPA via the fastlane lane, no upload |
| `testflight/distribute.rb` | Fills the **external** group and submits for Beta App Review |
| `testflight/list_builds.rb` | What Apple holds for one bundle id |
| `testflight/check_build.rb`, `records_present.rb` | Polling helpers |
| `testflight/enable_capabilities.rb` | Turns on app capabilities |
| `testflight/clear_stale_submissions.rb` | Deletes review submissions prepared and never sent. The public API refuses (`403 does not allow 'DELETE'`, `409 not in cancellable state`); the `iris` host with an Apple ID session returns 204. Leaves `UNRESOLVED_ISSUES` alone — those are real rejections |
| `testflight/reply_rejections.rb` | Posts the Guideline 2.1 reply into Resolution Center. A reply is a **draft that is then sent**: posting straight to `resolutionCenterMessages` answers "attribute 'messageBody' can not be included in a 'CREATE'", then "missing a required relationship: createFromDraftMessage" |
| `testflight/set_idfa.rb` | Declares `usesIdfa` per app, from whether its pubspec depends on `google_mobile_ads`. It was `null` on all 39 versions — never answered for any app — which App Store Connect reports only as "This resource cannot be reviewed, please check associated errors" |
| `testflight/submit_production.rb` | Submits for App Store review |
| `ios_profile_map.rb` | Maps every bundle id to its active App Store provisioning profile, from the API rather than a hand-made file, and with `--install` writes the `.mobileprovision` files where Xcode looks. `build_ipa.py` has always read this map; until 2026-09-26 nothing produced it, so the pipeline's iOS job could not run on a fresh runner |
| `policy_aliases.py` | Generates the `.htaccess` rewrite block that makes every policy URL resolve whatever case it is written in. `--apply` splices it into both `client/public/.htaccess` and `.htaccess` in the site repo, before the SPA catch-all. Pushing is not publishing — see MA-030 |
| `play_gap_audit.py` | Reports, and with `--fix` fills, everything Play's API can reach per app — contact details, listing text, screenshots, production track. Written because "the app is a Draft" is a symptom, not a diagnosis: 31 apps were missing a contact website and 10 had no screenshots on the listing |
| `merge_build_evidence.py` | Recombines `docs/build-evidence-shard*.json` after the six parallel Android shards. Newest `built_at` wins per app, so re-running one shard updates only its apps |
| `build_ipa.py` | **The IPA builder.** Archives *unsigned* and signs on export — a CLI signing setting applies to every target including CocoaPods, which reject provisioning profiles. Unlike the fastlane lane it does not rewrite each app's pbxproj, so it leaves no churn in the app repos |
| `verify_ipa_signing.py` | Proves every shipped IPA is `Apple Distribution`, `get-task-allow=false`, correct bundle id, signature valid |

**What the API cannot do**, each proven rather than assumed — see MA-008:
creating an app record (`apps` refuses `CREATE`), and `produce` needs an Apple ID
session rather than the API key. Re-tested on fastlane **2.240.1** (2026-09-25),
in case the update changed it: `fastlane run produce` for AeroSwift ends in
"The request could not be completed because: Unauthorized Access". It reaches
for the Apple ID path and the stored session has expired.

All 43 Developer Portal **bundle ids** are registered — that part the key does
do, and `BundleId.create` is idempotent, so a record can be created in the
Console without registering anything first.

## Google Play

Auth: `~/.secrets/play-publisher-agl.json`, or impersonation of
`american-group-publisher@american-group-llc.iam.gserviceaccount.com`.

| Script | What it does |
| --- | --- |
| `play_upload.py` | Uploads a signed bundle to the internal track. `--status completed` hands it to testers; the default is a draft |
| `play_internal_share.py` | **Internal app sharing.** Uploads a bundle and returns an install link for the existing Play Console users — no tester list and no Google Group |
| `play_state.py` | Asks Play what is actually there per package. Ground truth; the local evidence file is not |
| `play_release.py` | Promotes a draft internal release |
| `play_production_blockers.py` | Reports, per app, whether a production release exists and whether it is staged or live, and records the API's refusal for a Draft app. Writes `docs/play-production-blockers.json` |
| `store_inventory.py` | Reconciles the 43-app manifest against what each store actually holds, and names the records each account carries that are **not** in the manifest. Writes `docs/store-inventory.json` |
| `play_listing.py` | Pushes listing metadata |
| `sync_play_testers.py` | Reports each app's internal/alpha/beta tester lists and, with PLAY_TESTER_GOOGLE_GROUP, attaches that group to all three. Play takes no individual addresses — see MA-033. Roster is `store/testers.json` |

**What the API cannot do.** Google's own discovery document settles it — the
`Testers` schema has exactly one property:

```json
"Testers": { "googleGroups": { "items": {"type": "string"}, "type": "array" } }
```

There is **no way to add a tester by email address**. `testers.update` takes
Google Groups only. Internal app sharing is the route that avoids groups, but it
requires the app to exist on Play and to have been published at least once —
otherwise `404 Package not found` or `400 UploadException: NOT_PUBLISHED`.

**`NOT_PUBLISHED` is an app-level state, and uploading another bundle does not
clear it.** Measured 2026-09-22: AGCleaner's internal track already holds
`status=completed`, `versionCodes=['1'... '2']`, and internal app sharing still
rejects it with `400 UploadException: NOT_PUBLISHED`. A completed internal-track
release is therefore *not* what Play counts as published — the app itself is
still a Draft in Console until the App content declarations are finished and an
initial release is rolled out and reviewed. Do not schedule a bulk
`play_upload.py` run expecting it to unblock sharing; it will not.

What the API can contribute towards leaving Draft is narrow. It has
`applications.dataSafety` (Safety Labels, as a CSV body) and
`edits.listings`/`edits.details`/`edits.images`. It has **no** endpoint for the
content-rating questionnaire, target audience, ads declaration or app access —
`edits` exposes only `apks, bundles, countryavailability, deobfuscationfiles,
details, expansionfiles, images, listings, testers, tracks`. Those declarations
are Console-only, which is why MA-021 stays a human action.

There is also no `applications.create`: the `applications` resource exposes a
single method, `dataSafety`. An app record cannot be created over the API.

`users.list` does work for Play Console *account* users, and needs `pageSize=-1`;
any other value returns "Pagination is not currently available."

## Firebase · AdMob · GitHub

| Script | What it does |
| --- | --- |
| `firebase_register.py` | Registers each app and writes its real config files. Needs the `x-goog-user-project` header with ADC. `--debug-variant` registers `<package>.debug` for apps whose debug buildType adds that suffix and writes both clients into google-services.json; `--debug-project=<id>` puts it in another project (writing `src/debug/google-services.json`) when the app's own project is full |
| `status.py` | Repository state via the GitHub API; needs `GH_TOKEN` |

`admob_setup.py` creates an AdMob app for every app on both platforms (43 x 2 =
86) and a banner and interstitial unit for each. **Use v1beta, not v1**: v1
exposes only list/get/report, while v1beta adds `accounts.apps.create` and
`accounts.adUnits.create`. Verified against both discovery documents 2026-09-26.

AdMob has no service-account path — it authorises as the account owner — so the
credential comes from one interactive consent:

```bash
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/admob.monetization,https://www.googleapis.com/auth/admob.readonly
```

The script refuses with that exact command if the scope is missing. See MA-015.

## Supabase

| Script | What it does |
| --- | --- |
| `supabase_accounts.py` | Makes the three documented test accounts real on project `smvvjivvlprjhzhoizym` — creates them, confirms their email, resets them to the documented password, and verifies each one signs in. `--check` verifies without writing. `--wire-store` then records the QA address on every app with a sign-in screen, so `asc_readiness.rb` hands it to App Review |

Two things about this one are not obvious.

**The service-role key is never stored.** Confirming an address is an admin
operation (`PUT /auth/v1/admin/users/{id} {"email_confirm": true}`) and the
project has `mailer_autoconfirm: False`, so a created user cannot sign in until
that call is made. The key is fetched per run from the Supabase CLI:

```bash
supabase projects api-keys --project-ref smvvjivvlprjhzhoizym -o json
```

The CLI holds its own token in the macOS keychain and can read it; a plain
`security find-generic-password -s "Supabase CLI" -a supabase -w` from a
non-interactive shell returns **empty**, which is why the key is taken this way
rather than by extracting the token. `supabase login` is the only prerequisite.

**Do not reach for `supabase config push`.** The repo's `supabase/config.toml`
is a local-development file — `site_url = "http://127.0.0.1:3000"` — and
pushing it would overwrite the production auth configuration with localhost
redirects.

Passwords live in the integration guide and are read from it at run time, by
this script and by `asc_readiness.rb`. `store/apps/*.json` names the reviewer
account but deliberately holds no password; `AGL_DEMO_PASSWORD` overrides.

Still not doable from here: **enabling anonymous sign-ins**. That is Management
API configuration and needs a personal access token, not the service-role key.
`POST /auth/v1/signup {}` currently answers `422 anonymous_provider_disabled`,
which is why yourtube's "Continue as guest" button does not work. See MA-040.

## Firebase Test Lab — real hardware

| Script | What it does |
| --- | --- |
| `testlab_run.py` | Runs each app's APK as a Robo crawl on a **physical** phone in Firebase Test Lab, records video, and downloads the mp4. `--list-devices` shows what the live catalog offers; `--all --skip-build` uses APKs already built |

This is the answer to a blocker that `MANUAL_ACTIONS.md` wrongly recorded as
human-only. Apple asked, for twelve apps, for *"a screen recording of the app
running on a physical device"*. Test Lab's catalog is real hardware —
`gcloud firebase test android models list --filter="form=PHYSICAL"` — and
`--record-video` produces exactly that artefact.

Robo, not instrumentation, for two reasons: a Robo crawl needs **no test code**
(so it works on all 43 apps today, with no androidTest APK per app), and the
crawl is a recording of someone using the app, which is what was asked for.

Device ids are validated against the live catalog on every run, because Test
Lab retires models and a stale id fails the whole run.

iOS Test Lab exists too (`gcloud firebase test ios models list` offers iPhone
16 Pro, iPad 10th gen and others) but needs an XCTest bundle per app rather
than a bare binary, so it is not wired up yet.

## Supabase

| Script | What it does |
| --- | --- |
| `remove_demo_auth.py` | Deletes the test-account and demo-mode code paths from the apps — see below. Not an API action, but it is the other half of `supabase_accounts.py` |

`remove_demo_auth.py` exists because the apps authenticated **locally**:
`_isConfiguredTestAccount` compared the typed email and password against
constants compiled into the binary and returned "signed in" without ever
asking Supabase. That, the "Use test account" button and the "Demo mode (dev)
— skip to app" shortcut all existed only because the documented QA accounts
did not work. They work now, so a tester signs in like any other user.

The removal is structural — a scanner that understands Dart strings, comments
and nesting — because a textual one is actively dangerous here. Writing it
turned up four of its own bugs, each caught by a guard that is now permanent:

* a bracket-balance check on every file before it is written, after a removal
  cut `OutlinedButton(` in half and left its arguments orphaned;
* dead-symbol matching that ignores string literals, after it deleted the test
  *"no committed source ships a literal test credential"* — whose whole purpose
  is to name `qaPassword` — in every app;
* single-line-only statement removal, after `[^;()]*` matched across newlines
  and swallowed the multi-line `AppEnv.validate(...)` startup guard;
* `--verify`, which runs `flutter analyze` **and** `flutter test` per app,
  because analyze alone once passed a codemod that broke 355 tests.

Phase B, not done: `auth_demo_session` is still read at startup. It is also how
roughly seven widget tests per app get past the sign-in wall, so removing the
read means giving the harness another way in.

## Measuring and verifying

| Script | What it answers |
| --- | --- |
| `store_checklist.py` | Per-app readiness; the headline number |
| `artifact_staleness.py` | Which artifacts predate a commit that could change them. Android and iOS inputs are kept separate — conflating them reported eight bundles as stale when only `ios/Podfile.lock` had changed |
| `website_apps.py` | Generates www.americangroup.ai's 43 mobile-app pages (`client/src/data/mobileApps.generated.ts`) from each app's App Store copy, with status and store links from what Apple and Google report. A download button appears only for a live listing that answered HTTP 200. `--check` exits 1 when the site is stale; store_watch runs it |
| `verify_api_hosts.py` | Whether every host each app calls **exists**, via Google DNS-over-HTTPS (plain DNS is blocked here, so `dig` times out on every name). NXDOMAIN fails the gate; anything short of an address is recorded as `unverified`, never as dead. Writes `docs/api-hosts.json`; runs in CI and in every `store_watch` pass |
| `verify_store_urls.py` | Whether each store URL is real. **Do not trust HTTP 200** — this host serves its homepage for any unknown path, so the body is compared against a known-nonexistent path |
| `verify_deletion_urls.py` | Whether every app has a working account-deletion page (Play Data safety) |
| `audit_release_readiness.py` | 63 measured fields per app |
| `audit_i18n.py` | Translation coverage |

## Assets

| Script | What it does |
| --- | --- |
| `generate_app_icons.py` | App icons from a Material Icons glyph over a per-app gradient. Parses codepoints straight out of the Flutter SDK |
| `rebuild_android_icons.py` | Rebuilds Android icons from an app's own iOS artwork — adaptive foreground inset into the safe zone, genuinely round round-icons |
| `fix_launch_images.py` | Replaces the template 1×1 launch image; removes junk icon files |
| `feature_graphics.py` | The 1024×500 Play feature graphic |
| `policy_pages.py` | Generates the per-app policy site, including the deletion page every app needs |

## Build infrastructure

| Script | What it does |
| --- | --- |
| `build_release.py` | Signed Android bundles. Handles this machine's IPv4/proxy JVM requirements — see CLAUDE.md |
| `sim_install.py` | Debug-builds apps and installs them on an iPhone simulator and an Android emulator, launches each and checks it is still running. One app, several, or `--all`; `--ios`/`--android` for one platform, `--skip-build` to reinstall what is built. Report in `<DIST>/sim-install/`. Reuses `build_release.py`'s flavour choice and JVM flags |
| `ios_build_janitor.sh` | Reclaims disk during a long iOS sweep. Takes the build log as its argument. Never touches the app currently building, and never deletes `*.noindex` from DerivedData — those are shared Xcode caches, and removing them mid-sweep fails the build |

## Adding a new API action

1. Put the script in `agl-manifest/scripts/`.
2. Check this table first — if something already does it, extend that script
   rather than writing a second one. `upload_play.py` was retired for being an
   unreferenced duplicate of `play_upload.py`.
3. Support `--dry-run` where the action mutates anything.
4. Write evidence to `~/agl/.dist/`, not next to the script.
5. Add a row here.

| `firebase_distribute.py` | Uploads each app's APK to Firebase App Distribution and distributes it to the 11-person roster in `store/testers.json`. Talks to the REST API, not the CLI: the CLI's credentials are expired and `--reauth` needs a browser. Needs `x-goog-user-project` and the project **number** — see MA-038 |
