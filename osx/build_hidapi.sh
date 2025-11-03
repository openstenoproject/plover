cmake_build_macos() {
  local src="$1" bld="$2" arches="$3" config="${4:-Release}"
  rm -rf "$bld"
  cmake -S "$src" -B "$bld" \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_BUILD_TYPE="$config" \
    -DCMAKE_OSX_ARCHITECTURES="$arches"
  cmake --build "$bld" --config "$config" --parallel
}
