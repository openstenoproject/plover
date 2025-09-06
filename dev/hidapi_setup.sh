#!/usr/bin/env bash
set -euo pipefail

# Build a local hidapi shared library for development.
# After building, export DYLD/LD paths it prints so `import hid` finds it.
#
# Usage:
#   ./dev/macos_dev_setup.sh
#   HIDAPI_VERSION=0.15.0 ./dev/macos_dev_setup.sh
#   UNIVERSAL2=1 ./dev/macos_dev_setup.sh      # macOS: build arm64+x86_64
#
# Resulting libs:
#   macOS:  build/local-hidapi/macos/lib/libhidapi*.dylib
#   Linux:  build/local-hidapi/linux/lib/libhidapi-hidraw.so

HIDAPI_VERSION="${HIDAPI_VERSION:-0.15.0}"
UNIVERSAL2="${UNIVERSAL2:-0}"

# Resolve repo root relative to this script
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

# Shared fetch/build helpers
# shellcheck disable=SC1091
. "${REPO_ROOT}/osx/build_hidapi.sh"

WORK_DIR="${REPO_ROOT}/build/local-hidapi"
SRC_DIR="${WORK_DIR}/src"
BUILD_DIR="${WORK_DIR}/build"
OUT_LIB_DIR_MAC="${WORK_DIR}/macos/lib"
OUT_LIB_DIR_LNX="${WORK_DIR}/linux/lib"

# Fetch source
rm -rf "${SRC_DIR}" "${BUILD_DIR}"
mkdir -p "${SRC_DIR}" "${BUILD_DIR}"

TARBALL="${WORK_DIR}/hidapi-${HIDAPI_VERSION}.tar.gz"
echo "==> Downloading & unpacking hidapi ${HIDAPI_VERSION}"
fetch_hidapi "${HIDAPI_VERSION}" "${SRC_DIR}" "${TARBALL}"

OS="$(uname -s)"
ARCH="$(uname -m)"

if [[ "${OS}" == "Darwin" ]]; then
  echo "==> Configuring (macOS, IOHIDManager backend)"
  mkdir -p "${OUT_LIB_DIR_MAC}"
  # Architectures
  if [[ "${UNIVERSAL2}" == "1" ]]; then
    OSX_ARCHES="x86_64;arm64"
  else
    # build host arch only for faster local dev
    if [[ "${ARCH}" == "arm64" || "${ARCH}" == "aarch64" ]]; then
      OSX_ARCHES="arm64"
    else
      OSX_ARCHES="x86_64"
    fi
  fi

  cmake_build_macos "${SRC_DIR}" "${BUILD_DIR}" "${OSX_ARCHES}" "RelWithDebInfo"

  # Find the produced dylib (name can be libhidapi.dylib or versioned)
  DYLIB="$(/usr/bin/find "${BUILD_DIR}" -type f -name 'libhidapi*.dylib' -print -quit || true)"
  if [[ -z "${DYLIB}" ]]; then
    echo "Error: libhidapi*.dylib not found in build output." >&2
    exit 3
  fi

  BASENAME="$(basename "${DYLIB}")"
  echo "==> Staging ${BASENAME}"
  cp -f "${DYLIB}" "${OUT_LIB_DIR_MAC}/${BASENAME}"

  pushd "${OUT_LIB_DIR_MAC}" >/dev/null
  # Create friendly aliases some loaders use
  ln -sf "${BASENAME}" libhidapi.dylib
  popd >/dev/null

  echo
  echo "✅ Built macOS hidapi at: ${OUT_LIB_DIR_MAC}/${BASENAME}"
  echo
  echo "To use it for source runs (tox/venv):"
  echo "  export DYLD_FALLBACK_LIBRARY_PATH=\"${OUT_LIB_DIR_MAC}:\${DYLD_FALLBACK_LIBRARY_PATH:-}\""
  echo "  # then run: tox -e launch (or python …)"
  echo
  echo "Tox snippet:"
  cat <<EOF
[testenv]
setenv =
    DYLD_FALLBACK_LIBRARY_PATH = ${OUT_LIB_DIR_MAC}:\${DYLD_FALLBACK_LIBRARY_PATH}
EOF

elif [[ "${OS}" == "Linux" ]]; then
  echo "==> Configuring (Linux, hidraw backend)"
  mkdir -p "${OUT_LIB_DIR_LNX}"
  need cmake

  cmake -S "${SRC_DIR}" -B "${BUILD_DIR}" \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo

  echo "==> Building"
  cmake --build "${BUILD_DIR}" --config RelWithDebInfo --parallel

  SO="$(/usr/bin/find "${BUILD_DIR}" -type f -name 'libhidapi-hidraw.so*' -print -quit || true)"
  if [[ -z "${SO}" ]]; then
    echo "Error: libhidapi-hidraw.so not found in build output." >&2
    exit 3
  fi

  BASENAME="$(basename "${SO}")"
  echo "==> Staging ${BASENAME}"
  cp -f "${SO}" "${OUT_LIB_DIR_LNX}/${BASENAME}"

  pushd "${OUT_LIB_DIR_LNX}" >/dev/null
  # soname convenience
  [[ -e libhidapi-hidraw.so ]] || ln -sf "${BASENAME}" libhidapi-hidraw.so || true
  popd >/dev/null

  echo
  echo "✅ Built Linux hidapi at: ${OUT_LIB_DIR_LNX}/${BASENAME}"
  echo
  echo "To use it for source runs:"
  echo "  export LD_LIBRARY_PATH=\"${OUT_LIB_DIR_LNX}:\${LD_LIBRARY_PATH:-}\""
  echo "  # then run: tox -e launch (or python …)"
  echo
  echo "Tox snippet:"
  cat <<EOF
[testenv]
setenv =
    LD_LIBRARY_PATH = ${OUT_LIB_DIR_LNX}:\${LD_LIBRARY_PATH}
EOF

else
  echo "Unsupported OS: ${OS}. This helper currently supports macOS and Linux." >&2
  exit 4
fi