#!/bin/zsh
# The 29 apps without crash reporting are waiting on Firebase being enabled for
# americangroupllc-agl2 / -agl3. Both GCP projects exist and Firebase lists them
# under availableProjects, but POST :addFirebase answers with an HTML 404 from
# this machine (every other method on the same host returns normal JSON), so it
# has to be run once from a normal shell:
#
#     firebase login
#     firebase projects:addfirebase americangroupllc-agl2
#     firebase projects:addfirebase americangroupllc-agl3
#
# This polls every 5 minutes for 12 hours and registers the remaining apps the
# moment either project becomes a Firebase project.
G=~/google-cloud-sdk/bin/gcloud
LOG=~/agl/.dist/firebase-watch.log
end=$(( $(date +%s) + 12*3600 ))
while [ $(date +%s) -lt $end ]; do
  T=$($G auth print-access-token --account=rainbow472.sri@gmail.com 2>/dev/null)
  ready=0
  for P in americangroupllc-agl2 americangroupllc-agl3; do
    code=$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $T" \
      -H "x-goog-user-project: americangroupllc-5bdfc" \
      "https://firebase.googleapis.com/v1beta1/projects/$P")
    [ "$code" = "200" ] && ready=$((ready+1))
  done
  if [ "$ready" -gt 0 ]; then
    echo "[$(date)] $ready project(s) now Firebase-enabled — registering the rest" >> $LOG
    python3 ~/agl/agl-manifest/scripts/firebase_register.py --all --commit >> $LOG 2>&1
    exit 0
  fi
  echo "[$(date)] agl2/agl3 not Firebase projects yet" >> $LOG
  sleep 300
done
