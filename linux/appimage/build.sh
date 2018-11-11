#!/bin/bash

set -e

. ./plover_build_utils/functions.sh

topdir="$PWD"
distdir="$topdir/dist"
builddir="$topdir/build/appimage"
appdir="$builddir/plover.AppDir"
cachedir="$topdir/.cache/appimage"
wheel=''
python='python3'
make_opts=(-s)
configure_opts=(-q)
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
run "$python" -m plover_build_utils.download 'https://github.com/probonopd/AppImages/raw/f748bb63999e655cfbb70e88ec27e74e2b9bf8fd/functions.sh' 'a99457e22d24a61f42931b2aaafd41f2746af820' "$cachedir/functions.sh"
run "$python" -m plover_build_utils.download 'https://github.com/probonopd/AppImageKit/releases/download/9/appimagetool-x86_64.AppImage' 'ba71c5a03398b81eaa678207da1338c83189db89' "$cachedir/appimagetool"
run "$python" -m plover_build_utils.download 'https://www.python.org/ftp/python/3.6.7/Python-3.6.7.tar.xz' 'dd2b0a8bf9b9617c57a0070b53065286c2142994'

# Generate Plover wheel.
if [ -z "$wheel" ]
then
  run "$python" setup.py bdist_wheel
  wheel="$distdir/plover-$version-py3-none-any.whl"
fi

if [ $opt_ccache -ne 0 ]
then
   run export CCACHE_DIR="$topdir/.cache/ccache" CCACHE_BASEDIR="$buildir" CC='ccache gcc'
 fi

# Build Python.
run tar xf "$downloads/Python-3.6.7.tar.xz" -C "$builddir"
info '('
(
run cd "$builddir/Python-3.6.7"
cmd=(
  ./configure
  --cache-file="$cachedir/python.config.cache"
  --prefix="$appdir/usr"
  --enable-ipv6
  --enable-loadable-sqlite-extensions
  --enable-shared
  --with-threads
  --without-ensurepip
  ${configure_opts[@]}
)
if [ $opt_optimize -ne 0 ]
then
  cmd+=(--enable-optimizations)
fi
run "${cmd[@]}"
run make "${make_opts[@]}"
# Drop the need for ccache when installing some Python packages from source.
run sed -i 's/ccache //g' "$(find build -name '_sysconfigdata_m_*.py')"
run make "${make_opts[@]}" install >/dev/null
)
info ')'

run_eval "
appdir_python()
{
  env \
    PYTHONNOUSERSITE=1 \
    LD_LIBRARY_PATH=\"$appdir/usr/lib:$appdir/usr/lib/x86_64-linux-gnu\${LD_LIBRARY_PATH+:\$LD_LIBRARY_PATH}\" \
    "$appdir/usr/bin/python3.6" \"\$@\"
}
"
python='appdir_python'

# Install Plover and dependencies.
bootstrap_dist "$wheel"

# Add desktop integration.
run cp 'application/plover.desktop' "$appdir/plover.desktop"
run cp 'plover/assets/plover.png' "$appdir/plover.png"

# Trim the fat.
run "$python" -m plover_build_utils.trim "$appdir" linux/appimage/blacklist.txt

# Make distribution source-less.
run "$python" -m plover_build_utils.source_less "$appdir/usr/lib/python3.6" '*/pip/_vendor/distlib/*'

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
# Note: temporarily move PyQt5 out of the way so
# we don't try to bundle its system dependencies.
run mv "$appdir/usr/lib/python3.6/site-packages/PyQt5" "$builddir"
run copy_deps; run copy_deps; run copy_deps
run move_lib
run mv "$builddir/PyQt5" "$appdir/usr/lib/python3.6/site-packages"
# Move usr/include out of the way to preserve usr/include/python3.6m.
run mv usr/include usr/include.tmp
run delete_blacklisted
run mv usr/include.tmp usr/include
)

# Strip binaries.
strip_binaries()
{
  chmod u+w -R "$appdir"
  {
    printf '%s\0' "$appdir/usr/bin/python3.6"
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

# Check requirements.
run "$python" -I -m plover_build_utils.check_requirements

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
