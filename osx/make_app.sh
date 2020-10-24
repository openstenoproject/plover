#!/usr/bin/env bash

set -e

. ./plover_build_utils/functions.sh

topdir="$PWD"
builddir="$topdir/build/osxapp"
appdir="$builddir/Plover.app"
distdir="$topdir/dist/Plover.app"
python='python3'
plover_wheel="$1"

echo "Making Plover.app with Plover wheel $plover_wheel."

run rm -rf "$builddir" "$distdir"
run mkdir -p "$appdir"

# Make skeleton.
frameworks_dir="$appdir/Contents/Frameworks"
resources_dir="$appdir/Contents/Resources"
macos_dir="$appdir/Contents/MacOS"
run mkdir -p "$frameworks_dir" "$resources_dir" "$macos_dir"

# Add Python framework.
py_reloc_version='f4c4110f36ac1cb60b8253c2e04eaf34804f7303'
py_home="$frameworks_dir/Python.framework/Versions/Current"
run_eval "$("$python" -c 'print("py_base_version={0}.{1}; py_version={0}.{1}.{2}".format(*__import__("sys").version_info[:3]))')"
run "$python" -m plover_build_utils.download "https://github.com/gregneagle/relocatable-python/archive/$py_reloc_version.zip" 'cc5078733760dfa747ea24bd4b36a62f9d0f0b7e'
run rm -rf "build/relocatable-python-$py_reloc_version"
run unzip -d build "$downloads/f4c4110f36ac1cb60b8253c2e04eaf34804f7303.zip"
run "$python" "build/relocatable-python-$py_reloc_version/make_relocatable_python_framework.py" --python-version="$py_version" --no-unsign --pip-requirements=/dev/null --destination="$frameworks_dir"
run mv "$py_home/bin"/{"python$py_base_version",python}
run ln -s "../../lib/python$py_base_version/site-packages/certifi/cacert.pem" "$py_home/etc/openssl/cert.pem"

# Switch to target Python.
run_eval "appdir_python() { env PYTHONNOUSERSITE=1 "$py_home/bin/python" \"\$@\"; }"
python='appdir_python'
unset __PYVENV_LAUNCHER__

# Install Plover and dependencies.
bootstrap_dist "$plover_wheel"

# Create launcher.
run gcc -Wall -O2 'osx/app_resources/plover_launcher.c' -o "$macos_dir/Plover"

# Copy icon.
run cp 'osx/app_resources/plover.icns' "$resources_dir/plover.icns"

# Get Plover's version.
plover_version="$("$python" -c 'print(__import__("plover").__version__)')"

# Setup PList for Plover.
run cp 'osx/app_resources/Info.plist' "$appdir/Contents/Info.plist"
run sed -e "s/\$version/$plover_version/" -e "s/\$year/$(date '+%Y')/" -i '' "$appdir/Contents/Info.plist"

# Trim superfluous content.
run cp osx/app_resources/dist_blacklist.txt "$builddir/dist_blacklist.txt"
run sed -e "s/\$python_version/$py_version/" -e "s/\$python_base_version/$py_base_version/" -i '' "$builddir/dist_blacklist.txt"
run "$python" -m plover_build_utils.trim "$py_home" "$builddir/dist_blacklist.txt"

# Make distribution source-less.
run "$python" -m plover_build_utils.source_less "$py_home/lib" "*/pip/_vendor/distlib/*"

# Strip 32-bit support
run mv "$appdir"{,.fat}
run ditto -v --arch x86_64 "$appdir"{.fat,}

# Check requirements.
run "$python" -I -m plover_build_utils.check_requirements

run mv "$appdir" "$distdir"
