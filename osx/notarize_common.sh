#!/usr/bin/env bash
set -euo pipefail

notarize_and_staple() {
  local path=$1
  require_env MACOS_NOTARIZE_TEAM_ID
  require_env MACOS_NOTARIZE_KEY_ID
  require_env MACOS_NOTARIZE_ISSUER_ID
  require_env MACOS_NOTARIZE_KEY_CONTENTS

  local workdir; workdir="$(mktemp -d)"; trap 'rm -rf "$workdir"' RETURN
  local zip="$workdir/$(basename "$path").zip"
  echo "Zipping for notarization → $zip"
  ditto -c -k --keepParent "$path" "$zip"

  local key_path="$workdir/AuthKey_${MACOS_NOTARIZE_KEY_ID}.p8"
  umask 077
  printf '%s' "$MACOS_NOTARIZE_KEY_CONTENTS" > "$key_path"

  echo "Submitting to notary service (team=$MACOS_NOTARIZE_TEAM_ID, key_id=$MACOS_NOTARIZE_KEY_ID)…"
  xcrun notarytool submit "$zip" \
    --key "$key_path" \
    --key-id "$MACOS_NOTARIZE_KEY_ID" \
    --issuer "$MACOS_NOTARIZE_ISSUER_ID" \
    --team-id "$MACOS_NOTARIZE_TEAM_ID" \
    --wait --timeout 20m --progress

  echo "Stapling ticket to $path..."
  xcrun stapler staple "$path"
  echo "Validating staple for $path..."
  xcrun stapler validate "$path"
  echo "✅ Notarization complete for $path"
}
