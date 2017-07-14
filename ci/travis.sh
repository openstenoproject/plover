#!/bin/bash

set -e

. ./utils/functions.sh

is_deployment()
{
  if [ -n "$TRAVIS_TAG" ] && [ "$TRAVIS_PYTHON_VERSION" == '3.5' ]
  then
    return 0
  else
    return 1
  fi
}

setenv()
{
  # Fix path to to python-config.
  run_eval "export PATH=\"/opt/python/$TRAVIS_PYTHON_VERSION/bin:\$PATH\""
}

setup()
{
  setenv
  # Install system dependencies.
  builddeps=(
    # dbus-python:
    libdbus-1-dev
    libdbus-glib-1-dev
    # hidapi:
    libudev-dev
    libusb-1.0-0-dev
  )
  if is_deployment
  then
    builddeps+=(
      # AppImage:
      libfuse2
      # Python:
      libbz2-dev
      libgdbm-dev
      libglib2.0-dev
      liblzma-dev
      libncurses5-dev
      libreadline-dev
      libsqlite3-dev
      libssl-dev
      zlib1g-dev
      # wmctrl:
      libx11-dev
      libxmu-dev
    )
  fi
  run sudo apt-get install -qq "${builddeps[@]}"
  # Setup development environment.
  bootstrap_dev
}

build()
{
  setenv
  run git fetch --quiet --unshallow
  run "$python" setup.py patch_version
  run "$python" setup.py test

  # Only generate artifacts if we're actually going to deploy them.
  # Note: if we moved this to the `before_deploy` phase, we would
  # not have to check, but we'd also lose caching; since the cache
  # is stored before the `before_install` phase...
  if ! is_deployment
  then
    return
  fi

  # Create wheel and source distribution.
  run "$python" setup.py bdist_wheel sdist
  # Build AppImage.
  run ./linux/appimage/build.sh -c -j 2 -w dist/*.whl
  run rm -rf .cache/pip
}

[ "$TRAVIS_OS_NAME" == 'linux' ]
[ $# -eq 1 ]

python='python'

"$1"
