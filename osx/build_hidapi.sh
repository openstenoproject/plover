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

cmake_build_macos() {
  local src="$1" bld="$2" arches="$3" config="${4:-Release}"
  need cmake
  rm -rf "$bld"
  cmake -S "$src" -B "$bld" \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_BUILD_TYPE="$config" \
    -DCMAKE_OSX_ARCHITECTURES="$arches"
  cmake --build "$bld" --config "$config" --parallel
}
