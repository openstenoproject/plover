#!/bin/bash

set -e

. ./plover_build_utils/functions.sh

setup()
{
  installer="$downloads/python37.pkg"
  # Install Python (using the default system Python for fetching the installer).
  run python2 -m plover_build_utils.download 'https://www.python.org/ftp/python/3.7.9/python-3.7.9-macosx10.9.pkg' '51d6d52c0aeb8c9dd728f323e3011d83746504d8' "$installer"
  run sudo installer -pkg "$installer" -target /
  # Update certificates.
  run '/Applications/Python 3.7/Install Certificates.command'
  # Setup development environment.
  bootstrap_dev --user
}

build()
{
  run "$python" setup.py patch_version
  run "$python" setup.py test
  run "$python" setup.py bdist_dmg
  run mkdir -p "$CIRCLE_ARTIFACTS"
  run mv dist/*.dmg "$CIRCLE_ARTIFACTS/"
}

deploy()
{
  artifact="$(echo -n "$CIRCLE_ARTIFACTS"/*.dmg)"
  github_release="$downloads/circle_github_release_darwin-amd64.tar.bz2"
  github_release_url='https://github.com/aktau/github-release/releases/download/v0.7.2/darwin-amd64-github-release.tar.bz2'
  github_release_sha1='16d40bcb4de7e29055789453f0d5fdbf1bfd3b49'
  github_release_exe='./bin/darwin/amd64/github-release'
  github_release_opts=(--user "$CIRCLE_PROJECT_USERNAME" --repo "$CIRCLE_PROJECT_REPONAME" --tag "$CIRCLE_TAG")
  run [ -r "$artifact" ]
  run "$python" -m plover_build_utils.download "$github_release_url" "$github_release_sha1" "$github_release"
  run tar xvjf "$github_release"
  run "$github_release_exe" release "${github_release_opts[@]}" --draft
  run "$github_release_exe" upload "${github_release_opts[@]}" --file "$artifact" --name "${artifact##*/}"
}

[ $# -eq 1 ]

python='python3'

"$1"
