# Windows helper (MSVC only, pinned to VS 2022) — builds a shared DLL.

need() { command -v "$1" >/dev/null 2>&1 || { echo "Error: '$1' not found" >&2; exit 2; }; }

fetch_hidapi() {
  local version="$1" src_dir="$2" tarball="$3"
  local url="https://github.com/libusb/hidapi/archive/refs/tags/hidapi-${version}.tar.gz"
  need curl; need tar
  rm -rf "$src_dir"
  mkdir -p "$src_dir"
  curl -fsSL "$url" -o "$tarball"
  tar -xzf "$tarball" -C "$src_dir" --strip-components=1
}

cmake_build_windows() {
  local src="$1" bld="$2" config="${3:-RelWithDebInfo}"
  need cmake
  rm -rf "$bld"

  # Architecture override: WIN_ARCH=Win32|x64|ARM64 (default x64)
  local arch="${WIN_ARCH:-x64}"

  local -a cmake_args=(
    -A "$arch"
    -DBUILD_SHARED_LIBS=ON
    -DHIDAPI_BUILD_HIDTEST=OFF
    -DHIDAPI_BUILD_TESTS=OFF
    -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL
  )

  echo "==> running cmake (arch: $arch, config: $config)"
  cmake -S "$src" -B "$bld" "${cmake_args[@]}"
  cmake --build "$bld" --config "$config" --parallel
}
