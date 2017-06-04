#!/bin/bash

set -e

. ./utils/functions.sh

setup()
{
  # Install Python.
  run mkdir -p "$downloads"
  installer_url='https://www.python.org/ftp/python/3.5.3/python-3.5.3-macosx10.6.pkg'
  installer_md5='6f9ee2ad1fceb1a7c66c9ec565e57102'
  installer_pkg="$downloads/python35.pkg"
  for retry in $(seq 3)
  do
    if ! [ -r "$dst" ] && ! run curl --show-error --silent -o "$installer_pkg" "$installer_url"
    then
      err "python download failed"
      run rm -f "$installer_pkg"
      continue
    fi
    if [ $opt_dry_run -eq 0 ] && [ "$(md5 -q "$installer_pkg")" != "$installer_md5" ]
    then
      err "python md5 did not match"
      run rm -f "$installer_pkg"
      continue
    fi
    break
  done
  run sudo installer -pkg "$installer_pkg" -target /

  # Setup development environment.
  bootstrap_dev --user
}

build()
{
  run git fetch --quiet --unshallow
  run "$python" setup.py patch_version
  run "$python" setup.py test
  run "$python" setup.py bdist_dmg
  run mv dist/*.dmg "$CIRCLE_ARTIFACTS/"
}

deploy()
{
  artifact="$(echo -n "$CIRCLE_ARTIFACTS"/*.dmg)"
  github_release="$downloads/circle_github_release_darwin-amd64.tar.bz2"
  github_release_url='https://github.com/aktau/github-release/releases/download/v0.7.2/darwin-amd64-github-release.tar.bz2'
  github_release_sha1='16d40bcb4de7e29055789453f0d5fdbf1bfd3b49'
  github_release_exe='./bin/darwin/amd64/github-release'
  github_release_opts=(--user openstenoproject --repo plover --tag "$("$python" ./setup.py --version)")
  run [ -r "$artifact" ]
  run "$python" -m utils.download "$github_release_url" "$github_release_sha1" "$github_release"
  run tar xvjf "$github_release"
  run "$github_release_exe" release "${github_release_opts[@]}" --draft
  run "$github_release_exe" upload "${github_release_opts[@]}" --file "$artifact" --name "${artifact#*/}"
}

[ "$CIRCLE_BUILD_IMAGE" == 'osx' ]
[ $# -eq 1 ]

python='python3'

"$1"
