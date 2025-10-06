#!/usr/bin/env bash
set -e

# Sign and notarize + staple a .dmg image.
# Enabled with:
#   MACOS_NOTARIZE_ENABLED=1
# Required envs when notarization is enabled:
#   MACOS_CODESIGN_IDENTITY
#   MACOS_NOTARIZE_TEAM_ID
#   MACOS_NOTARIZE_KEY_ID
#   MACOS_NOTARIZE_ISSUER_ID
#   MACOS_NOTARIZE_KEY_CONTENTS
# Optional:
#   MACOS_CODESIGN_KEYCHAIN, e.g. plover-dev.keychain

dmg_path="${1:-}"
if [[ -z "$dmg_path" || ! -f "$dmg_path" ]]; then
  echo "❌ Usage: $0 /path/to/file.dmg" >&2
  exit 1
fi

. ./plover_build_utils/functions.sh
. ./osx/notarize_common.sh

notarize_enabled="${MACOS_NOTARIZE_ENABLED:-0}"
if [[ "$notarize_enabled" != "1" ]]; then
  echo "ℹ️ Skipping DMG signing & notarization (MACOS_NOTARIZE_ENABLED=$notarize_enabled)"
  exit 0
fi

# --- Codesign ---
require_env MACOS_CODESIGN_IDENTITY
echo "Signing with identity $MACOS_CODESIGN_IDENTITY: $dmg_path"

cs_args=(--force --timestamp -s "$MACOS_CODESIGN_IDENTITY")
if [[ -n "${MACOS_CODESIGN_KEYCHAIN:-}" ]]; then
  cs_args+=(--keychain "$MACOS_CODESIGN_KEYCHAIN")
  echo "Using keychain: $MACOS_CODESIGN_KEYCHAIN"
fi
run_quiet /usr/bin/codesign "${cs_args[@]}" "$dmg_path"

echo "✅ Code signing complete"
# --- End codesign ---

# Notarize & staple DMG
notarize_and_staple "$dmg_path"

echo "🎉 DMG ready: $dmg_path"
