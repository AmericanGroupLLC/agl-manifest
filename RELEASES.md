# Release binaries

Every app, and what you can download and run right now. Regenerate with
`python3 scripts/status.py`.

`artifacts.yml` publishes these — an APK that installs on a device, the AAB
Play needs, and for iOS a simulator build. A `.aab` **cannot** be sideloaded;
it is a Play upload format, which is why both are published. The iOS build is
unsigned, so it runs in the Simulator and not on a phone — TestFlight is the
only route to real hardware.

| App | Android | iOS | Latest build | Assets | Releases |
| --- | :-: | :-: | --- | --- | --- |
| AGCleaner | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/AGCleaner/releases) |
| AGrammarly | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/AGrammarly/releases) |
| AGRecorder | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/AGRecorder/releases) |
| BodyQuest | yes | yes | no release | — | [releases](https://github.com/AmericanGroupLLC/BodyQuest/releases) |
| CalcMaster | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/CalcMaster/releases) |
| CarDeal | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/CarDeal/releases) |
| ChefCount | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/ChefCount/releases) |
| CodeDeal | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/CodeDeal/releases) |
| daily-pulse | yes | yes | no release | — | [releases](https://github.com/AmericanGroupLLC/daily-pulse/releases) |
| DriftDate | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/DriftDate/releases) |
| EventSpark | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/EventSpark/releases) |
| FashionFactory | yes | yes | no release | — | [releases](https://github.com/AmericanGroupLLC/FashionFactory/releases) |
| GadgetNest | yes | yes | no release | — | [releases](https://github.com/AmericanGroupLLC/GadgetNest/releases) |
| GroceryMatch | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/GroceryMatch/releases) |
| HerJourney | yes | yes | no release | — | [releases](https://github.com/AmericanGroupLLC/HerJourney/releases) |
| HomeWise | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/HomeWise/releases) |
| iMaps | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/iMaps/releases) |
| iMeasure | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/iMeasure/releases) |
| Kinnav | yes | yes | v1.0.1 | `app-release.aab`, `app-release.apk` | [releases](https://github.com/AmericanGroupLLC/Kinnav/releases) |
| MileMaster | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/MileMaster/releases) |
| MyFinance | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/MyFinance/releases) |
| MyHealth | yes | yes | v1.1.0 | `myhealth-server-v1.1.0.tar.gz`, `MyHealth-web-v1.1.0.tar.gz` | [releases](https://github.com/AmericanGroupLLC/MyHealth/releases) |
| NearServe | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/NearServe/releases) |
| NewsBoard | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/NewsBoard/releases) |
| NexusTransferPay | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/NexusTransferPay/releases) |
| Photriya | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/Photriya/releases) |
| PilotEnRoute | yes | yes | no release | — | [releases](https://github.com/AmericanGroupLLC/PilotEnRoute/releases) |
| portfolio-board | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/portfolio-board/releases) |
| radiotune | yes | yes | no release | — | [releases](https://github.com/AmericanGroupLLC/radiotune/releases) |
| RideZap | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/RideZap/releases) |
| RoomCraft | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/RoomCraft/releases) |
| TripNest | yes | yes | no release | — | [releases](https://github.com/AmericanGroupLLC/TripNest/releases) |
| Uscis-Case | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/Uscis-Case/releases) |
| Verba | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/Verba/releases) |
| VirtuBand | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/VirtuBand/releases) |
| WiFiTrail | yes | yes | v1.0.0 | **none — tag only** | [releases](https://github.com/AmericanGroupLLC/WiFiTrail/releases) |
| yourtube | yes | yes | no release | — | [releases](https://github.com/AmericanGroupLLC/yourtube/releases) |

**2 of 37 apps have a binary anyone can download.** 28 carry a release tag, so most of those tags are empty — they look like a release on the Releases page with nothing attached to install.

To produce them:

```sh
# from the Actions tab: “Publish test builds”, or locally:
bundle exec fastlane publish_artifacts platform:android apps:all
bundle exec fastlane publish_artifacts platform:ios apps:all
```

Nothing will publish until `AGL_PACKAGES_TOKEN` exists with **write** access —
see [PENDING.md](PENDING.md).
