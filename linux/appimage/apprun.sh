#!/bin/sh

set -e

APPDIR="$(dirname "$(readlink -e "$0")")"
export LD_LIBRARY_PATH="${APPDIR}/usr/lib/:${APPDIR}/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH+:$LD_LIBRARY_PATH}"
export PATH="${APPDIR}/usr/bin:${PATH}"

exec "${APPDIR}/usr/bin/python3.5" -m plover.main "$@"
