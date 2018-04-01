#!/usr/bin/env bash

# Usage: ./setup.py bdist_app
# $1: wheel name
# $2: package name
set -e

. ./plover_build_utils/functions.sh

python='python3'
osx_dir="$(dirname "$0")"
plover_dir="$(dirname "$osx_dir")"
plover_wheel="$plover_dir/dist/$1.whl"
PACKAGE="$2"

echo "Making Plover.app with Plover wheel $plover_wheel"

# Get Plover's version
plover_version="$("$python" -c "from plover import __version__; print(__version__)")"

# Find system Python
python3_bin_dir="$(python3 -c 'import os, sys; print(os.path.dirname(os.path.realpath(sys.executable)))')"
python3_dir="$(dirname "$python3_bin_dir")"
py_version="$(basename "$python3_dir")" # e.g. 3.6
echo "System python3 is found at: $python3_dir"

# App to build
app_dir="$plover_dir/build/$PACKAGE.app"
app_dist_dir="$plover_dir/dist/Plover.app"

rm -rf "$app_dir"{,.fat} "$app_dist_dir"

# E.g. python3.6 (name of python executable)
target_python="python${py_version}"
# Main library folder in App
target_dir="$app_dir/Contents/Frameworks"

# Make skeleton
mkdir -p "$target_dir"
mkdir "$app_dir/Contents/MacOS"
mkdir "$app_dir/Contents/Resources"

# Copy Python launcher
cp "$python3_dir/Resources/Python.app/Contents/MacOS/Python" "$target_dir/${target_python}"

# Copy over system dependencies for Python
"$python" -m macholib standalone "$app_dir"

# Make site-packages local
python_home="$target_dir/Python.framework/Versions/$py_version/"
# We want pip to install packages to $target_libs
target_libs="$python_home/lib/$target_python"
# Delete system site-packages
rm -rf "$target_libs/site-packages"
mkdir "$target_libs/site-packages"
# Add sitecustomize.py -- adds the above site-packages to our Python's sys.path
cp "$plover_dir/osx/app_resources/sitecustomize.py" "$target_libs/sitecustomize.py"

# Switch to target Python.
python="$PWD/$target_dir/$target_python"
unset __PYVENV_LAUNCHER__

run_eval "
appdir_python()
{
  env \
    PYTHONNOUSERSITE=1 \
    "$PWD/$target_dir/$target_python" \"\$@\"
}
"
python='appdir_python'

# Install Plover and dependencies.
bootstrap_dist "$plover_wheel"

# Make launcher
plover_executable=MacOS/Plover
launcher_file="$app_dir/Contents/$plover_executable"
sed "s/pythonexecutable/$target_python/g" "$osx_dir/app_resources/plover_launcher.sh" >"$launcher_file"
chmod +x "$launcher_file"

# Copy icon
cp "$osx_dir/app_resources/plover.icns" "$app_dir/Contents/Resources/plover.icns"

# This allows notifications from our Python binary to identify as from Plover...
/usr/libexec/PlistBuddy -c 'Add :CFBundleIdentifier string "org.openstenoproject.plover"' "$app_dir/Contents/Frameworks/Info.plist"

# Setup PList for Plover
/usr/libexec/PlistBuddy -c 'Add :CFBundleDevelopmentRegion string "en"' "$app_dir/Contents/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :CFBundleIconFile string "plover.icns"' "$app_dir/Contents/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :CFBundleIdentifier string "org.openstenoproject.plover"' "$app_dir/Contents/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :CFBundleName string "Plover"' "$app_dir/Contents/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :CFBundleDisplayName string "Plover"' "$app_dir/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Add :CFBundleExecutable string \"$plover_executable\"" "$app_dir/Contents/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :CFBundlePackageType string "APPL"' "$app_dir/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string \"$plover_version\"" "$app_dir/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Add :CFBundleVersion string \"$plover_version\"" "$app_dir/Contents/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :CFBundleInfoDictionaryVersion string "6.0"' "$app_dir/Contents/Info.plist"
year=$(date '+%Y')
copyright="© $year, Open Steno Project"
/usr/libexec/PlistBuddy -c "Add :NSHumanReadableCopyright string \"$copyright\"" "$app_dir/Contents/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :NSPrincipalClass string "NSApplication"' "$app_dir/Contents/Info.plist"
/usr/libexec/PlistBuddy -c 'Add :NSAppSleepDisabled bool true' "$app_dir/Contents/Info.plist"

# Remove broken symlinks
rm "$target_dir/Python.framework/Headers"
rm "$target_dir/Python.framework/Python"
rm "$target_dir/Python.framework/Resources"
# Trim superfluous content from app
sed -e "s/\$python_version/$py_version/" -e "s/\$target_python/$target_python/" osx/app_resources/dist_blacklist.txt > build/dist_blacklist.txt
"$python" -m plover_build_utils.trim "$target_dir/Python.framework" build/dist_blacklist.txt
# Make distribution source-less
"$python" -m plover_build_utils.source_less "$target_libs" "*/pip/_vendor/distlib/*"

# Strip 32-bit support
mv "$app_dir"{,.fat}
ditto -v --arch x86_64 "$app_dir"{.fat,}

# Check requirements.
run "$python" -I -m plover_build_utils.check_requirements

mv "$app_dir" "$app_dist_dir"
