#!/bin/sh

cd "$(dirname "$(readlink -e "$0")")" &&
exec ./setup.py test -- "$@"
