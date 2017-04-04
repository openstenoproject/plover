#!/bin/bash

. ./utils/functions.sh

# Mac OS X. {{{

osx_bootstrap()
{
  url='https://www.python.org/ftp/python/3.5.3/python-3.5.3-macosx10.6.pkg'
  md5='6f9ee2ad1fceb1a7c66c9ec565e57102'
  dst='.cache/downloads/python35.pkg'
  run mkdir -p "$(dirname "$dst")"
  for retry in $(seq 3)
  do
    if ! [ -r "$dst" ] && ! run curl --show-error --silent -o "$dst" "$url"
    then
      err "python download failed"
      rm -f "$dst"
      continue
    fi
    if [ $opt_dry_run -ne 0 ] || [ "$(md5 -q "$dst")" = "$md5" ]
    then
      break
    fi
    err "python md5 did not match"
    rm -f "$dst"
  done
  [ $opt_dry_run -ne 0 -o -r "$dst" ]
  run sudo installer -pkg "$dst" -target /
  pip_install --user wheel
}

osx_packages_install()
{
  wheels_install --user "$@"
}

osx_python3_packages=(
certifi
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
python-hidapi
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

help()
{
  echo "Usage: $0 [python2|python3]"
  exit 1
}

set -e

parse_opts args "$@" && [ "${#args[@]}" -le 1 ] || help
python="${args[0]:-python3}"
case "$python" in
  python2|python3) ;;
  *) help;;
esac

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
pip_install --user --upgrade pip
# Upgrade setuptools, we need at least 19.6 to prevent issues with Cython patched 'build_ext' command.
wheels_install --user --upgrade 'setuptools>=19.6'
# Manually install Cython if not already to speedup hidapi build.
wheels_install --user Cython
# Generate requirements.
run "$python" setup.py write_requirements
wheels_install --user -c requirements_constraints.txt -r requirements.txt

user_bin="$("$python" - <<\EOF
import os
import site

user_bin = os.path.join(site.USER_BASE, "bin")
home = os.path.expanduser("~/")
if user_bin.startswith(home):
  user_bin = os.path.join("~", user_bin[len(home):])
print(user_bin)
EOF
)"
info -c32 "Note: please make sure $user_bin is in your \$PATH!"

# vim: foldmethod=marker
