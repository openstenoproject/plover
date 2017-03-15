#!/bin/sh

set -e

# No `readlink -e` on macOS...
srcdir="$(python3 - "$0" <<\EOF
import os
import sys

print(os.path.dirname(os.path.realpath(sys.argv[1])))
EOF
)"

cd "$srcdir"
exec python3 setup.py launch -- "$@"
