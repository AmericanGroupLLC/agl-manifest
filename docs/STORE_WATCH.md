# The scheduled store pass

```bash
python3 scripts/store_watch.py --dry-run     # see what it would do
python3 scripts/store_watch.py --remediate   # one real pass
```

Every pass reads both stores, classifies any new App Store rejection, runs
the submission gate, re-applies metadata that has drifted, and submits the
apps that are genuinely ready.

## What it will not do, deliberately

**It never resubmits an app under a 4.3 or 2.1 hold.** Apple's wording on
the 4.3 rejections:

> If the app is resubmitted without substantial improvements, it will be
> rejected again, and may be rejected for additional issues.

A timer that resubmits would do that 14 times over and put the developer
account at risk. `HOLD_GUIDELINES` in the script is a refusal list: an app
whose latest Resolution Center message cites 4.3, 4.2.6, 2.1, 4.2 or 5.1.1
is reported and skipped.

Once a person has actually changed the app:

```bash
python3 scripts/store_watch.py --clear-hold CalcMaster
```

It is submitted on the next pass if the gate passes. Holds live in
`docs/store-holds.json`; the last pass is in `docs/store-watch.json`.

## Turning the schedule on

The agent is written but **not loaded** — loading a job that runs commands
unattended needs a person:

```bash
cp ops/com.americangroupllc.storewatch.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.americangroupllc.storewatch.plist
launchctl list | grep storewatch        # confirm
```

Four passes a day at :17 past 03, 09, 15 and 21. Store state does not change
faster — Apple review takes days — and a tighter loop adds only load.

Logs: `~/agl/.dist/store-watch/`, newest symlinked as `latest.log`, kept 30
days. Stop it with `launchctl unload`.

## What the wrapper has to set

launchd runs with almost no environment. `store_watch_run.sh` sets PATH,
`AGL_ROOT` (otherwise ROOT flips to `agl-manifest/work` and takes the
Flutter SDK lookup with it), `FASTLANE_USER`, and sources
`scripts/testflight/env.sh` for the App Store Connect key. Without that last
one the pass reads an empty portfolio and reports it as healthy.

## The one thing it cannot do

Reading rejection text needs an Apple ID web session, which expires. When it
has, the pass still runs — it just cannot classify anything new, and says so
rather than assuming existing holds are stale. Refresh with:

```bash
bundle exec fastlane spaceauth -u srikanth.patchava@outlook.com
```
