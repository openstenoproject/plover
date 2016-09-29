#!/bin/bash

set -e

if [ $# -ne 2 ]
then
  exit 1
fi

app="$1"
dmg="$2"

name='plover'
tmpdir='build/dmg'
tmpdmg="$tmpdir/template.dmg"
mpoint="$tmpdir/plover_mountpoint"

[ -r "$app" ]
mkdir -p "$tmpdir"
gunzip -c osx/plover_template.dmg.gz >"$tmpdmg"
hdiutil resize -size 100m "$tmpdmg"
mkdir "$mpoint"
hdiutil attach "$tmpdmg" -noautoopen -quiet -mountpoint "$mpoint"
rm -rf "$mpoint"/*.app
ditto "$app" "$mpoint/$name.app"
hdiutil detach "$(hdiutil info | grep "$mpoint" | grep Apple_HFS | cut -f1)"
rmdir "$mpoint"
hdiutil convert "$tmpdmg" -format UDZO -imagekey zlib-level=9 -o "$dmg"
rm "$tmpdmg"
rmdir "$tmpdir"
