#!/bin/bash

. ./plover_build_utils/functions.sh

apt_get_install()
{
  run sudo apt-get update -qqy || die
  run sudo apt-get install -qqy "$@"
}

list_cache()
{
  "$python" -m plover_build_utils.tree -L 2 .cache
}

run_tests()
{
  "$python" setup.py -q test -- --color=yes --durations=5 -ra "$@"
}

setup_cache_name()
{
  target_python="$1"
  platform_name="$2"
  if [ "$RUNNER_OS" = 'macOS' ]
  then
    . ./osx/deps.sh
    [ "$target_python" = "${py_installer_version%.*}" ] || die 1 "versions mismatch: target=$target_python, installer=$py_installer_version"
    target_python="$py_installer_version"
  fi
  "$python" - "$GITHUB_JOB" "$target_python" "$platform_name" <<\EOF
import platform
import re
import sys

name, target_python, platform_name = sys.argv[1:]

# If target_python is a fully dotted version use it as is, otherwise
# use the current interpreter (and check for versions mismatch).
if re.match(r'\d+\.\d+.\d+$', target_python) is not None:
  python_version = target_python
else:
  parts = target_python.split('.')
  python_version = platform.python_version()
  assert parts == python_version.split('.')[:len(parts)], \
    'versions mismatch: expected=%s, actual=%s' % (target_python, python_version)

cache_name = '%s_py-%s_%s' % (name, python_version, platform_name)
print('::set-output name=cache_name::' + cache_name)
EOF
}

setup_osx_python()
{
  target_python="$1"
  . ./osx/deps.sh
  [ "$target_python" = "${py_installer_version%.*}" ] || die 1 "versions mismatch: target=$target_python, installer=$py_installer_version"
  python='python3'
  python_dir="$cache_dir/python"
  if [ ! -e "$python_dir" ]
  then
    # Create standalone Python installation if necessary.
    run osx_standalone_python "$python_dir" "$py_installer_version" "$py_installer_macos" "$py_installer_sha1" "$reloc_py_url" "$reloc_py_sha1"
  fi
  # Update PATH.
  run_eval "echo \"\$PWD/$python_dir/Python.framework/Versions/Current/bin\" >>\$GITHUB_PATH"
  # Target Mavericks.
  run_eval "echo MACOSX_DEPLOYMENT_TARGET=10.9 >>\$GITHUB_ENV"
  # Fix SSL certificates so plover_build_utils.download works.
  SSL_CERT_FILE="$("$python" -m pip._vendor.certifi)" || die
  run_eval "echo SSL_CERT_FILE='$SSL_CERT_FILE' >>\$GITHUB_ENV"
}

setup_pip_options()
{
  # If the wheels cache is available, disable pip's index.
  if [ -e "$wheels_cache" ]
  then
    run_eval "echo PIP_NO_INDEX=1 >>\$GITHUB_ENV"
  else
    run mkdir -p "$wheels_cache"
  fi
  if [ "$RUNNER_OS" = 'Windows' ]
  then
    PIP_FIND_LINKS="$(cygpath -a -w "$wheels_cache")" || die
  else
    PIP_FIND_LINKS="$PWD/$wheels_cache"
  fi
  run_eval "echo PIP_FIND_LINKS='$PIP_FIND_LINKS' >>\$GITHUB_ENV"
}

setup_python_env()
{
  python_userbase="$cache_dir/python_userbase"
  if [ "$RUNNER_OS" = 'Windows' ]
  then
    PYTHONUSERBASE="$(cygpath -a -w "$python_userbase")" || die
  else
    PYTHONUSERBASE="$PWD/$python_userbase"
  fi
  run_eval "export PYTHONUSERBASE='$PYTHONUSERBASE'"
  run_eval "echo PYTHONUSERBASE='$PYTHONUSERBASE' >>\$GITHUB_ENV"
  if [ ! -e "$python_userbase" ]
  then
    get_base_devel --no-warn-script-location --user || die
    install_wheels --no-warn-script-location --user "$@" || die
    if [ "$RUNNER_OS" = 'Windows' ]
    then
      run rm -rf "$python_userbase"/Python*/Scripts
    else
      run rm -rf "$python_userbase/bin"
    fi
  fi
}

publish_github_release()
{
  run_eval "tag=${GITHUB_REF##*/tags/}"
  run_eval "is_prerelease=$("$python" <<EOF
from pkg_resources import parse_version
version = parse_version('${tag#v}')
print('1' if version.is_prerelease else '')
EOF
  )" || die
  run pandoc --from=gfm --to=gfm \
    --lua-filter=.github/RELEASE_DRAFT_FILTER.lua \
    --template=.github/RELEASE_DRAFT_TEMPLATE.md \
    --base-header-level=2 --wrap=none \
    --variable="version:$tag" \
    --output=notes.md \
    NEWS.md || die
  run gh release create \
    --draft \
    --title "$tag" \
    --notes-file notes.md \
    ${is_prerelease:+--prerelease} \
    "$tag" dist/*/*
}

publish_pypi_release()
{
  run "$python" -m twine upload dist/Source/* dist/Wheel/*
}

python='python3'

exec 2>&1

"$@"
