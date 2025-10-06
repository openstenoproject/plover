#!/usr/bin/env bash
set -euo pipefail

topdir="$PWD"

. ./plover_build_utils/functions.sh

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
