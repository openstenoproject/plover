#!/bin/bash

set -e

. ./plover_build_utils/functions.sh

# Note: Python 3 is not supported, use Apple's built-in Python 2.
python='/usr/bin/python2.7'
rwt 'dmgbuild==1.3.1' -- run "$python" -c \
  'import sys, dmgbuild; dmgbuild.build_dmg(*sys.argv[1:], lookForHiDPI=True)' \
  "$@"
