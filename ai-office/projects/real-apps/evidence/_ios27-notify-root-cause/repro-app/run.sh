#!/bin/bash
# run.sh <udid> <label> <steps> <fresh:1|0> [seconds]
UDID=$1; LABEL=$2; STEPS=$3; FRESH=$4; SECS=${5:-15}
BID=ai.americangroup.qa.flnRepro
APP=/tmp/agl-fln-repro/app/build/ios/iphonesimulator/Runner.app
OUT=/tmp/agl-fln-repro/out/$LABEL
xcrun simctl terminate $UDID $BID >/dev/null 2>&1
if [ "$FRESH" = 1 ]; then xcrun simctl uninstall $UDID $BID >/dev/null 2>&1; xcrun simctl install $UDID $APP; fi
xcrun simctl launch --console-pty --terminate-running-process $UDID $BID -steps "$STEPS" > $OUT.log 2>&1 &
LPID=$!
sleep $SECS
xcrun simctl io $UDID screenshot $OUT.png >/dev/null 2>&1
xcrun simctl terminate $UDID $BID >/dev/null 2>&1
sleep 1; kill $LPID 2>/dev/null
grep -E 'FLNPROBE|FLNDART' $OUT.log | sed -E 's/^.*FLNPROBE //' | grep -v '^.*FLNDART' | cut -c1-200
