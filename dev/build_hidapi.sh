#!/usr/bin/env bash
set -euo pipefail

# Build hidapi library locally for development.
#
# Usage:
#   ./dev/macos_dev_setup.sh
#   MACOS_UNIVERSAL2=0 ./dev/build_hidapi.sh      # macOS: don't build universal2
#
# Resulting libs:
#   macOS:   build/local-hidapi/macos/lib/libhidapi*.dylib
#   Linux:   build/local-hidapi/linux/lib/libhidapi-hidraw.so
#   Windows: build/local-hidapi/windows/bin/hidapi.dll

. ./plover_build_utils/deps.sh
. ./plover_build_utils/functions.sh

python='python3'

MACOS_UNIVERSAL2="${MACOS_UNIVERSAL2:-1}"

# Resolve repo root relative to this script
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

WORK_DIR="${REPO_ROOT}/build/local-hidapi"
SRC_DIR="${WORK_DIR}/src"
BUILD_DIR="${WORK_DIR}/build"
OUT_LIB_DIR_MAC="${WORK_DIR}/macos/lib"
OUT_LIB_DIR_LNX="${WORK_DIR}/linux/lib"
OUT_BIN_DIR_WIN="${WORK_DIR}/windows/bin"

# Clean and prep
# Prepare directories 
mkdir -p "${SRC_DIR}" "${BUILD_DIR}"

OS="$(uname -s || true)"
# If outputs already exist for the current platform, skip rebuilding.
if [[ "${OS}" == "Darwin" ]]; then
  if ls "${OUT_LIB_DIR_MAC}"/libhidapi*.dylib >/dev/null 2>&1; then
    echo "hidapi found at ${OUT_LIB_DIR_MAC}; skipping build."
    exit 0
  fi
elif [[ "${OS}" == "Linux" ]]; then
  if ls "${OUT_LIB_DIR_LNX}"/libhidapi-hidraw.so* >/dev/null 2>&1; then
    echo "hidapi found at ${OUT_LIB_DIR_LNX}; skipping build."
    exit 0
  fi
elif [[ "${OS}" == MINGW* || "${OS}" == MSYS* || "${OS}" == CYGWIN* || "${OS}" == "Windows_NT" ]]; then
  if [ -f "${OUT_BIN_DIR_WIN}/hidapi.dll" ]; then
    echo "hidapi found at ${OUT_BIN_DIR_WIN}/hidapi.dll; skipping build."
    exit 0
  fi
fi

# Clean and prep for a fresh build
rm -rf "${SRC_DIR}" "${BUILD_DIR}"
mkdir -p "${SRC_DIR}" "${BUILD_DIR}"

echo "==> Downloading & unpacking hidapi ${hidapi_version}"
fetch_hidapi "${SRC_DIR}" "${WORK_DIR}"


if [[ "${OS}" == "Darwin" ]]; then
  echo "==> Configuring (macOS, IOHIDManager backend)"

  # Shared fetch/build helpers (macOS)
  # shellcheck disable=SC1091
  . "${REPO_ROOT}/osx/build_hidapi.sh"

  mkdir -p "${OUT_LIB_DIR_MAC}"
  # Architectures
  if [[ "${MACOS_UNIVERSAL2}" == "1" ]]; then
    OSX_ARCHES="x86_64;arm64"
  else
    ARCH="$(uname -m || true)"
    if [[ "${ARCH}" == "arm64" || "${ARCH}" == "aarch64" ]]; then
      OSX_ARCHES="arm64"
    else
      OSX_ARCHES="x86_64"
    fi
  fi

  cmake_build_macos "${SRC_DIR}" "${BUILD_DIR}" "${OSX_ARCHES}" "RelWithDebInfo"

  # Find produced dylib
  DYLIB="$(/usr/bin/find "${BUILD_DIR}" -type f -name 'libhidapi*.dylib' -print -quit || true)"
  if [[ -z "${DYLIB}" ]]; then
    echo "Error: libhidapi*.dylib not found in build output." >&2
    exit 3
  fi

  BASENAME="$(basename "${DYLIB}")"
  echo "==> Staging ${BASENAME}"
  cp -f "${DYLIB}" "${OUT_LIB_DIR_MAC}/${BASENAME}"

  pushd "${OUT_LIB_DIR_MAC}" >/dev/null
  ln -sf "${BASENAME}" libhidapi.dylib || true
  popd >/dev/null

  echo
  echo "✅ Built macOS hidapi at: ${OUT_LIB_DIR_MAC}/${BASENAME}"

elif [[ "${OS}" == "Linux" ]]; then
  echo "==> Configuring (Linux, hidraw backend)"
  mkdir -p "${OUT_LIB_DIR_LNX}"

  # Shared fetch/build helpers (Linux)
  # shellcheck disable=SC1091
  . "${REPO_ROOT}/linux/build_hidapi.sh"

  cmake_build_linux "${SRC_DIR}" "${BUILD_DIR}" "RelWithDebInfo"

  SO="$(/usr/bin/find "${BUILD_DIR}" -type f -name 'libhidapi-hidraw.so*' -print -quit || true)"
  if [[ -z "${SO}" ]]; then
    echo "Error: libhidapi-hidraw.so not found in build output." >&2
    exit 3
  fi

  BASENAME="$(basename "${SO}")"
  echo "==> Staging ${BASENAME}"
  cp -f "${SO}" "${OUT_LIB_DIR_LNX}/${BASENAME}"

  pushd "${OUT_LIB_DIR_LNX}" >/dev/null
  [[ -e libhidapi-hidraw.so ]] || ln -sf "${BASENAME}" libhidapi-hidraw.so || true
  popd >/dev/null

  echo
  echo "✅ Built Linux hidapi at: ${OUT_LIB_DIR_LNX}/${BASENAME}"

elif [[ "${OS}" == MINGW* || "${OS}" == MSYS* || "${OS}" == CYGWIN* || "${OS}" == "Windows_NT" ]]; then
  echo "==> Configuring (Windows, WinAPI backend)"
  mkdir -p "${OUT_BIN_DIR_WIN}"

  # Shared fetch/build helpers (Windows)
  # shellcheck disable=SC1091
  . "${REPO_ROOT}/windows/build_hidapi.sh"

  # Build shared DLL
  cmake_build_windows "${SRC_DIR}" "${BUILD_DIR}" "Release"

  # Find the produced DLL (varies by generator)
  DLL="$(/usr/bin/find "${BUILD_DIR}" -type f \( -iname 'hidapi*.dll' -o -iname 'libhidapi*.dll' \) -print -quit 2>/dev/null || true)"
  if [[ -z "${DLL}" ]]; then
    echo "Error: hidapi DLL not found in build output." >&2
    exit 3
  fi

  BASENAME="$(basename "${DLL}")"
  echo "==> Staging ${BASENAME}"
  cp -f "${DLL}" "${OUT_BIN_DIR_WIN}/hidapi.dll"

  echo
  echo "✅ Built Windows hidapi at: ${OUT_BIN_DIR_WIN}/hidapi.dll"
else
  echo "Unsupported OS: ${OS}. This helper currently supports macOS, Linux, and Windows." >&2
  exit 4
fi
