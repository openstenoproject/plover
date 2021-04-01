# - zsync2's URL is unfortunately versioned,
#   so we need to use Github's API to find
#   the latest continuous release asset.
zsync2_url="$(wget -q -O - https://api.github.com/repos/AppImage/zsync2/releases/tags/continuous | sed -n 's/^\s*"browser_download_url": "\([^"]*zsync2-[^"]*-x86_64.AppImage\)"$/\1/p')"
linuxdeploy_url='https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage'
appimagetool_url='https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage'
