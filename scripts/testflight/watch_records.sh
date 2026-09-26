#!/bin/zsh
# Every 5 minutes: which apps now have an App Store Connect record but no
# TestFlight build? Ship them. Lets a person create records in App Store Connect
# while delivery keeps up on its own. Stops after 12 hours.
source ~/agl/agl-manifest/scripts/testflight/env.sh
cd ~/agl/agl-manifest/scripts/testflight || exit 1
end=$(( $(date +%s) + 12*3600 ))
while [ $(date +%s) -lt $end ]; do
  have=$(bundle exec ruby records_present.rb 2>/dev/null)
  todo=$(python3 - "$have" <<'PY'
import json,sys
have=set(sys.argv[1].split()); res=json.load(open('/Users/spatchava/agl/.dist/ios-batch/results.json'))
# CodeDeal compiles (it shipped to Play at v16 on 2026-09-25).
# radiotune used to be skipped because Apple rejected
# its build in processing, but that was against the old com.americangroup.radiotune
# record; under the new identifier it should be attempted and the failure logged
# rather than silently passed over.
skip={"CodeDeal"}
print(",".join(r for r in sorted(have) if res.get(r,{}).get("status")!="uploaded" and r not in skip))
PY
)
  if [ -n "$todo" ]; then
    echo "[watch_records $(date +%H:%M)] shipping: $todo" >> ~/agl/.dist/ios-batch/batch.log
    python3 run_batch.py --apps "$todo" >> ~/agl/.dist/ios-batch/batch.log 2>&1
  fi
  sleep 300
done
