#!/bin/sh

set -e

PACKAGE='plover'
TOP_DIR="$PWD"
BUILD_DIR="$TOP_DIR/build"
DIST_DIR="$TOP_DIR/dist"

VERSION="$(python2)" <<\EOF
from __future__ import print_function
from plover import __version__

version = __version__
version = version.replace('+', '-')
version = version.replace('.g', '-g')
print(version)
EOF

BASENAME="${PACKAGE}_${VERSION}"

rm -rf "$BUILD_DIR/$BASENAME"
mkdir -p "$BUILD_DIR/$BASENAME" "$DIST_DIR"
git ls-files -z | xargs -0 cp -a --no-dereference --parents --target-directory="$BUILD_DIR/$BASENAME"
cd "$BUILD_DIR"
tar cvzf "${BASENAME%%-g*}.orig.tar.gz" "$BASENAME"
cd "$BASENAME"
dch -b -v "$VERSION" "weekly build $VERSION"
debuild -i "$@"
find .. \( -name "${BASENAME}_all.deb" -o -name "${BASENAME}_source.changes" \) -print0 | xargs -0 --no-run-if-empty mv --target-directory="$DIST_DIR"
