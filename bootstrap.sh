#!/bin/bash

opt_tests_only=0
opt_dry_run=0

python='false'
wheels=''

info()
{
  if [ -t 1 ]
  then
    echo "[34m$@[0m"
  else
    echo "$@"
  fi
}

err()
{
  if [ -t 2 ]
  then
    echo "[31m$@[0m" 1>&2
  else
    echo "$@" 1>&2
  fi
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
    err "unsuported distribution: $dist"
    return 1
  fi
  dist="$(lsb_release -i -s | tr A-Z a-z)"
  case "$dist" in
    arch)
      echo 'arch'
      ;;
    linuxmint|ubuntu)
      echo 'ubuntu'
      ;;
    *)
      err "unsuported distribution: $dist"
      return 1
      ;;
  esac
}

run()
{
  info "$@"
  if [ $opt_dry_run -eq 0 ]
  then
    "$@"
  fi
}

pip()
{
  run "$python" -m pip --disable-pip-version-check --timeout=5 --retries=2 "$@"
}

pip_cache_requirements()
{
  run pip wheel -r requirements.txt -w "$wheels" --find-links "$wheels" "$@"
}

pip_install_requirements()
{
  run pip install --user --upgrade --no-index -r requirements.txt --find-links "$wheels" "$@"
}

# Mac OS X. {{{

osx_bootstrap()
{
  if [ "$python" == 'python2' ]
  then
    python_package='python'
  else
    python_package="$python"
  fi
  run brew update
  osx_packages_install $python_package
  run brew link --overwrite $python_package
}

osx_packages_install()
{
  for package in "$@"
  do
    run brew install $package ||
    run brew outdated $package ||
    run brew upgrade $package
  done
}

osx_python2_base_packages=(
)
osx_python2_extra_packages=(
wxpython
)

osx_python3_base_packages=(
)
osx_python3_extra_packages=(
)

# }}}

# Arch Linux. {{{

arch_bootstrap()
{
  run sudo pacman --sync --refresh
}

arch_packages_install()
{
  run sudo pacman --sync --needed "$@"
}

arch_python2_base_packages=(
cython2
libusb
python2-appdirs
python2-dbus
python2-hidapi
python2-mock
python2-pip
python2-pyserial
python2-pytest
python2-setuptools
python2-setuptools-scm
python2-six
python2-wheel
python2-xlib
)
arch_python2_extra_packages=(
base-devel
wmctrl
wxpython
)

arch_python3_base_packages=(
cython
libusb
python-appdirs
python-dbus
python-mock
python-pip
python-pyserial
python-pytest
python-setuptools
python-setuptools-scm
python-six
python-wheel
python-xlib
)
arch_python3_extra_packages=(
wmctrl
)

# }}}

# Ubuntu. {{{

ubuntu_bootstrap()
{
  run sudo apt-add-repository -y ppa:benoit.pierre/plover
  run sudo apt-get update -qq
}

ubuntu_packages_install()
{
  run sudo apt-get install -y "$@"
}

ubuntu_python2_base_packages=(
cython
libudev-dev
libusb-1.0-0-dev
python-appdirs
python-dbus
python-dev
python-hid
python-mock
python-pip
python-pkg-resources
python-pytest
python-serial
python-setuptools
python-setuptools-scm
python-six
python-wheel
python-xlib
)
ubuntu_python2_extra_packages=(
debhelper
devscripts
python-wxgtk3.0
wmctrl
)

ubuntu_python3_base_packages=(
cython3
libudev-dev
libusb-1.0-0-dev
python3-appdirs
python3-dbus
python3-dev
python3-hid
python3-mock
python3-pip
python3-pkg-resources
python3-pytest
python3-serial
python3-setuptools
python3-setuptools-scm
python3-six
python3-wheel
python3-xlib
)
ubuntu_python3_extra_packages=(
wmctrl
)

# }}}

set -e

while [ $# -ne 0 ]
do
  case "$1" in
    --tests-only|-t)
      opt_tests_only=1
      ;;
    --dry-run|-n)
      opt_dry_run=1
      ;;
    --debug|-d)
      set -x
      ;;
    --help|-h)
      exit 0
      ;;
    -*)
      err "invalid option: $1"
      exit 1
      ;;
    *)
      break
      ;;
  esac
  shift
done

python="${1:-python2}"

case "$OSTYPE" in
  linux-gnu)
    dist="$(find_dist)"
    wheels="${XDG_CACHE_HOME:-$HOME/.cache}/wheels"
    ;;
  darwin*)
    dist='osx'
    wheels="$HOME/Library/Caches/wheels"
    ;;
  *)
    err "unsupported OS type: $OSTYPE"
    exit 1
    ;;
esac

var="${dist}_${python}_base_packages[@]"
packages=("${!var}")
if [ $opt_tests_only -eq 0 ]
then
  var="${dist}_${python}_extra_packages[@]"
  packages+=("${!var}")
fi

"${dist}_bootstrap"
if [ -n "$packages" ]
then
  "${dist}_packages_install" "${packages[@]}"
fi

# Update antiquated version of pip on Ubuntu...
run "$python" -m pip install --upgrade --user pip
# Upgrade setuptools, we need at least 19.6 to prevent issues with Cython patched 'build_ext' command.
pip install --upgrade --user 'setuptools>=19.6'
# Manually install Cython if not already to speedup hidapi build.
pip install --user Cython
# Generate requirements.
run "$python" setup.py write_requirements
# Since pip will not build and cache wheels for VCS links, we do it ourselves:
# - first, update the cache (without VCS links), and try to install from it
if ! { pip_cache_requirements && pip_install_requirements; }
then
  # - if it failed, try to update the cache again, this time with VCS links
  pip_cache_requirements -c requirements_constraints.txt
  # - and try again
  pip_install_requirements
fi

# vim: foldmethod=marker
