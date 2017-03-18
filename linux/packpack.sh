#!/bin/bash

set -e

. ./utils/functions.sh

BUILD_DIR="build/packpack"
DIST_DIR="dist"

opt_no_pull=0

parse_opts args "$@"
set -- "${args[@]}"

while [ $# -ne 0 ]
do
  case "$1" in
    --no-pull)
      opt_no_pull=1
      ;;
    -*)
      err "invalid option: $1"
      exit 1
      ;;
    *)
      break
      ;;
  esac
  shift
done

[ $# -eq 1 ]

REPO='plover/packpack'
case "$1" in
  rawhide)
    OS='fedora'
    DIST='rawhide'
    EXT='noarch.rpm'
    TARGET="package"
    ;;
  trusty)
    OS='ubuntu'
    DIST='trusty'
    EXT='deb'
    TARGET="package"
    ;;
  xenial)
    OS='ubuntu'
    DIST='xenial'
    EXT='deb'
    TARGET="package"
    ;;
  *)
    err "unsupported target: $1"
    exit 1
    ;;
esac
shift

NAME='plover'
VERSION="$(./setup.py --version)"
SDIST="$DIST_DIR/$NAME-$VERSION.tar.xz"

run rm -rf "$BUILD_DIR"
run mkdir -p "$BUILD_DIR" "$DIST_DIR" .cache
run ./setup.py -q sdist --format=xztar
run cp "$SDIST" "$BUILD_DIR/"
cmd=(env)
if [ $opt_no_pull -ne 0 ]
then
  cmd+=(NO_PULL=1)
fi
cmd+=(
  BUILDDIR="$PWD/$BUILD_DIR" CACHE_DIR="$PWD/.cache"
  DOCKER_REPO="$REPO"
  OS="$OS" DIST="$DIST"
  PRODUCT="$NAME" VERSION="$VERSION"
  packpack "$TARGET"
)
run "${cmd[@]}"
run_eval "mv '$BUILD_DIR/'*.$EXT '$DIST_DIR/'"
