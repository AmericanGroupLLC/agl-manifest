#!/bin/zsh
# Poll the Play Developer API every 5 minutes. The service account key exists and
# authenticates, but until a human grants it access in Play Console → Users and
# permissions, every call returns 403 "The caller does not have permission".
# The moment that grant lands, upload every staged bundle to internal testing.
# Gives up after 12 hours.
SA=agl-play-publisher@americangroupllc-5bdfc.iam.gserviceaccount.com
KEY=~/agl/.secrets/play-service-account.json
LOG=~/agl/.dist/play-watch.log
end=$(( $(date +%s) + 12*3600 ))
while [ $(date +%s) -lt $end ]; do
  T=$(~/google-cloud-sdk/bin/gcloud auth print-access-token --account=$SA \
        --scopes=https://www.googleapis.com/auth/androidpublisher 2>/dev/null)
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST \
    "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/com.americangroupllc.calcmaster/edits" \
    -H "Authorization: Bearer $T" -H "Content-Length: 0")
  if [ "$code" = "200" ]; then
    echo "[$(date)] access granted — uploading all bundles" >> $LOG
    PLAY_JSON_KEY_FILE=$KEY python3 ~/agl/agl-manifest/scripts/upload_play.py >> $LOG 2>&1
    exit 0
  fi
  echo "[$(date)] still HTTP $code — waiting for the Play Console grant" >> $LOG
  sleep 300
done
