#!/usr/bin/env bash
# Push the store credentials into a repository's GitHub secrets so the Fastlane
# release workflow can talk to App Store Connect and Google Play directly.
#
#   scripts/set-store-secrets.sh AmericanGroupLLC/CalcMaster
#   scripts/set-store-secrets.sh --all          # every Flutter app in ~/agl
#
# Reads the key material from a local, gitignored directory. Nothing is echoed.
#
#   export AGL_SECRETS_DIR=~/agl-secrets
#     AuthKey_UV8NYF9767.p8        App Store Connect API key
#     play-service-account.json    Play Console service account
#     upload.jks                   Android upload keystore (per app, see below)
#
# Per-app keystores may be named <repo>-upload.jks; the shared upload.jks is
# used as a fallback.
#
# Everything else comes from the environment:
#   ASC_ISSUER_ID, ANDROID_KEYSTORE_PASSWORD, ANDROID_KEY_ALIAS,
#   ANDROID_KEY_PASSWORD, MATCH_GIT_URL, MATCH_PASSWORD
set -euo pipefail

SECRETS_DIR="${AGL_SECRETS_DIR:-$HOME/agl-secrets}"
ASC_KEY_ID="${ASC_KEY_ID:-UV8NYF9767}"
AGL_ROOT="${AGL_ROOT:-$HOME/agl}"

die() { echo "error: $*" >&2; exit 1; }

need_file() {
  [ -f "$1" ] || die "missing $1 — see docs/RELEASE_PIPELINE.md section 3"
}

need_env() {
  for k in "$@"; do
    [ -n "${!k:-}" ] || die "environment variable $k is not set"
  done
}

set_secret() {
  local repo="$1" name="$2" value="$3"
  printf '%s' "$value" | gh secret set "$name" --repo "$repo" --body -
  echo "    set $name"
}

apply_to_repo() {
  local repo="$1"
  local short="${repo##*/}"
  echo "  $repo"

  # ── iOS ───────────────────────────────────────────────────────────────────
  local p8="$SECRETS_DIR/AuthKey_${ASC_KEY_ID}.p8"
  need_file "$p8"
  set_secret "$repo" ASC_KEY_ID "$ASC_KEY_ID"
  set_secret "$repo" ASC_ISSUER_ID "$ASC_ISSUER_ID"
  set_secret "$repo" ASC_KEY_CONTENT "$(base64 < "$p8" | tr -d '\n')"

  if [ -n "${MATCH_GIT_URL:-}" ]; then
    set_secret "$repo" MATCH_GIT_URL "$MATCH_GIT_URL"
    set_secret "$repo" MATCH_PASSWORD "$MATCH_PASSWORD"
    [ -n "${MATCH_GIT_BASIC_AUTHORIZATION:-}" ] &&
      set_secret "$repo" MATCH_GIT_BASIC_AUTHORIZATION "$MATCH_GIT_BASIC_AUTHORIZATION"
  else
    echo "    (skipping match secrets — MATCH_GIT_URL unset)"
  fi

  # ── Android ───────────────────────────────────────────────────────────────
  local play="$SECRETS_DIR/play-service-account.json"
  need_file "$play"
  set_secret "$repo" PLAY_SERVICE_ACCOUNT_JSON "$(cat "$play")"

  local ks="$SECRETS_DIR/${short}-upload.jks"
  [ -f "$ks" ] || ks="$SECRETS_DIR/upload.jks"
  if [ -f "$ks" ]; then
    set_secret "$repo" ANDROID_KEYSTORE_BASE64 "$(base64 < "$ks" | tr -d '\n')"
    set_secret "$repo" ANDROID_KEYSTORE_PASSWORD "$ANDROID_KEYSTORE_PASSWORD"
    set_secret "$repo" ANDROID_KEY_ALIAS "$ANDROID_KEY_ALIAS"
    set_secret "$repo" ANDROID_KEY_PASSWORD "$ANDROID_KEY_PASSWORD"
  else
    echo "    (no keystore for $short — android release lane will fail until one exists)"
  fi
}

main() {
  command -v gh >/dev/null || die "gh is not installed"
  gh auth status >/dev/null 2>&1 || die "gh is not authenticated"
  need_env ASC_ISSUER_ID ANDROID_KEYSTORE_PASSWORD ANDROID_KEY_ALIAS ANDROID_KEY_PASSWORD
  [ -d "$SECRETS_DIR" ] || die "AGL_SECRETS_DIR ($SECRETS_DIR) does not exist"

  if [ "${1:-}" = "--all" ]; then
    echo "Applying to every Flutter app under $AGL_ROOT"
    for d in "$AGL_ROOT"/*/; do
      local name; name="$(basename "$d")"
      [ -d "$d/.git" ] || continue
      # Flutter project at the repo root or in mobile/
      if [ -f "$d/pubspec.yaml" ] || [ -f "$d/mobile/pubspec.yaml" ]; then
        apply_to_repo "AmericanGroupLLC/$name"
      fi
    done
  elif [ -n "${1:-}" ]; then
    apply_to_repo "$1"
  else
    die "usage: $0 <owner/repo> | --all"
  fi

  echo
  echo "Done. Verify with:  gh secret list --repo <owner/repo>"
  echo "Then run:           gh workflow run release.yml -f platform=android -f lane=beta"
}

main "$@"
