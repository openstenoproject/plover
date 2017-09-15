#!/bin/bash

set -e

. ./plover_build_utils/functions.sh

is_deployment()
{
  if [ -n "$TRAVIS_TAG" ]
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
      liblzma-dev
      libncurses5-dev
      libreadline-dev
      libsqlite3-dev
      libssl-dev
      zlib1g-dev
      # PyQt5:
      libasound2
      libegl1-mesa
      libfontconfig1
      libgl1-mesa-glx
      libnss3
      libxcomposite1
      libxcursor1
      libxi6
      libxrandr2
      libxss1
      libxtst6
    )
  fi
  run sudo apt-get install -qq "${builddeps[@]}"
  # Setup development environment.
  bootstrap_dev --user
}

build()
{
  setenv
  run git fetch --quiet --unshallow
  run "$python" setup.py patch_version
  # Run tests.
  run "$python" setup.py test
  # Run some packaging related sanity checks.
  run "$python" -m check_manifest
  run "$python" setup.py check -m -r -s
  # Only generate artifacts if we're actually going to deploy them.
  # Note: if we moved this to the `before_deploy` phase, we would
  # not have to check, but we'd also lose caching; since the cache
  # is stored before the `before_install` phase...
  if is_deployment
  then
    # Create wheel and source distribution.
    run "$python" setup.py bdist_wheel sdist
    # Build AppImage.
    run ./linux/appimage/build.sh -c -j 2 -w dist/*.whl
    run rm -rf .cache/pip
  else
    # Otherwise, install plugins, and check requirements.
    run "$python" setup.py bdist_wheel
    wheels_install --user --ignore-installed --no-deps dist/*.whl
    wheels_install --user -r requirements_plugins.txt
    run "$python" -m plover_build_utils.check_requirements
  fi
}

[ "$TRAVIS_OS_NAME" == 'linux' ]
[ $# -eq 1 ]

python='python'

"$1"
