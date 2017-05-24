#!/bin/bash

set -e

BUILD_DIR="build/debian"
DIST_DIR="dist"

. ./utils/functions.sh

NAME='plover'
VERSION="$(./setup.py --version | sed 's/+/-/g;s/\.g/-g/')"
SDIST="$DIST_DIR/$NAME-$VERSION.tar.gz"

run rm -rf "$BUILD_DIR"
run mkdir -p "$BUILD_DIR" "$DIST_DIR"
run ./setup.py -q sdist --format=gztar
run tar xf "$SDIST" -C "$BUILD_DIR"
run cp "$SDIST" "$BUILD_DIR/plover_$VERSION.orig.tar.gz"
run cd "$BUILD_DIR/$NAME-$VERSION"
run dch -b -v "$VERSION" "automatic build $VERSION"
run debuild -i "$@"
run cd -
run mv "$BUILD_DIR/${NAME}_${VERSION}_all.deb" "$DIST_DIR/"
