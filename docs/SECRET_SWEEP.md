# Portfolio secret-material sweep

**Date of sweep:** 2026-09-13
**Scope:** every git repository under `/Users/spatchava/agl/` (46 directories containing `.git`),
plus the out-of-repo keystore vault at `/Users/spatchava/agl/.secrets/`.
**Author:** security sweep. **Report only — nothing was deleted, moved, or rewritten, and no
git history was altered.**

---

## 1. Bottom line

| | Count |
| --- | --- |
| Secret-shaped files on disk today (excluding `.secrets/`) | 56 |
| ...of which **tracked at HEAD** | **3** (all Android *debug* keystores) |
| ...of which **untracked but present in pushed git history** | **8** |
| ...of which correctly ignored and never committed | 45 |
| Additional secret files that exist **only in git history** (already deleted from disk) | 9 real + 3 vendored `node_modules` copies |
| Hardcoded secrets found in Dart source | **0** (one Supabase *publishable/anon* key in 16 apps — by design) |
| Real `.env` files with live values on disk | **0** |

**The two things that actually matter:**

1. **Seven Android upload keystores plus their cleartext passwords were committed and pushed
   to GitHub** (CalcMaster, iMaps, iMeasure, radiotune, Uscis-Case, VirtuBand, TripNest).
   They were later `git rm`'d, but the blobs are still reachable from `origin/main` /
   `origin/master`. **Verified good news:** every one of those keys has since been *replaced* —
   the keystore now referenced by each app's `key.properties` has a different signing
   certificate and a different password (fingerprints in §3.1). So the leak is of *superseded*
   keys, not of the keys in use today.
2. **An Apple App Store Connect API private key (`AuthKey_AZ338M36U3.p8`, a real 256-bit EC
   private key) is in `AmericanGroupLLC-Backend` history on both `origin/main` and
   `origin/dev`.** It has been replaced on disk by a different key ID (`AuthKey_UV8NYF9767`),
   but **whether key `AZ338M36U3` was revoked in App Store Connect is not something I can
   verify from this machine.** If it was not revoked, it is a live credential in a pushed repo.

Everything else is either correctly ignored local-only material, or a well-known public value.

---

## 2. Verdict legend

| Verdict | Meaning | Risk |
| --- | --- | --- |
| `EXPOSED — in pushed history` | The blob is reachable from a `origin/*` ref. Deleting the file does **not** undo this. | Real |
| `TRACKED AT HEAD` | Currently in the index and pushed. | Depends on the material |
| `In local history only` | Committed locally, but not reachable from any remote-tracking ref. | Contained, fix before pushing |
| `OK — local only, ignored` | On disk, matched by a `.gitignore` rule, zero commits ever. **This is the correct state.** | None |
| `OK — outside git` | Lives in `/Users/spatchava/agl/.secrets/`, which is not inside any repository. | None |

A file being *present on disk* is not a leak. A file being *in pushed history* is. This report
keeps those two strictly separate.

---

## 3. Findings that need action

### 3.1 Android upload keystores + cleartext passwords in pushed history

Seven repos committed a release upload keystore and its `key.properties` (which stores
`storePassword` and `keyPassword` in cleartext) to a branch that was pushed to GitHub. All were
later untracked by a "security: untrack Android signing credentials"-style commit, but that only
removes them from the tip — the blobs remain in history.

| Repo | Leaked keystore path (history) | Leaked `key.properties` | Reachable from | Window |
| --- | --- | --- | --- | --- |
| CalcMaster | `android/upload-keystore.jks` | `android/key.properties` | `origin/main` | 2026-08-14 → 2026-09-08 |
| iMaps | `android/new-upload-key.jks` | `android/key.properties` | `origin/main` | 2026-08-15 → 2026-09-05 |
| iMeasure | `android/imasure-upload.jks` | `android/key.properties` | `origin/main` | 2026-08-15 → 2026-09-06 |
| radiotune | `android/new-upload-key.jks` | `android/key.properties` | `origin/master` | 2026-08-15 → 2026-09-06 |
| Uscis-Case | `android/new-upload-key.jks` | `android/key.properties` | `origin/main` | 2026-08-15 → 2026-09-06 |
| VirtuBand | `android/new-upload-key.jks` | `android/key.properties` | `origin/main` | 2026-08-15 → 2026-09-06 |
| TripNest | `mobile/android/upload-key.jks` | `mobile/android/key.properties` | `origin/main` | 2026-08-26 → 2026-09-08 |

**Rotation status — verified.** I extracted each leaked keystore blob with `git cat-file`, opened
it with the leaked password from the corresponding historical `key.properties`, and compared its
certificate to the keystore each app's current `key.properties` points at. Every pair differs:

| App | Leaked cert SHA-256 | Current cert SHA-256 | Rotated? |
| --- | --- | --- | --- |
| CalcMaster | `59:E6:1F:33:7E:EB:29:94:…:50:DE:27` | `20:73:F4:95:8E:35:CF:71:…:DF:FC:B6` | yes |
| iMaps | `B4:BF:59:B8:AD:87:5F:48:…:38:37:33` | `B7:4E:83:A4:4A:11:DF:7A:…:2B:FE:1A` | yes |
| iMeasure | `A3:9E:15:7C:B4:82:50:2A:…:EE:80:93` | `EC:5E:6A:86:68:B7:12:CE:…:30:D3:3F` | yes |
| radiotune | `E0:A9:9F:E0:3A:33:CA:48:…:4C:FA:21` | `A1:89:05:EB:AF:28:2B:B1:…:89:AD:F6` | yes |
| Uscis-Case | `35:D1:48:63:54:80:D4:68:…:32:CA:12` | `56:5D:BE:E8:1C:47:3E:BC:…:93:29:BE` | yes |
| VirtuBand | `F2:39:FF:6F:7B:96:C1:D9:…:2D:A6` | `99:63:5E:5E:B1:FF:B4:8D:…:09:CC:74` | yes |
| TripNest | `3E:DF:12:2A:E2:D5:8D:EF:…:D7:B9:E8` | `72:D9:17:6A:72:E4:F8:75:…:26:BC:B3` | yes |

The store passwords also differ (compared as SHA-256 digests; no cleartext password appears in
this document). Every current `key.properties` in the portfolio now points at an absolute path
under `/Users/spatchava/agl/.secrets/keystores/`, which is outside every repository.

**What is still open, and what I cannot verify from here:**

- **Play App Signing registration.** A leaked *upload* key is only harmless if Google no longer
  accepts it for that package. If any of these seven apps was already uploaded to Play with the
  leaked cert, the rotation must also be registered with Google (upload-key reset) or the leaked
  key is still a valid upload credential. I have no Play Console access and **cannot verify
  this**. This is the single highest-value follow-up.
- **History scrubbing.** The blobs are still in `origin/*`. Removing them requires a history
  rewrite + force-push, which is explicitly out of scope for this run and should be a deliberate,
  coordinated decision. Rotation (already done) is the more important half; scrubbing is
  hygiene.
- **TripNest still has the compromised keystore on disk.** `TripNest/mobile/android/upload-key.jks`
  (sha256 `c8e1648e…`) is byte-identical to the leaked blob. It is git-ignored and is **not** the
  file the build uses (`key.properties` points at `.secrets/keystores/TripNest-upload.jks`,
  sha256 `c8f2544a…`), so it is a stale orphan rather than an active risk — but it is a loaded
  footgun sitting next to the build.

### 3.2 Apple App Store Connect API key in pushed history

| Path | Repo | On disk | Commits | Reachable from |
| --- | --- | --- | --- | --- |
| `certs/AuthKey_AZ338M36U3.p8` | AmericanGroupLLC-Backend | no (deleted 2026-09-06) | 2 | `origin/main`, `origin/dev` |

Confirmed to be a genuine key, not a placeholder: the 257-byte blob parses as a PKCS#8
`BEGIN PRIVATE KEY` with a 256-bit EC private scalar (`openssl pkey -noout -text`). The key ID
`AZ338M36U3` is embedded in the filename, which is all an attacker needs alongside the issuer ID
to mint App Store Connect API tokens.

The keys on disk today are `AuthKey_UV8NYF9767.p8` and `SubscriptionKey_PX7TXTDSHP.p8` — different
key IDs and different SHA-256 digests from the leaked one, so a replacement clearly happened.
**Whether `AZ338M36U3` was actually *revoked* in App Store Connect is not verifiable from this
machine.** Treat it as live until someone confirms revocation in the Apple developer portal.

### 3.3 Debug keystores tracked at HEAD

| Path | Repo | Alias | Store password | Cert SHA-1 |
| --- | --- | --- | --- | --- |
| `AGStudio/aQuantum/android/app/debug.keystore` | AGStudio | `androiddebugkey` | `android` (default) | `5E:8F:16:06:2E:A3:CD:2C:4A:0D:54:78:76:BA:A6:F3:8C:AB:F6:25` |
| `AGStudio/iQuantum/android/app/debug.keystore` | AGStudio | `androiddebugkey` | `android` (default) | same blob as above (identical file) |
| `NearServe/android/app/debug.keystore` | NearServe | `androiddebugkey` | `android` (default) | `D3:A5:E7:A0:4B:5C:F0:AD:AE:6D:85:49:A4:8F:D0:9B:23:3C:BF:E7` |

These are the only three secret-shaped files tracked in any repo's index, and none of them is
covered by a `.gitignore` rule. **Risk: low.** All three open with the universally-known password
`android`; the AGStudio pair is the stock React Native template keystore (`CN=Android Debug,
OU=Android, O=Unknown`, valid from 2013), which ships publicly in every RN release. NearServe's is
locally generated (`CN=Android Debug, O=NearServe`, 2026-05-23) but still uses the default
password, so it carries no secret either. Debug keystores never sign store builds.

They are still signing material tracked in a public-facing repo, so they are worth removing for
hygiene and to keep a "no signing material in git" policy honest — but this is a cleanliness
issue, not an incident. `MyFinance/android/app/debug.keystore` (same 2013 RN template blob) and
the three vendored `node_modules/react-native/template/.../debug.keystore` copies in ChefCount,
EventSpark and HomeWise are the same non-issue, already deleted from HEAD.

### 3.4 Local-history-only

| Path | Repo | Reachable from | Contents |
| --- | --- | --- | --- |
| `.env` | MyHealth | `refs/tags/backup/feat/supabase-login` only — **no local or remote branch** | `EXPO_PUBLIC_BACKEND`, `EXPO_PUBLIC_SUPABASE_URL`, `EXPO_PUBLIC_SUPABASE_ANON_KEY` (an `sb_pub…` publishable key) |

Only client-side publishable values, and the commit is not on any branch. **No action needed**
beyond not pushing that backup tag. I could not check whether `origin` already holds that tag
(no network egress in this sandbox).

### 3.5 Minor hardening

`/Users/spatchava/agl/.secrets/` (43 upload keystores, one stray `FashionFactory-key.properties`,
and `keystores.json`) is mode `drwxr-xr-x`
(0755) — world-readable to any local account. `chmod 700` would cost nothing. The important
property, that it sits outside every git repository, is already correct and is what keeps the
current production keys clean.

---

## 4. Dart source scan — clean

2,709 `.dart` files across all repos (excluding `build/`, `.dart_tool/`, `node_modules/`, and the
vendored Flutter SDK copies in `radiotune/.flutter-sdk-run/` and `yourtube/.flutter_sdk/`).

Patterns searched: `sk_live_*`, `sk-*` / `sk-proj-*` (OpenAI), `AKIA…` / `ASIA…` (AWS),
`ghp_*` / `github_pat_*`, `xox[baprs]-*` (Slack), `sbp_*` (Supabase PAT), `AIza…` (Google),
`-----BEGIN … PRIVATE KEY-----`, `service_role` / `SUPABASE_SERVICE`, long `Bearer` literals,
JWTs (`eyJ…​.eyJ…`), and generic `apiKey|secret|token|password|clientSecret = '<20+ chars>'`
assignments.

**Result: zero live secrets.** What the scan did surface, and why each is fine:

| Hit | Where | Assessment |
| --- | --- | --- |
| One Supabase JWT, 17 files across **16 apps** | `lib/**/supabase_config.dart`, `app_config.dart`, `backend_config.dart` | **Not a secret.** Decoded payload: `{"iss":"supabase","ref":"smvvjivvlprjhzhoizym","role":"anon","iat":1780202103,"exp":2095778103}` — `role: anon`, i.e. the publishable key, which is designed to ship inside the client binary. It is a `String.fromEnvironment('SUPABASE_ANON_KEY', defaultValue: …)` default, so it is overridable at build time. No `service_role` key exists anywhere in Dart. Apps: BodyQuest, CalcMaster, daily-pulse, DriftDate, GroceryMatch, HerJourney, iMaps, iMeasure, Kinnav, MyHealth, Photriya, PilotEnRoute, radiotune, Uscis-Case, VirtuBand, yourtube. |
| `AIzaSy-XXXXXXXX…` | `Verba/lib/core/config/verba_config.dart:120` | Literal placeholder, annotated `// ← placeholder`. |
| `'sk-integration-test-key'` | `Photriya/test/integration/storage_integration_test.dart:302` | Test fixture. |
| `service_role` string mentions | `GroceryMatch/test/release_hardening_test.dart:35,37`, `DriftDate/test/auth_service_test.dart:52`, `Kinnav/test/security/security_test.dart:26` | These are **tests asserting that a service-role key is absent**. Good sign, not a finding. |

A `git grep` over every repo's HEAD for `BEGIN … PRIVATE KEY`, `sk_live_`, `AKIA`, `ghp_` and
Slack tokens returned nothing outside `node_modules`.

The one real `AIza` key in the portfolio lives in `MyHealth/google-services.json` and
`MyHealth/expo_legacy/android/app/google-services.json` — both git-ignored, both with zero
commits ever. Android API keys in `google-services.json` are package-name-restricted and are
meant to ship in the APK; not a finding.

## 5. `.env` files — clean

53 `.env*` files exist on disk. **Every one of them is a `.example` or `.template`.** There is not
a single live `.env` anywhere under `/Users/spatchava/agl/*/`. Grepping all 53 for real-shaped
values (`eyJ…`, `sk_live_`, `sk-`, `AKIA`, `AIza`, `ghp_`, `sbp_`, `service_role`, `xox*-`,
long base64 blobs), after filtering obvious placeholders, returned **zero** hits.

## 6. Full inventory — every secret-shaped file on disk

The 44 entries under `.secrets/keystores/` (43 `*.jks` plus `FashionFactory-key.properties`) are
omitted from the table: they are all
`OK — outside git`, since `/Users/spatchava/agl` is not itself a repository and `.secrets/`
therefore belongs to none.

| Path (relative to `/Users/spatchava/agl/`) | Repo | Tracked | Ignored | In history | Verdict |
| --- | --- | --- | --- | --- | --- |
| `AeroSwift/mobile/android/key.properties` | AeroSwift | no | yes (`mobile/android/.gitignore:12`) | none | OK — local only, ignored |
| `AGCleaner/android/key.properties` | AGCleaner | no | yes (`android/.gitignore:12`) | none | OK — local only, ignored |
| `agl-manifest/work/GadgetNest/android/key.properties` | GadgetNest (nested clone) | no | yes (`android/.gitignore:12`) | none | OK — local only, ignored |
| `AGrammarly/mobile/android/key.properties` | AGrammarly | no | yes (`mobile/android/.gitignore:12`) | none | OK — local only, ignored |
| `AGRecorder/android/key.properties` | AGRecorder | no | yes (`android/.gitignore:12`) | none | OK — local only, ignored |
| `AGStudio/aQuantum/android/app/debug.keystore` | AGStudio | **yes** | **NO** | 1 commit, on remote | **TRACKED AT HEAD** (low risk — default debug key) |
| `AGStudio/iQuantum/android/app/debug.keystore` | AGStudio | **yes** | **NO** | 1 commit, on remote | **TRACKED AT HEAD** (low risk — default debug key) |
| `AGStudio/mobile/android/key.properties` | AGStudio | no | yes (`mobile/android/.gitignore:12`) | none | OK — local only, ignored |
| `AmericanGroupLLC-Backend/AuthKey_UV8NYF9767.p8` | AmericanGroupLLC-Backend | no | yes (`.gitignore:64`) | none | OK — local only, ignored |
| `AmericanGroupLLC-Backend/SubscriptionKey_PX7TXTDSHP.p8` | AmericanGroupLLC-Backend | no | yes (`.gitignore:65`) | none | OK — local only, ignored |
| `ApexMarketWatch/mobile/android/key.properties` | ApexMarketWatch | no | yes (`mobile/android/.gitignore:12`) | none | OK — local only, ignored |
| `BodyQuest/android/key.properties` | BodyQuest | no | yes (`android/.gitignore:11`) | none | OK — local only, ignored |
| `BuddyPlay/mobile/android/key.properties` | BuddyPlay | no | yes (`mobile/android/.gitignore:12`) | none | OK — local only, ignored |
| `CalcMaster/android/key.properties` | CalcMaster | no | yes (`.gitignore:39`) | 7 commits, on remote | **EXPOSED — in pushed history** (key since rotated) |
| `CalcMaster/AppStore_com.americangroupllc.calcmaster.mobileprovision` | CalcMaster | no | yes (`.gitignore:44`) | none | OK — local only, ignored |
| `CalcMaster/AuthKey_UV8NYF9767.p8` | CalcMaster | no | yes (`.gitignore:42`) | none | OK — local only, ignored |
| `CalcMaster/SubscriptionKey_PX7TXTDSHP.p8` | CalcMaster | no | yes (`.gitignore:42`) | none | OK — local only, ignored |
| `CarDeal/mobile/android/key.properties` | CarDeal | no | yes (`mobile/android/.gitignore:12`) | none | OK — local only, ignored |
| `ChefCount/android/key.properties` | ChefCount | no | yes (`android/.gitignore:12`) | none | OK — local only, ignored |
| `CodeDeal/mobile/codedeal_app/android/key.properties` | CodeDeal | no | yes (`mobile/codedeal_app/android/.gitignore:12`) | none | OK — local only, ignored |
| `daily-pulse/android/key.properties` | daily-pulse | no | yes (`android/.gitignore:17`) | none | OK — local only, ignored |
| `DriftDate/android/key.properties` | DriftDate | no | yes (`android/.gitignore:12`) | none | OK — local only, ignored |
| `DriftDate/android/upload-keystore.jks` | DriftDate | no | yes (`android/.gitignore:14`) | none | OK — local only, ignored (stale; build uses `.secrets/`) |
| `EventSpark/mobile/android/key.properties` | EventSpark | no | yes (`mobile/android/.gitignore:12`) | none | OK — local only, ignored |
| `GadgetNest/android/key.properties` | GadgetNest | no | yes (`android/.gitignore:12`) | none | OK — local only, ignored |
| `GroceryMatch/android/key.properties` | GroceryMatch | no | yes (`android/.gitignore:17`) | none | OK — local only, ignored |
| `HerJourney/android/key.properties` | HerJourney | no | yes (`android/.gitignore:12`) | none | OK — local only, ignored |
| `HomeWise/mobile/android/key.properties` | HomeWise | no | yes (`mobile/android/.gitignore:12`) | none | OK — local only, ignored |
| `iMaps/android/key.properties` | iMaps | no | yes (`android/.gitignore:11`) | 8 commits, on remote | **EXPOSED — in pushed history** (key since rotated) |
| `iMeasure/android/key.properties` | iMeasure | no | yes (`.gitignore:70`) | 6 commits, on remote | **EXPOSED — in pushed history** (key since rotated) |
| `Kinnav/android/key.properties` | Kinnav | no | yes (`android/.gitignore:13`) | none | OK — local only, ignored |
| `MileMaster/android/key.properties` | MileMaster | no | yes (`android/.gitignore:12`) | none | OK — local only, ignored |
| `MyCard/mobile/android/key.properties` | MyCard | no | yes (`mobile/android/.gitignore:12`) | none | OK — local only, ignored |
| `MyFinance/android/key.properties` | MyFinance | no | yes (`android/.gitignore:12`) | none | OK — local only, ignored |
| `MyHealth/android/key.properties` | MyHealth | no | yes (`android/.gitignore:12`) | none | OK — local only, ignored |
| `MyHealth/expo_legacy/android/app/debug.keystore` | MyHealth | no | yes (`.gitignore:60`) | none | OK — local only, ignored |
| `MyHealth/expo_legacy/android/app/google-services.json` | MyHealth | no | yes (`.gitignore:60`) | none | OK — local only, ignored |
| `MyHealth/google-services.json` | MyHealth | no | yes (`.gitignore:52`) | none | OK — local only, ignored |
| `NearServe/android/app/debug.keystore` | NearServe | **yes** | **NO** | 1 commit, on remote | **TRACKED AT HEAD** (low risk — default debug password) |
| `NearServe/mobile/android/key.properties` | NearServe | no | yes (`mobile/android/.gitignore:12`) | none | OK — local only, ignored |
| `NewsBoard/mobile/android/key.properties` | NewsBoard | no | yes (`mobile/android/.gitignore:12`) | none | OK — local only, ignored |
| `NexusTransferPay/flutter-mobile-app/android/key.properties` | NexusTransferPay | no | yes (`flutter-mobile-app/android/.gitignore:12`) | none | OK — local only, ignored |
| `Photriya/android/key.properties` | Photriya | no | yes (`android/.gitignore:11`) | none | OK — local only, ignored |
| `PilotEnRoute/android/key.properties` | PilotEnRoute | no | yes (`android/.gitignore:12`) | none | OK — local only, ignored |
| `PlantPulse/mobile/android/key.properties` | PlantPulse | no | yes (`mobile/android/.gitignore:12`) | none | OK — local only, ignored |
| `portfolio-board/mobile/android/key.properties` | portfolio-board | no | yes (`mobile/android/.gitignore:12`) | none | OK — local only, ignored |
| `radiotune/android/key.properties` | radiotune | no | yes (`android/.gitignore:17`) | 5 commits, on remote | **EXPOSED — in pushed history** (key since rotated) |
| `RideZap/mobile/android/key.properties` | RideZap | no | yes (`mobile/android/.gitignore:12`) | none | OK — local only, ignored |
| `RoomCraft/android/key.properties` | RoomCraft | no | yes (`android/.gitignore:12`) | none | OK — local only, ignored |
| `TripNest/mobile/android/key.properties` | TripNest | no | yes (`.gitignore:48`) | 2 commits, on remote | **EXPOSED — in pushed history** (key since rotated) |
| `TripNest/mobile/android/upload-key.jks` | TripNest | no | yes (`.gitignore:49`) | 2 commits, on remote | **EXPOSED — in pushed history**; on-disk copy is byte-identical to the leaked blob |
| `Uscis-Case/android/key.properties` | Uscis-Case | no | yes (`android/.gitignore:12`) | 5 commits, on remote | **EXPOSED — in pushed history** (key since rotated) |
| `Verba/android/key.properties` | Verba | no | yes (`android/.gitignore:12`) | none | OK — local only, ignored |
| `VirtuBand/android/key.properties` | VirtuBand | no | yes (`android/.gitignore:17`) | 6 commits, on remote | **EXPOSED — in pushed history** (key since rotated) |
| `WiFiTrail/android/key.properties` | WiFiTrail | no | yes (`android/.gitignore:12`) | none | OK — local only, ignored |
| `yourtube/android/key.properties` | yourtube | no | yes (`android/.gitignore:11`) | none | OK — local only, ignored |

**Note on FashionFactory:** `FashionFactory/android/key.properties` existed on disk at the start of
this sweep (untracked, ignored by `android/.gitignore:12`, zero commits) and was gone by the time
the final pass ran. FashionFactory is owned by another agent this run; its repo policy forbids
signing material on disk, so that is consistent with expected concurrent work, not with a
problem. FashionFactory has **no** secret material in its git history.

## 7. Files that exist only in git history

| Path | On disk now | Commits | Window | Reachable from | What it is |
| --- | --- | --- | --- | --- | --- |
| `CalcMaster/android/upload-keystore.jks` | no (deleted) | 7 | 2026-08-14 → 2026-09-08 | `origin/main` | Android upload keystore (binary) |
| `iMaps/android/new-upload-key.jks` | no (deleted) | 6 | 2026-08-15 → 2026-09-05 | `origin/main` | Android upload keystore (binary) |
| `iMeasure/android/imasure-upload.jks` | no (deleted) | 6 | 2026-08-15 → 2026-09-06 | `origin/main` | Android upload keystore (binary) |
| `radiotune/android/new-upload-key.jks` | no (deleted) | 5 | 2026-08-15 → 2026-09-06 | `origin/master` | Android upload keystore (binary) |
| `Uscis-Case/android/new-upload-key.jks` | no (deleted) | 5 | 2026-08-15 → 2026-09-06 | `origin/main` | Android upload keystore (binary) |
| `VirtuBand/android/new-upload-key.jks` | no (deleted) | 6 | 2026-08-15 → 2026-09-06 | `origin/main` | Android upload keystore (binary) |
| `TripNest/mobile/android/upload-key.jks` | **yes** | 2 | 2026-08-26 → 2026-09-08 | `origin/main` | Android upload keystore (binary) |
| `AmericanGroupLLC-Backend/certs/AuthKey_AZ338M36U3.p8` | no (deleted) | 2 | 2026-06-28 → 2026-09-06 | `origin/dev`, `origin/main` | Apple App Store Connect API private key |
| `MyFinance/android/app/debug.keystore` | no (deleted) | 2 | 2026-05-09 → 2026-09-08 | `origin/main` | RN template debug keystore (public) |
| `MyHealth/.env` | no (deleted) | 1 | 2026-06-21 | local tag only | Supabase URL + publishable anon key |
| `ChefCount/node_modules/react-native/template/android/app/debug.keystore` | no (deleted) | 2 | 2026-05-27 | `origin/main` | vendored `node_modules`, public template key |
| `EventSpark/node_modules/react-native/template/android/app/debug.keystore` | no (deleted) | 2 | 2026-05-27 | `origin/main` | vendored `node_modules`, public template key |
| `HomeWise/node_modules/react-native/template/android/app/debug.keystore` | no (deleted) | 2 | 2026-05-27 | `origin/main` | vendored `node_modules`, public template key |

---

## 8. Method, and a methodological warning

Per file:

```sh
git -C <repo> ls-files --error-unmatch -- <path>          # tracked?
git -C <repo> check-ignore -v -- <path>                   # ignored, and by which rule?
git -C <repo> log --all --full-history -- <path>          # ever committed?
git -C <repo> branch -r --contains <sha>                  # ...and was that commit pushed?
```

Portfolio-wide, to catch files that are no longer on disk:

```sh
git -C <repo> rev-list --all --objects | grep -Ei '<secret-shaped filenames>'
```

> **Warning for anyone repeating this: `git log --all -- <path>` is not sufficient.**
> Without `--full-history`, git's history simplification silently hides adds that are buried
> under merge commits. In this portfolio, plain `git log --all` reported **0 commits** for
> `iMeasure/android/key.properties` and `iMeasure/android/imasure-upload.jks` — both of which are
> in fact in six commits on `origin/main`. It also undercounted CalcMaster (4 vs 7), iMaps (6 vs 8),
> radiotune (2 vs 5), Uscis-Case (2 vs 5) and VirtuBand (4 vs 6). Always use `--full-history`, and
> cross-check with `rev-list --all --objects`.

Excluded from scanning: `.git/`, `node_modules/` (except where checked deliberately), `build/`,
`.dart_tool/`, `Pods/`, and the two vendored Flutter SDK trees
(`radiotune/.flutter-sdk-run/`, `yourtube/.flutter_sdk/`) whose `debug.keystore` and
`dummy-cert.pem` / `dummy-key.pem` are upstream Flutter test fixtures.

## 9. Explicitly not verified

- Whether the seven leaked upload keys are still accepted by Google Play for their packages
  (requires Play Console access).
- Whether Apple auth key `AZ338M36U3` was revoked in App Store Connect (requires Apple developer
  portal access).
- Whether the remote (`origin`) holds tags beyond the remote-tracking branches visible locally —
  in particular `MyHealth`'s `refs/tags/backup/feat/supabase-login`. No network egress in this
  sandbox, so `git ls-remote` was not run.
- Whether any leaked value was actually accessed by a third party. Nothing here establishes
  exploitation, only exposure.
- Row-Level Security enforcement on Supabase project `smvvjivvlprjhzhoizym`, which is what makes
  shipping the anon key safe. That is a server-side setting and was not checked.
