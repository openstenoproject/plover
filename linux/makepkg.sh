#!/bin/bash

set -e

BUILD_DIR='build/archlinux'
DIST_DIR='dist'

. ./utils/functions.sh

NAME='plover'
VERSION="$(./setup.py --version)"
SDIST="$NAME-$VERSION.tar.gz"

run rm -rf "$BUILD_DIR"
run mkdir -p "$BUILD_DIR" "$DIST_DIR"
run ./setup.py -q sdist -d "$BUILD_DIR" --format=gztar
run_eval "sed 's/^pkgver=.*\$/pkgver=$VERSION/;s,^source=.*,source=($SDIST),' archlinux/PKGBUILD >'$BUILD_DIR/PKGBUILD'"
run_eval "(cd '$BUILD_DIR' && env PKGDEST='$PWD/$DIST_DIR' makepkg --syncdeps --rmdeps --skipchecksums --force ${@@Q})"
