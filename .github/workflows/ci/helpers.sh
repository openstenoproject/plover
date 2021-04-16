#!/bin/bash

. ./plover_build_utils/functions.sh

apt_get_install()
{
  run sudo apt-get update -qqy || die
  run sudo apt-get install -qqy "$@"
}

generate_translations_catalogs_archive()
{
  # Make sure the main catalog is up-to-date first.
  run "$python" setup.py extract_messages
  archive="$PWD/dist/$("$python" setup.py --name)-$("$python" setup.py --version)-messages.zip"
  run mkdir -p "${archive%/*}"
  run_eval "(cd plover && zip -9 '$archive' messages/{*.pot,*/*/*.po})"
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
  # Target High Sierra.
  run_eval "echo MACOSX_DEPLOYMENT_TARGET=10.13 >>\$GITHUB_ENV"
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
  case "$RELEASE_TYPE" in
    continuous)
      tag='continuous'
      title='Continuous build'
      is_draft=''
      is_prerelease='yes'
      overwrite='yes'
      notes_body='news_draft.md'
      run_eval "'$python' -m towncrier --draft >$notes_body" || die
      ;;
    tagged)
      tag="${GITHUB_REF#refs/tags/}"
      title="$tag"
      is_draft='yes'
      is_prerelease="$("$python" <<EOF
from pkg_resources import parse_version
version = parse_version('$RELEASE_VERSION')
print('1' if version.is_prerelease else '')
EOF
)" || die
      overwrite=''
      notes_body='NEWS.md'
      ;;
    *)
      die 1 "unsupported release type: $RELEASE_TYPE"
      ;;
  esac
  assets=()
  for a in dist/*/*
  do
    case "$a" in
      # plover-4.0.0.dev8+380.gdf570a7-macosx_10_13_x86_64.dmg
      # plover-4.0.0.dev8+380.gdf570a7-messages.zip
      # plover-4.0.0.dev8+380.gdf570a7-py3-none-any.whl
      # plover-4.0.0.dev8+380.gdf570a7-win64.setup.exe
      # plover-4.0.0.dev8+380.gdf570a7-win64.zip
      # plover-4.0.0.dev8+380.gdf570a7-x86_64.AppImage
      # plover-4.0.0.dev8+380.gdf570a7.tar.gz
      *-messages.zip) name='Translations Catalogs' ;;
      *.AppImage)     name='Linux: AppImage' ;;
      *.dmg)          name='macOS: Disk Image' ;;
      *.exe)          name='Windows: Installer' ;;
      *.zip)          name='Windows: Portable ZIP' ;;
      *.tar.gz)       name='Python: Source Distribution' ;;
      *.whl)          name='Python: Wheel' ;;
      *) name='' ;;
    esac
    assets+=("$a${name:+# }$name")
  done
  run pandoc --from=gfm --to=gfm \
    --lua-filter=.github/RELEASE_DRAFT_FILTER.lua \
    --template=.github/RELEASE_DRAFT_TEMPLATE.md \
    --base-header-level=2 --wrap=none \
    --variable="version:$RELEASE_VERSION" \
    --output=notes.md \
    "$notes_body" || die
  if [ -n "$overwrite" ]
  then
    # Is there an existing release?
    if run_eval "last_release=\"\$(gh release view "$tag")\""
    then
      # Yes, check we're not downgrading.
      head -n20 <<<"$last_release"
      run_eval "last_version=\"\$(echo -n \"\$last_release\" | sed -n '/^# \\w\\+ \\([^ ]\\+\\)\$/{s//\\1/;P;Q0};\$Q1')\""
      if python <<EOF
from pkg_resources import parse_version
import sys
version = parse_version('$RELEASE_VERSION')
last_version = parse_version('$last_version')
sys.exit(0 if version < last_version else 1)
EOF
      then
        die 1 "cowardly refusing to downgrade \`$tag\` from \`$last_version\` to \`$RELEASE_VERSION\`"
      fi
      # Delete it.
      run gh release delete "$tag" -y
    fi
    # Create / force update tag manually.
    run git tag --force "$tag"
    run git push -f "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY" "$tag"
  fi
  run gh release create \
    ${is_prerelease:+--prerelease} \
    ${is_draft:+--draft} \
    --target "$GITHUB_SHA" \
    --title "$title" \
    --notes-file notes.md \
    "$tag" "${assets[@]}"
}

publish_pypi_release()
{
  run "$python" -m twine upload dist/Source/* dist/Wheel/*
}

analyze_set_release_info()
{
  if [[ "$GITHUB_REF" == refs/tags/* ]]
  then
    # Tagged release.
    release_type='tagged'
  elif [[ "$GITHUB_REF" == refs/heads/$CONTINUOUS_RELEASE_BRANCH ]]
  then
    # Continuous release.
    release_type='continuous'
  else
    # Not a release.
    release_type=''
  fi
  # Are we releasing something?
  if [[ "$GITHUB_EVENT_NAME" == 'push' ]] && [[ -n "$release_type" ]]
  then
    is_release='yes'
    skip_release='no'
  else
    is_release='no'
    skip_release='yes'
  fi
  info "Skip Release? $skip_release ($release_type)"
  echo "::set-output name=is_release::$is_release"
  echo "::set-output name=release_type::$release_type"
  echo "::set-output name=release_skip_job::$skip_release"
}

analyze_set_job_skip_cache_key()
{
  echo -n '::group::' 1>&2; info "$job_name"
  skiplists=()
  for list in default "${job_skiplists[@]}"
  do
    skiplists+=(".github/workflows/ci/skiplist_$list.txt")
  done
  sha1="$(git_tree_sha1 -d '@' "${skiplists[@]}")" || die
  echo "::set-output name=${job_id}_skip_cache_key::${job_skip_cache_name}_$sha1"
  echo '::endgroup::' 1>&2
}

analyze_set_job_skip_job()
{
  if [ "$is_release" = "no" -a -e "$job_skip_cache_path" ]
  then
    run_link="$(< "$job_skip_cache_path")" || die
    echo 2>&1 "::warning ::Skipping \`$job_name\` job, the same subtree has already successfully been run as part of: $run_link"
    skip_job='yes'
  else
    skip_job='no'
  fi
  info "Skip $job_name? $skip_job"
  echo "::set-output name=${job_id}_skip_job::$skip_job"
}

python='python3'

exec 2>&1

"$@"
