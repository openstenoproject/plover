#!/bin/bash

opt_dry_run=0
opt_timings=0

python='false'
wheels="$PWD/.cache/wheels"
downloads="$PWD/.cache/downloads"

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
  eval "$args_varname=(${_args[@]@Q})"
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
  if [ -t 2 ]
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

find_dist()
{
  if ! [ -r /etc/lsb-release ]
  then
    if [ -r /etc/arch-release ]
    then
      echo arch
      return
    fi
    err "unsupported distribution: $dist"
    return 1
  fi
  dist="$(lsb_release -i -s | tr A-Z a-z)"
  case "$dist" in
    arch)
      echo 'arch'
      ;;
    linuxmint|trisquel|ubuntu)
      echo 'ubuntu'
      ;;
    *)
      err "unsupported distribution: $dist"
      return 1
      ;;
  esac
}

run()
{
  info "$@"
  [ $opt_dry_run -ne 0 ] && return
  if [ $opt_timings -ne 0 ]
  then
    time "$@"
  else
    "$@"
  fi
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

# Crude version of wheels_install, that will work
# if wheel is not installed and for installing it,
# but still tries to hit/update the wheels cache.
pip_install()
{
  run mkdir -p "$wheels" || return $?
  run "$python" -m pip install -d "$wheels" -f "$wheels" "$@" || true
  run "$python" -m pip install -f "$wheels" "$@"
}

wheels_install()
{
  run "$python" -m utils.install_wheels "$@"
}

# Crude version of https://github.com/jaraco/rwt
rwt()
{(
  local rwt_args=()
  while [ $# -ne 0 ]
  do
    if [ "x$1" = 'x--' ]
    then
      shift
      break
    fi
    rwt_args+=("$1")
    shift
  done
  wheels_install -t "$PWD/.rwt" "${rwt_args[@]}"
  run export PYTHONPATH="$PWD/.rwt${PYTHONPATH:+:$PYTHONPATH}"
  "$@"
  run rm -rf .rwt
)}
