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

# Helper to extract an AppImage so it can be used without needing fuse.
extract_appimage()
{(
  appimage="$1"
  destdir="$2"

  tmpdir="$(mktemp -d "$(dirname "$destdir")/squashfs-root.XXXXXXXXXX")"
  cd "$tmpdir"
  chmod +x "$appimage"
  "$appimage" --appimage-extract >/dev/null
  mv squashfs-root "$destdir"
  cd ..
  rmdir "$tmpdir"
)}

version="$("$python" -c 'from plover import __version__; print(__version__)')"
appimage="$distdir/plover-$version-x86_64.AppImage"

run rm -rf "$builddir"
run mkdir -p "$appdir" "$cachedir" "$distdir"

# Fetch some helpers.
# Note:
# - extract AppImages so fuse is not needed.
# - we start with zsync2 and do two passes
#   so it can update itself as needed.
while read tool url sha1;
do
  if [ ! -r "$cachedir/$tool" ]
  then
    run wget -O "$cachedir/$tool" "$url"
  else
    if [ -n "$zsync2" ]
    then
      run_eval "(cd '$cachedir' && '$zsync2' -o '$cachedir/$tool' '$url.zsync')"
    fi
  fi
  run extract_appimage "$cachedir/$tool" "$builddir/$tool"
  run_eval "$tool='$builddir/$tool/AppRun'"
done <<\EOF
zsync2        https://github.com/AppImage/zsync2/releases/download/continuous/zsync2-156-10e85c0-x86_64.AppImage
zsync2        https://github.com/AppImage/zsync2/releases/download/continuous/zsync2-156-10e85c0-x86_64.AppImage
linuxdeploy   https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
appimagetool  https://github.com/probonopd/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
EOF

# Generate Plover wheel.
if [ -z "$wheel" ]
then
  run "$python" setup.py bdist_wheel
  wheel="$distdir/plover-$version-py3-none-any.whl"
fi

# Setup Python distribution.
pydist="$appdir/usr"
run_eval "$("$python" linux/appimage/pyinfo.py)"
run mkdir -p "$pydist/"{bin,lib,"$pystdlib"/..,"$pyinclude"/..}
run cp "$pyexe" "$pydist/bin/python"
run cp -a "$pyprefix/$pyinclude" "$pydist/$pyinclude/../"
run cp -a "$pyprefix/lib/$pyldlib"* "$pyprefix/lib/$pypy3lib" "$pydist/lib/"
run_eval "(cd '$pyprefix' && find '$pystdlib' \\( -name __pycache__ -o -path '$pypurelib' -o -path '$pyplatlib' \\) -prune -o -type f -not -name '*.py[co]' -print0 | xargs -0 cp --parents -t '$pydist')"
run rm -f "$pydist/$pystdlib/sytecustomize.py"
run mkdir -p "$pydist/"{"$pypurelib","$pyplatlib"}

# Switch to AppDir python.
run cp linux/appimage/apprun.sh "$appdir/AppRun"
run_eval "appdir_python(){ env PYTHONNOUSERSITE=1 '$appdir/AppRun' --python \"\$@\"; }"
python='appdir_python'

"$python" --version

# Install Plover and dependencies.
bootstrap_dist "$wheel"

# Trim the fat.
run cp linux/appimage/blacklist.txt "$builddir/blacklist.txt"
run sed -e "s/\${pyversion}/$pyversion/g" -i "$builddir/blacklist.txt"
run "$python" -m plover_build_utils.trim "$appdir" "$builddir/blacklist.txt"

# Make distribution source-less.
run "$python" -m plover_build_utils.source_less "$pydist/$purelib" "$pydist/$platlib" '*/pip/_vendor/distlib/*'

# Avoid possible permission errors.
run chmod u+w -R "$appdir"

# Strip binaries.
strip_binaries()
{
  {
    printf '%s\0' "$appdir/usr/bin/python"
    find "$appdir" -type f -regex '.*\.so\(\.[0-9.]+\)?$' -print0
  } | xargs -0 --no-run-if-empty strip
}
run strip_binaries

# Finalize the AppDir.
# Note:
# - use a custom launcher that does not change the working directory.
# - temporarily move PyQt5 out of the way so linuxdeploy does not try
#   to bundle its system dependencies.
run mv "$pydist/$pypurelib/PyQt5" "$builddir"
run "$linuxdeploy" \
  --desktop-file='application/plover.desktop' \
  --icon-file='plover/assets/plover.png' \
  --appdir="$appdir" \
  --verbosity=2
run mv "$builddir/PyQt5" "$pydist/$pypurelib/PyQt5"

# Remove empty directories.
remove_emptydirs()
{
  find "$appdir" -type d -empty -print0 |
  xargs -0 --no-run-if-empty rmdir -vp --ignore-fail-on-non-empty
}
run remove_emptydirs

# Check requirements.
run env -i "$appdir/AppRun" --python -I -m plover_build_utils.check_requirements

# Create the AppImage.
run env VERSION="$version" "$appimagetool" --no-appstream "$appdir" "$appimage"
