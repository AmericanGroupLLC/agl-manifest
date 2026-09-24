export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export PATH="$HOME/agl/.flutter-sdk/bin:$HOME/.rbenv/shims:$PATH"
export ASC_KEY_ID=UV8NYF9767
export ASC_ISSUER_ID=ec93cc91-97c2-4b03-860b-697d7ec5d1fb
export ASC_KEY_CONTENT="$(base64 -i "$HOME/agl/.secrets/AuthKey_UV8NYF9767.p8" | tr -d '\n')"
export ASC_KEY_PATH="$HOME/agl/.secrets/AuthKey_UV8NYF9767.p8"
export APPLE_TEAM_ID=TLH7Z3G27A
export BUILD_NUMBER="$(date +%Y%m%d%H)"
export FASTLANE_SKIP_UPDATE_CHECK=1 FASTLANE_HIDE_CHANGELOG=1 FASTLANE_OPT_OUT_USAGE=1
export BUNDLE_GEMFILE="$HOME/agl/agl-manifest/Gemfile"
export FASTLANE_USER=rainbow472.sri@gmail.com
# Unset, not set-to-empty. spaceship tests whether FASTLANE_SESSION is present,
# not whether it is non-empty, so `FASTLANE_SESSION=` makes it try to reuse a
# blank cookie and fail the login instead of prompting. Exporting a real value
# afterwards still works — this only clears a leftover.
unset FASTLANE_SESSION 

# An Apple ID web session, when one has been captured. The API key cannot create
# an app record or publish App Privacy answers; the iris host behind App Store
# Connect does both and takes a session instead. Capture one with
# `bundle exec fastlane spaceauth -u "$FASTLANE_USER"` and paste it into the file
# below; it lasts about a month. Absent, everything that only needs the key
# still works.
if [ -s "$HOME/agl/.secrets/fastlane-session" ]; then
  export FASTLANE_SESSION="$(cat "$HOME/agl/.secrets/fastlane-session")"
fi
