#!/bin/bash

opt_dry_run=0

python='false'

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

wheels_install()
{
  run "$python" -m utils.install_wheels --disable-pip-version-check --timeout=5 --retries=2 "$@"
}

# Mac OS X. {{{

osx_bootstrap()
{
  run brew update
  run export HOMEBREW_NO_AUTO_UPDATE=1
  run git -C "$(brew --repo)/Library/Taps/homebrew/homebrew-core" checkout '5596439c4ca5a9963a7fec0146d3ce2b27e07a17^' Formula/python3.rb
  osx_packages_install $python
  run brew link --overwrite $python
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

osx_python3_packages=(
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

arch_python2_packages=(
base-devel
cython2
libusb
python2-appdirs
python2-babel
python2-dbus
python2-hidapi
python2-mock
python2-pip
python2-pyqt5
python2-pyserial
python2-pytest
python2-setuptools
python2-setuptools-scm
python2-six
python2-wheel
python2-xlib
wmctrl
)

arch_python3_packages=(
cython
libusb
python-appdirs
python-babel
python-dbus
python-mock
python-pip
python-pyqt5
python-pyserial
python-pytest
python-setuptools
python-setuptools-scm
python-six
python-wheel
python-xlib
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
  run sudo apt-get install -qq "$@"
}

ubuntu_python2_packages=(
cython
libudev-dev
libusb-1.0-0-dev
pyqt5-dev-tools
python-appdirs
python-babel
python-dbus
python-dev
python-hid
python-mock
python-pip
python-pkg-resources
python-pyqt5
python-pytest
python-serial
python-setuptools
python-setuptools-pyqt
python-setuptools-scm
python-six
python-wheel
python-xlib
wmctrl
)

ubuntu_python3_packages=(
cython3
debhelper
devscripts
libudev-dev
libusb-1.0-0-dev
pyqt5-dev-tools
python3-appdirs
python3-babel
python3-dbus
python3-dev
python3-hid
python3-mock
python3-pip
python3-pkg-resources
python3-pyqt5
python3-pytest
python3-serial
python3-setuptools
python3-setuptools-pyqt
python3-setuptools-scm
python3-six
python3-wheel
python3-xlib
wmctrl
)

# }}}

set -e

while [ $# -ne 0 ]
do
  case "$1" in
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

python="${1:-python3}"

case "$OSTYPE" in
  linux-gnu)
    dist="$(find_dist)"
    ;;
  darwin*)
    dist='osx'
    ;;
  *)
    err "unsupported OS type: $OSTYPE"
    exit 1
    ;;
esac

if [ "$python" == 'python2' -a "$OSTYPE" != 'linux-gnu' ]
then
  err "Python 2 is only supported on Linux"
  exit 1
fi

var="${dist}_${python}_packages[@]"
packages=("${!var}")

"${dist}_bootstrap"
if [ -n "$packages" ]
then
  "${dist}_packages_install" "${packages[@]}"
fi

# Update antiquated version of pip on Ubuntu...
run "$python" -m pip install --upgrade --user pip
# Upgrade setuptools, we need at least 19.6 to prevent issues with Cython patched 'build_ext' command.
wheels_install --upgrade --user 'setuptools>=19.6'
# Manually install Cython if not already to speedup hidapi build.
wheels_install --user Cython
# Generate requirements.
run "$python" setup.py write_requirements
wheels_install --user -c requirements_constraints.txt -r requirements.txt

# vim: foldmethod=marker
