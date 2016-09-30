#! /bin/bash

set -xe

TOP_DIR="$(realpath -m "$0"/../../)"
ARCH_DIR="$TOP_DIR/archlinux"
BUILD_DIR="$TOP_DIR/build"
DIST_DIR="$TOP_DIR/dist"

. "$ARCH_DIR/PKGBUILD"
pkgver="$(cd "$TOP_DIR" && ./setup.py --version)"
src="$BUILD_DIR/src/$pkgname-$pkgver"
rm -rf "$BUILD_DIR/src" "$BUILD_DIR/pkg"
mkdir -p "$src" "$DIST_DIR"
sed "s/^pkgver=.*\$/pkgver=$pkgver/" "$ARCH_DIR/PKGBUILD" >"$BUILD_DIR/PKGBUILD"
(cd "$TOP_DIR" && git ls-files -z | xargs -0 cp -a --no-dereference --parents --target-directory="$src")

(cd "$BUILD_DIR" && env PKGDEST="$PWD/../dist" makepkg --noextract --force "$@")

