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

while [ $# -ne 0 ]
do
  case "$1" in
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
run "$python" -m plover_build_utils.download 'https://github.com/AppImage/pkg2appimage/raw/ed1d385282a6aa6c9a93b52296f20555adf9bae7/functions.sh' 'e04404e00dfdf2cd869f892417befa46bbd4e24e' "$cachedir/functions.sh"
run "$python" -m plover_build_utils.download 'https://github.com/probonopd/AppImageKit/releases/download/11/appimagetool-x86_64.AppImage' 'f3bc2b45d3a9f3c62915ace123a7f8063cfc1822' "$cachedir/appimagetool"

# Generate Plover wheel.
if [ -z "$wheel" ]
then
  run "$python" setup.py bdist_wheel
  wheel="$distdir/plover-$version-py3-none-any.whl"
fi

# Setup Python distribution.
run_eval "$("$python" linux/appimage/pyinfo.py)"
pydist="$appdir/usr"
run mkdir -p "$pydist/"{bin,lib,"$pystdlib"/..,"$pyinclude"/..}
run cp "$pyexe" "$pydist/bin/python"
info '('
(
run cd "$pyprefix"
run cp -a "$pyprefix/$pyinclude" "$pydist/$pyinclude/../"
run cp -a lib/"$pyldlib"* lib/"$pypy3lib" "$pydist/lib/"
run_eval "find '$pystdlib' \\( -name __pycache__ -o -path '$pypurelib' -o -path '$pyplatlib' \\) -prune -o -type f -not -name '*.py[co]' -print0 | xargs -0 cp --parents -t '$pydist'"
)
info ')'
run rm -f "$pydist/$pystdlib/sytecustomize.py"
run mkdir -p "$pydist/"{"$pypurelib","$pyplatlib"}

run_eval "
appdir_python()
{
  env \
    PYTHONNOUSERSITE=1 \
    LD_LIBRARY_PATH=\"$appdir/usr/lib:$appdir/usr/lib/x86_64-linux-gnu\${LD_LIBRARY_PATH+:\$LD_LIBRARY_PATH}\" \
    "$appdir/usr/bin/python" \"\$@\"
}
"
python='appdir_python'

# Install Plover and dependencies.
bootstrap_dist "$wheel"

# Add desktop integration.
run cp 'application/plover.desktop' "$appdir/plover.desktop"
run cp 'plover/assets/plover.png' "$appdir/plover.png"

# Trim the fat.
run cp linux/appimage/blacklist.txt "$builddir/blacklist.txt"
run sed -e "s/\${pyversion}/$pyversion/" -i "$builddir/blacklist.txt"
run "$python" -m plover_build_utils.trim "$appdir" "$builddir/blacklist.txt"

# Make distribution source-less.
run "$python" -m plover_build_utils.source_less "$pydist/$purelib" "$pydist/$platlib" '*/pip/_vendor/distlib/*'

# Add launcher.
# Note: don't use AppImage's AppRun because
# it will change the working directory.
run cp linux/appimage/apprun.sh "$appdir/AppRun"

# Finalize AppDir.
(
run . "$cachedir/functions.sh"
run cd "$appdir"
# Fix missing system dependencies.
# Note: temporarily move PyQt5 out of the way so
# we don't try to bundle its system dependencies.
run mv "$pydist/$pypurelib/PyQt5" "$builddir"
run copy_deps; run copy_deps; run copy_deps
run move_lib
run mv "$builddir/PyQt5" "$pydist/$pypurelib/PyQt5"
# Move usr/include out of the way to preserve usr/include/python3.7m.
run mv usr/include usr/include.tmp
run delete_blacklisted
run mv usr/include.tmp usr/include
)

# Strip binaries.
strip_binaries()
{
  chmod u+w -R "$appdir"
  {
    printf '%s\0' "$appdir/usr/bin/python"
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
