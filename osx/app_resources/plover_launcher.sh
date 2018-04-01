#!/usr/bin/env bash

set -e

DIR=$(dirname "$0")
exec "$DIR/../Frameworks/pythonexecutable" -s -m plover.dist_main "$@"
