#!/usr/bin/env bash
set -euo pipefail

topdir="$PWD"

. ./plover_build_utils/functions.sh
. ./osx/make_common.sh

PLATFORM="${1:-}"
PACKAGE="${2:-}"
if [[ -z "$PLATFORM" || -z "$PACKAGE" ]]; then
  echo "❌ Usage: $0 <platform-string> <package>" >&2
  echo "   e.g.: $0 macosx_12_0_universal2 plover-5.0.0" >&2
  exit 1
fi

APP="$topdir/dist/Plover.app"
[[ -d "$APP" ]] || { echo "❌ App not found: $APP. Run bdist_app first."; exit 1; }

DMG="$topdir/dist/${PACKAGE}-${PLATFORM}.dmg"

# Build DMG via dmgbuild
echo "Building DMG → $DMG"
python3 -m dmgbuild -s osx/dmg_resources/settings.py "Plover" "$DMG"

# --- Codesign (with Developer ID if configured) ---
# Required envs when enabled:
#   MACOS_CODESIGN_ENABLED=1
#   MACOS_CODESIGN_IDENTITY
# Optional envs when enabled:
#   MACOS_CODESIGN_KEYCHAIN
if [[ "${MACOS_CODESIGN_ENABLED:-0}" == "1" ]]; then
  require_env MACOS_CODESIGN_IDENTITY
  echo "Signing with identity $MACOS_CODESIGN_IDENTITY: $DMG"

  cs_args=(--force --timestamp -s "$MACOS_CODESIGN_IDENTITY")
  if [[ -n "${MACOS_CODESIGN_KEYCHAIN:-}" ]]; then
    cs_args+=(--keychain "$MACOS_CODESIGN_KEYCHAIN")
    echo "Using keychain: $MACOS_CODESIGN_KEYCHAIN"
  fi
  run_quiet /usr/bin/codesign "${cs_args[@]}" "$DMG"

  echo "✅ Code signing complete"
fi
# --- End codesign ---

# Notarize & staple DMG
notarize_and_staple_if_enabled "$DMG"

echo "🎉 DMG ready: $DMG"
