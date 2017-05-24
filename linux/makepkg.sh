#!/bin/bash

set -e

BUILD_DIR='build/archlinux'
DIST_DIR='dist'

. ./utils/functions.sh

NAME='plover'
VERSION="$(./setup.py --version)"
SDIST="$DIST_DIR/$NAME-$VERSION.tar.gz"

run rm -rf "$BUILD_DIR"
run mkdir -p "$BUILD_DIR/src" "$DIST_DIR"
run ./setup.py -q sdist --format=gztar
run tar xf "$SDIST" -C "$BUILD_DIR/src"
run_eval "sed 's/^pkgver=.*\$/pkgver=$VERSION/' archlinux/PKGBUILD >'$BUILD_DIR/PKGBUILD'"
run_eval "(cd '$BUILD_DIR' && env PKGDEST='$PWD/$DIST_DIR' makepkg --noextract --force ${@@Q})"
