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
  if [ -d .cache ]
  then
    "$python" -m plover_build_utils.tree -L 2 .cache
  else
    echo "no .cache directory found; nothing to list"
  fi
}

run_tests()
{
  test_cmd=(env QT_QPA_PLATFORM=offscreen "$python" -m pytest --color=yes --durations=5 "$@")
  run "$python" setup.py -q egg_info
  info "$(printf "%q " "${test_cmd[@]}")"
  "${test_cmd[@]}"
}

setup_cache_name()
{
  target_python="$1"
  platform_name="$2"
  if [ "$RUNNER_OS" = 'macOS' ]
  then
    . ./osx/deps.sh
    [ "$target_python" = "$py_installer_version" ] || die 1 "versions mismatch: target=$target_python, installer=$py_installer_version"
    target_python="$py_installer_version"
  fi
  cache_name=$("$python" - "$GITHUB_JOB" "$target_python" "$platform_name" <<\EOF
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

print(f'{name}_py-{python_version}_{platform_name}')
EOF
)
  echo "cache_name=$cache_name" >> $GITHUB_OUTPUT
}

setup_osx_python()
{
  target_python="$1"
  . ./osx/deps.sh
  [ "$target_python" = "$py_installer_version" ] || die 1 "versions mismatch: target=$target_python, installer=$py_installer_version"
  python='python3'
  python_dir="$cache_dir/python"
  if [ ! -e "$python_dir" ]
  then
    # Create standalone Python installation if necessary.
    run osx_standalone_python "$python_dir" "$py_installer_version" "$py_installer_macos" "$py_installer_sha1" "$reloc_py_url" "$reloc_py_sha1"
  fi
  # Update PATH.
  run_eval "echo \"\$PWD/$python_dir/Python.framework/Versions/Current/bin\" >>\$GITHUB_PATH"
  run_eval "echo MACOSX_DEPLOYMENT_TARGET=12.0 >>\$GITHUB_ENV"
  # Fix SSL certificates so plover_build_utils.download works.
  SSL_CERT_FILE="$("$python" -m pip._vendor.certifi)" || die
  run_eval "echo SSL_CERT_FILE='$SSL_CERT_FILE' >>\$GITHUB_ENV"
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
    get_base_devel --no-warn-script-location || die
    install_wheels --no-warn-script-location "$@" || die
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
    tagged)
      tag="${GITHUB_REF#refs/tags/}"
      title="$tag"
      is_draft='yes'
      is_prerelease="$("$python" <<EOF
from packaging.version import parse
version = parse('$RELEASE_VERSION')
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
    "$notes_body" \
  | \
    pandoc --from=gfm --to=gfm \
      --template=.github/RELEASE_DRAFT_TEMPLATE.md \
      --shift-heading-level-by=1 --wrap=none \
      --variable="version:$RELEASE_VERSION" \
      --output=notes.md || die
  if [ -n "$overwrite" ]
  then
    # Is there an existing release?
    if run_eval "last_release=\"\$(gh release view "$tag")\""
    then
      # Yes, check we're not downgrading.
      head -n20 <<<"$last_release"
      run_eval "last_version=\"\$(echo -n \"\$last_release\" | sed -n '/^# \\w\\+ \\([^ ]\\+\\)\$/{s//\\1/;P;Q0};\$Q1')\""
      if python <<EOF
from packaging.version import parse
import sys
version = parse('$RELEASE_VERSION')
last_version = parse('$last_version')
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

analyze_set_release_info()
{
  info "GITHUB_REF: $GITHUB_REF"
  info "GITHUB_EVENT_NAME: $GITHUB_EVENT_NAME"
  if [[ "$GITHUB_REF" == refs/tags/* ]]
  then
    # Tagged release.
    release_type='tagged'
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
  echo "is_release=$is_release" >> $GITHUB_OUTPUT
  echo "release_type=$release_type" >> $GITHUB_OUTPUT
  echo "release_skip_job=$skip_release" >> $GITHUB_OUTPUT
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
  echo "${job_id}_skip_cache_key=${job_skip_cache_name}_$sha1" >> $GITHUB_OUTPUT
  echo '::endgroup::' 1>&2
}

analyze_set_job_skip_job()
{
  # TODO add back
  #if [[ "${job_type:-}" == "notarize" ]]; then
  #  case "$GITHUB_EVENT_NAME:$GITHUB_REF" in
  #    push:refs/heads/main|push:refs/heads/maintenance/*|push:refs/tags/v*)
  #      : ;;  # allowed; continue to normal skip logic below
  #    *)
  #      skip_job='yes'
  #      info "Skip $job_name? $skip_job (notarize allowed only on push to main, maintenance/*, or v* tag; event=$GITHUB_EVENT_NAME ref=$GITHUB_REF)"
  #      echo "${job_id}_skip_job=$skip_job" >> $GITHUB_OUTPUT
  #      return
  #      ;;
  #  esac
  #fi
  if [ "$is_release" = "no" -a -e "$job_skip_cache_path" ]
  then
    run_link="$(< "$job_skip_cache_path")" || die
    echo 2>&1 "::warning ::Skipping \`$job_name\` job, the same subtree has already successfully been run as part of: $run_link"
    skip_job='yes'
  else
    skip_job='no'
  fi
  info "Skip $job_name? $skip_job"
  echo "${job_id}_skip_job=$skip_job" >> $GITHUB_OUTPUT
}

# Install Developer ID certificate into a temporary keychain
#
# Env vars required:
#   MACOS_CODESIGN_CERT_P12_BASE64
#   MACOS_CODESIGN_CERT_PASSWORD
#   MACOS_TEMP_KEYCHAIN_NAME
#   MACOS_TEMP_KEYCHAIN_PASSWORD
#
# Side effects:
#   - Creates/unlocks ${MACOS_TEMP_KEYCHAIN_NAME}.keychain
#   - Adds it first in the user keychain search list
#   - Imports the Developer ID identity (.p12)
#   - Configures key partition list for non-interactive codesign
install_dev_id_cert_into_temp_keychain() {
  set -euo pipefail

  : "${MACOS_CODESIGN_CERT_P12_BASE64:?Missing secret MACOS_CODESIGN_CERT_P12_BASE64}"
  : "${MACOS_CODESIGN_CERT_PASSWORD:?Missing secret MACOS_CODESIGN_CERT_PASSWORD}"
  : "${MACOS_TEMP_KEYCHAIN_PASSWORD:?Missing secret MACOS_TEMP_KEYCHAIN_PASSWORD}"
  : "${MACOS_TEMP_KEYCHAIN_NAME:?MACOS_TEMP_KEYCHAIN_NAME not set}"

  KC_FILE="${MACOS_TEMP_KEYCHAIN_NAME}.keychain"
  KC_DB="${HOME}/Library/Keychains/${MACOS_TEMP_KEYCHAIN_NAME}.keychain-db"

  # Clean any stale keychain (both list entry and on-disk file)
  if security list-keychains -d user | grep -q "$KC_FILE"; then
    security -q delete-keychain "$KC_FILE" || true
  fi
  rm -f "$KC_DB" || true

  # Create & unlock keychain (6h auto-lock)
  security -q create-keychain -p "$MACOS_TEMP_KEYCHAIN_PASSWORD" "$KC_FILE"
  security -q set-keychain-settings -lut 21600 "$KC_FILE"
  security -q unlock-keychain -p "$MACOS_TEMP_KEYCHAIN_PASSWORD" "$KC_FILE"

  # Put our keychain first in the search list (keep existing ones)
  existing="$(security list-keychains -d user | tr -d ' \"')"
  security -q list-keychains -d user -s "$KC_FILE" $existing

  # Decode the .p12 file
  echo "$MACOS_CODESIGN_CERT_P12_BASE64" | base64 --decode > signing.p12

  # Import identity and always remove the .p12 file
  security import signing.p12 -k "$KC_FILE" -P "$MACOS_CODESIGN_CERT_PASSWORD" \
    -T /usr/bin/codesign -T /usr/bin/security >/dev/null; rm -f signing.p12

  # Allow codesign to use the private key non-interactively
  security set-key-partition-list -S apple-tool:,apple:,codesign: -s \
    -k "$MACOS_TEMP_KEYCHAIN_PASSWORD" "$KC_FILE" >/dev/null

  # Sanity check: can we see a codesigning identity in this keychain?
  if ! security find-identity -p codesigning -v "$KC_FILE" | grep -q "Developer ID Application"; then
    echo "No Developer ID Application identity found in ${MACOS_TEMP_KEYCHAIN_NAME}.keychain" >&2
    return 1
  fi
}

# Cleanup the temporary keychain created for codesigning
#
# Env vars required:
#   MACOS_TEMP_KEYCHAIN_NAME
# Optional env:
#   MACOS_CODESIGN_KEYCHAIN  # if set, will be used as the keychain file name
#
# Side effects:
#   - Deletes the keychain and its on-disk DB
#   - Clears MACOS_CODESIGN_KEYCHAIN from the GitHub Actions environment (if available)
cleanup_dev_id_temp_keychain() {
  set -euo pipefail

  : "${MACOS_TEMP_KEYCHAIN_NAME:?MACOS_TEMP_KEYCHAIN_NAME not set}"

  # Respect an explicit keychain override if provided; otherwise derive from the temp name
  KC_FILE="${MACOS_CODESIGN_KEYCHAIN:-${MACOS_TEMP_KEYCHAIN_NAME}.keychain}"
  KC_DB="${HOME}/Library/Keychains/${MACOS_TEMP_KEYCHAIN_NAME}.keychain-db"

  security -q delete-keychain "$KC_FILE" || true
  rm -f "$KC_DB" || true

  # Clear env for downstream steps only when running in GitHub Actions
  if [[ -n "${GITHUB_ENV:-}" && -w "${GITHUB_ENV}" ]]; then
    echo "MACOS_CODESIGN_KEYCHAIN=" >> "$GITHUB_ENV"
  fi
}

python='python3'

exec 2>&1

"$@"
