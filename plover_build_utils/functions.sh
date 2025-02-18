#!/bin/bash

opt_dry_run=0
opt_timings=0

python='false'
cache_dir='.cache'
wheels_cache="$cache_dir/wheels"
downloads_cache="$cache_dir/downloads"

# Usage: parse_opts args "$@"
#
# `$args` will be set to unhandled options and non-option arguments.
#
# Consumed options:
#
# --dry-run/-n: don't execute run/run_eval commands (print them instead)
# --debug/-d: enable `set -x` for debugging script
# --: stop options processing
#
# Tip: to update $@ after the call, use:
# parse_opts args "$@" && set -- "${args[@]}"
parse_opts()
{
  args_varname="$1"
  shift
  local _args=()
  while [ $# -ne 0 ]
  do
    case "$1" in
      --dry-run|-n)
        opt_dry_run=1
        ;;
      --debug|-d)
        set -x
        ;;
      --)
        shift
        _args+=("$@")
        break
        ;;
      *)
        _args+=("$1")
        ;;
    esac
    shift
  done
  eval "$args_varname=(\"\${_args[@]}\")"
}

info()
{
  color=34
  case "$1" in
    -c*)
      color="${1#-c}"
      shift
      ;;
  esac
  if [ -t 2 -o "x$CI" = "xtrue" ]
  then
    echo "[${color}m$@[0m" 1>&2
  else
    echo "$@" 1>&2
  fi
}

err()
{
  info -c31 "$@"
}

die()
{
  code=$?
  if [ $# -ne 0 ]
  then
    code="$1"
    shift
  fi
  if [ $# -ne 0 ]
  then
    err "$@"
  fi
  exit "$code"
}

run()
{
  if [ $opt_dry_run -eq 0 -a "x$CI" = "xtrue" ]
  then
    echo -n '::group::' 1>&2
  fi
  info "$(printf "%q " "$@")"
  [ $opt_dry_run -ne 0 ] && return
  if [ $opt_timings -ne 0 ]
  then
    time "$@"
    code=$?
  else
    "$@"
    code=$?
  fi
  if [ "x$CI" = "xtrue" ]
  then
    echo "::endgroup::" 1>&2
  fi
  return $code
}

run_eval()
{
  info "$@"
  [ $opt_dry_run -ne 0 ] && return
  if [ $opt_timings -ne 0 ]
  then
    time eval "$@"
  else
    eval "$@"
  fi
}

sha1sum()
{
  kernel="$(uname -s)" || die
  if [ "$kernel" = 'Darwin' ]
  then
    shasum "$@"
  else
    command sha1sum "$@"
  fi
}

get_base_devel()
{
  run "$python" -m plover_build_utils.get_pip -c reqs/constraints.txt -r reqs/bootstrap.txt "$@"
}

install_wheels()
{
  run "$python" -m plover_build_utils.install_wheels --disable-pip-version-check "$@"
}

bootstrap_dist()
{
  wheel="$1"
  shift
  # We still need setuptools/wheel to be available (not even --use-pep517
  # works around that). While we're at it, install Plover's wheel too,
  # taking advantage of the fact that thanks to get_pip the current
  # working directory is not added to sys.path.
  get_base_devel "$wheel" --no-deps "$@" || die
  # Install the rest: Plover's dependencies, as well as standard plugins.
  install_wheels \
    -c reqs/constraints.txt \
    -r reqs/dist.txt \
    -r reqs/dist_extra_gui_qt.txt \
    -r reqs/dist_extra_log.txt \
    -r reqs/dist_plugins.txt \
    "$@" || die
  # Avoid caching Plover's wheel.
  run rm "$wheels_cache/$(basename "$wheel")"
}

osx_standalone_python()
{
  [[ $# -eq 6 ]] || return 1

  dest="$1"
  py_version="$2"
  py_macos="$3"
  py_sha1="$4"
  reloc_py_url="$5"
  reloc_py_sha1="$6"

  py_framework_dir="$dest/Python.framework"

  [[ ! -e "$py_framework_dir" ]] || return 1

  run mkdir -p "$dest"
  run "$python" -m plover_build_utils.download "https://www.python.org/ftp/python/$py_version/python-$py_version-macosx$py_macos.pkg" "$py_sha1"
  reloc_py_zip="$(run "$python" -m plover_build_utils.download "$reloc_py_url" "$reloc_py_sha1")"
  run unzip -d "$dest" "$reloc_py_zip"
  reloc_py_dir="$(echo -n "$dest"/relocatable-python-*/)"
  run "$python" "$reloc_py_dir/make_relocatable_python_framework.py" \
    --baseurl="file://$PWD/$downloads_cache/%s/../python-%s-macosx%s.pkg" \
    --python-version="$py_version" --os-version="$py_macos" \
    --destination="$dest" \
    --without-pip \
    ;
  run ln -s 'python3' "$py_framework_dir/Versions/Current/bin/python"
  run rm -rf "$reloc_py_dir"
}

packaging_checks()
{
  run rm -rf dist
  # Check PEP 517/518 support.
  run "$python" -m build --sdist --wheel .
  # Validate distributions.
  run "$python" -m twine check --strict dist/*
  # Check manifest.
  run "$python" -m check_manifest -v
}

git_tree_sha1()
{
  if [ "x$1" = "x-d" ]
  then
    debug=1
    shift
  else
    debug=1
  fi
  refspec="$1"
  shift
  # Build excludes list.
  excludes=()
  for skiplist in "$@"
  do
    IFS=$'\r\n' read -r -d '{EOF}' -a patterns <"$skiplist" || die
    excludes+=("${patterns[@]/#/:!:}")
  done
  if [ $debug -eq 1 ]
  then
    info "excludes [${#excludes[@]}]"
    echo "${excludes[@]}" 1>&2
  fi
  # Build source tree listing.
  IFS=$'\r\n' sources=($(git ls-files "${excludes[@]}")) || die
  if [ $debug -eq 1 ]
  then
    info "sources [${#sources[@]}]:"
    echo "${sources[@]}" 1>&2
  fi
  # Build git tree listing.
  tree="$(git ls-tree "$refspec" "${sources[@]}")" || die
  if [ $debug -eq 1 ]
  then
    info "tree: [$(wc -l <<<"$tree")]"
    echo "${tree}" 1>&2
  fi
  # Calculate tree SHA1.
  sha1="$(sha1sum <<<"$tree")" || die
  sha1="${sha1%% *}"
  if [ $debug -eq 1 ]
  then
    info "sha1: $sha1"
  fi
  echo "$sha1"
}

release_prepare()
{
  [ $# -eq 1 ] || die 1 'expecting one argument: the new version'
  run "$python" setup.py patch_version "$1"
  run git add plover/__init__.py
  run git add doc/conf.py
  run towncrier build --version "$1" --yes
}

release_finalize()
{
  [ $# -eq 0 ] || die 1 'expecting no argument'
  version="$("$python" setup.py --version)"
  message="Release version $version"
  tag="v$version"
  run git commit -m "$message"
  run git tag -m "$message" "$tag"
  cat <<EOF
# now all that's left is to push to GitHub,
# assuming \`origin\` is the correct remote:
git push origin HEAD "$tag"
EOF
}

parse_opts args "$@"
set -- "${args[@]}"
