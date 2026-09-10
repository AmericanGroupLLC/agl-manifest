fastlane documentation
----

# Installation

Make sure you have the latest version of the Xcode command line tools installed:

```sh
xcode-select --install
```

For _fastlane_ installation instructions, see [Installing _fastlane_](https://docs.fastlane.tools/#installing-fastlane)

# Available Actions

### validate

```sh
[bundle exec] fastlane validate
```

Analyze and test every selected app. Replaces 37 separate CI runs.

### build_all

```sh
[bundle exec] fastlane build_all
```

Build every selected app for a platform without signing or uploading.

### batch_lane

```sh
[bundle exec] fastlane batch_lane
```

Run one of each app's own lanes across the batch: platform:, lane:, apps:

### batch

```sh
[bundle exec] fastlane batch
```



### publish_artifacts

```sh
[bundle exec] fastlane publish_artifacts
```

Build installable artifacts and publish them to each app's GitHub Releases

----

This README.md is auto-generated and will be re-generated every time [_fastlane_](https://fastlane.tools) is run.

More information about _fastlane_ can be found on [fastlane.tools](https://fastlane.tools).

The documentation of _fastlane_ can be found on [docs.fastlane.tools](https://docs.fastlane.tools).
