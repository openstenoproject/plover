#!/bin/bash

set -e

. ./utils/functions.sh

topdir="$PWD"
distdir="$topdir/dist"
builddir="$topdir/build/appimage"
appdir="$builddir/plover.AppDir"
cachedir="$topdir/.cache/appimage"
wheel=''
python='python3'
make_opts=(-s)
opt_ccache=0
opt_optimize=0

while [ $# -ne 0 ]
do
  case "$1" in
    -O)
      opt_optimize=1
      ;;
    -c|--ccache)
      opt_ccache=1
      ;;
    -j|--jobs)
      make_opts+=("-j$2")
      shift
      ;;
    -p|--python)
      python="$2"
      shift
      ;;
    -w|--wheel)
      wheel="$2"
      shift
      ;;
    -*)
      err "invalid option: $1"
      exit 1
      ;;
  esac
  shift
done

version="$("$python" -c 'from plover import __version__; print(__version__)')"
appimage="$distdir/plover-$version-x86_64.AppImage"

run rm -rf "$builddir"
run mkdir -p "$appdir" "$cachedir" "$distdir"

# Download dependencies.
run "$python" -m utils.download 'https://github.com/probonopd/AppImages/raw/6ca06be6d68606a18a90ebec5aebfd74e8a973c5/functions.sh' '3155bde5f40fd4aa08b3a76331936bd5b2e6b781' "$cachedir/functions.sh"
run "$python" -m utils.download 'https://github.com/probonopd/AppImageKit/releases/download/8/appimagetool-x86_64.AppImage' 'e756ecac69f393c72333f8bd9cd3a5f87dc175bf' "$cachedir/appimagetool"
run "$python" -m utils.download 'https://www.python.org/ftp/python/3.5.3/Python-3.5.3.tar.xz' '127121fdca11e735b3686e300d66f73aba663e93'
run "$python" -m utils.download 'http://ftp.debian.org/debian/pool/main/w/wmctrl/wmctrl_1.07.orig.tar.gz' 'a123019a7fd5adc3e393fc1108cb706268a34e4d'
run "$python" -m utils.download 'http://ftp.debian.org/debian/pool/main/w/wmctrl/wmctrl_1.07-7.debian.tar.gz' 'e8ac68f7600907be5489c0fd9ffcf2047daaf8cb'

# Generate Plover wheel.
if [ -z "$wheel" ]
then
  run "$python" setup.py bdist_wheel
  wheel="$distdir/plover-$version-py2.py3-none-any.whl"
fi

if [ $opt_ccache -ne 0 ]
then
   run export CCACHE_DIR="$topdir/.cache/ccache" CCACHE_BASEDIR="$buildir" CC='ccache gcc'
 fi

# Build Python.
run tar xf "$downloads/Python-3.5.3.tar.xz" -C "$builddir"
info '('
(
run cd "$builddir/Python-3.5.3"
cmd=(
  ./configure
  --cache-file="$cachedir/python.config.cache"
  --prefix="$appdir/usr"
  --enable-ipv6
  --enable-loadable-sqlite-extensions
  --enable-shared
  --with-threads
  --without-ensurepip
)
if [ $opt_optimize -ne 0 ]
then
  cmd+=(--enable-optimizations)
fi
run "${cmd[@]}"
run make "${make_opts[@]}"
run make "${make_opts[@]}" install >/dev/null
)
info ')'

# Build wmctrl.
run tar xf "$downloads/wmctrl_1.07.orig.tar.gz" -C "$builddir"
info '('
(
run cd "$builddir/wmctrl-1.07"
run tar xf "$downloads/wmctrl_1.07-7.debian.tar.gz"
run patch -p1 -i debian/patches/01_64-bit-data.patch
run ./configure \
  --cache-file="$cachedir/wmctrl.config.cache" \
  --prefix="$appdir/usr" \
  ;
run make "${make_opts[@]}" install
)
info ')'

appdir_python()
{
  env LD_LIBRARY_PATH="$appdir/usr/lib" "$appdir/usr/bin/python3.5" -s "$@"
}
python='appdir_python'

# Install Plover and dependencies.
bootstrap_dist "$wheel"

# Note: those will re-appear in their respective
# locations when creating the AppImage...
# ¯\_(ツ)_/¯
run mv "$appdir/usr/share/applications/plover.desktop" "$appdir/plover.desktop"
run mv "$appdir/usr/share/pixmaps/plover.png" "$appdir/plover.png"

# Trim the fat.
run "$python" -m utils.trim "$appdir" linux/appimage/blacklist.txt

# Make distribution source-less.
run "$python" -m utils.source_less "$appdir/usr/lib/python3.5" '*/pip/_vendor/distlib/*'

# Add launcher.
# Note: don't use AppImage's AppRun because
# it will change the working directory.
run cp linux/appimage/apprun.sh "$appdir/AppRun"

# Finalize AppDir.
(
run . "$cachedir/functions.sh"
run cd "$appdir"
# Add desktop integration.
run get_desktopintegration 'plover'
# Fix missing system dependencies.
run copy_deps; run copy_deps; run copy_deps
run move_lib
# Move usr/include out of the way to preserve usr/include/python3.5m.
run mv usr/include usr/include.tmp
run delete_blacklisted
run mv usr/include.tmp usr/include
)

# Strip binaries.
strip_binaries()
{
  chmod u+w -R "$appdir"
  {
    printf '%s\0' "$appdir/usr/bin/python3.5"
    find "$appdir" -type f -regex '.*\.so\(\.[0-9.]+\)?$' -print0
  } | xargs -0 --no-run-if-empty --verbose -n1 strip
}
run strip_binaries

# Remove empty directories.
remove_emptydirs()
{
  find "$appdir" -type d -empty -print0 | xargs -0 --no-run-if-empty rmdir -vp --ignore-fail-on-non-empty
}
run remove_emptydirs

# Create the AppImage.
# Note: extract appimagetool so fuse is not needed.
info '('
(
run cd "$builddir"
run chmod +x "$cachedir/appimagetool"
run "$cachedir/appimagetool" --appimage-extract
run env VERSION="$version" ./squashfs-root/AppRun --no-appstream --verbose "$appdir" "$appimage"
)
info ')'
