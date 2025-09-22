#!/usr/bin/env bash
set -euo pipefail

notarize_and_staple_if_enabled() {
  local path=$1
  local notarize_enabled="${MACOS_NOTARIZE_ENABLED:-0}"
  if [[ "$notarize_enabled" != "1" ]]; then
    echo "ℹ️ Skipping notarization for $path (MACOS_NOTARIZE_ENABLED=$notarize_enabled)"
    return 0
  fi

  local codesign_enabled="${MACOS_CODESIGN_ENABLED:-0}"
  if [[ "$codesign_enabled" != "1" ]]; then
    echo "❌️ Exiting notarization for $path: MACOS_CODESIGN_ENABLED needs to be set to 1"
    return 1
  fi

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
