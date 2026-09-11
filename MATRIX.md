# Capability matrix

Platform support, sign-in, and every AdMob identifier the portfolio uses.
Regenerate with `python3 scripts/status.py`.

## Platforms and sign-in

`yes` means the platform is present **and** deliverable — a real signing
config and a `beta` lane. `build only` means the project builds but delivery
is not wired yet.

| App | Android | iOS | Sign-in | Login screen | Account optional |
| --- | :-: | :-: | --- | :-: | :-: |
| AGCleaner | yes | yes | none | — | — |
| AGrammarly | yes | yes | none | — | — |
| AGRecorder | yes | yes | none | — | — |
| BodyQuest | yes | yes | Supabase + Google + Apple | yes | yes |
| CalcMaster | yes | yes | Supabase + Google + Apple | yes | yes |
| CarDeal | yes | yes | none | — | — |
| ChefCount | yes | yes | none | — | — |
| CodeDeal | yes | yes | none | — | — |
| daily-pulse | yes | yes | Supabase + Google + Apple | yes | yes |
| DriftDate | yes | yes | Supabase + Google + Apple | yes | — |
| EventSpark | yes | yes | none | — | — |
| FashionFactory | yes | yes | none | — | — |
| GadgetNest | yes | yes | none | — | — |
| GroceryMatch | yes | yes | Supabase + Firebase + Google + Apple | yes | yes |
| HerJourney | yes | yes | Supabase + Google + Apple | — | — |
| HomeWise | yes | yes | none | — | — |
| iMaps | yes | yes | Supabase + Google + Apple | yes | yes |
| iMeasure | yes | yes | Supabase + Google + Apple | yes | — |
| Kinnav | yes | yes | Supabase + Google + Apple | — | — |
| MileMaster | yes | yes | none | — | — |
| MyFinance | yes | yes | none | — | — |
| MyHealth | yes | yes | Supabase + Google + Apple | yes | yes |
| NearServe | yes | yes | none | — | — |
| NewsBoard | yes | yes | none | — | — |
| NexusTransferPay | yes | yes | Biometric | — | — |
| Photriya | yes | yes | Supabase + Firebase + Google + Apple | yes | yes |
| PilotEnRoute | yes | yes | Supabase + Google + Apple | yes | yes |
| portfolio-board | yes | yes | none | — | — |
| radiotune | yes | yes | Supabase + Google + Apple | yes | — |
| RideZap | yes | yes | none | — | — |
| RoomCraft | yes | yes | none | — | — |
| TripNest | yes | yes | none | — | — |
| Uscis-Case | yes | yes | Supabase + Google + Apple | yes | yes |
| Verba | yes | yes | none | — | yes |
| VirtuBand | yes | yes | Supabase | yes | yes |
| WiFiTrail | yes | yes | none | — | — |
| yourtube | yes | yes | Supabase + Google + Apple | yes | yes |

17 of 37 apps have a sign-in dependency; the rest need no account at all.

## AdMob

11 of 37 apps serve ads.

**Application ids** are declared in `AndroidManifest.xml` and `Info.plist` and
must match what is passed to `AglAds.configure`. A mismatch is not a degraded
experience — on iOS the SDK throws `GADInvalidInitializationException` and iOS
terminates the app on every launch.

**Unit ids** are never committed. They are read from `--dart-define` at build
time, so a build without them serves Google's public test units — the safe
default rather than a broken one. The values below are the console record,
shown here so there is one place to check them against AdMob.

| App | Android app id | iOS app id | Android banner | Android interstitial |
| --- | --- | --- | --- | --- |
| BodyQuest | `ca-app-pub-3940256099942544~3347511713` _(Google test)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |
| CalcMaster | `ca-app-pub-8528784688453695~5377349094` | `ca-app-pub-8528784688453695~9148987425` | `ca-app-pub-8528784688453695/7665581023` | `ca-app-pub-8528784688453695/7474009334` |
| iMaps | `${admobAppId}` _(build-time)_ | `$(ADMOB_APP_ID)` _(build-time)_ | `ca-app-pub-8528784688453695/1143402684` | `ca-app-pub-8528784688453695/8340879191` |
| iMeasure | `ca-app-pub-8528784688453695~9265279754` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/1222409251` | `ca-app-pub-8528784688453695/9950162694` |
| PilotEnRoute | `${admobAppId}` _(build-time)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |
| radiotune | `ca-app-pub-8528784688453695~7770953426` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/4087643109` | `ca-app-pub-8528784688453695/2327055058` |
| TripNest | `ca-app-pub-8528784688453695~8044208178` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/3721819782` | `ca-app-pub-8528784688453695/5528514029` |
| Uscis-Case | `ca-app-pub-8528784688453695~2309537905` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/5539491423` | `ca-app-pub-8528784688453695/9095593054` |
| Verba | `ca-app-pub-3940256099942544~3347511713` _(Google test)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |
| VirtuBand | `ca-app-pub-8528784688453695~2836542125` | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | `ca-app-pub-8528784688453695/6914604113` | `ca-app-pub-8528784688453695/9569471431` |
| yourtube | `ca-app-pub-3940256099942544~3347511713` _(Google test)_ | `ca-app-pub-3940256099942544~1458002511` _(Google test)_ | **missing** | **missing** |

**9 apps still carry Google's test application id on iOS** — correct while an app has no iOS AdMob app of its own, and the thing to replace when one is created: BodyQuest, iMeasure, PilotEnRoute, radiotune, TripNest, Uscis-Case, Verba, VirtuBand, yourtube.

No app has iOS unit ids at all, so iOS release builds serve test ads by
design until an iOS AdMob app exists for them.

## Consent

Every ad app gates its requests on UMP consent — `AglConsent` in `agl_ads`,
with a per-app test that fails if any ad is constructed without a check in
the enclosing method. It stays dormant until a GDPR message is published in
AdMob → Privacy & messaging; see [PENDING.md](PENDING.md) row 7.
