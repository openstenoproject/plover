cmake_build_linux() {
  local src="$1" bld="$2" config="${3:-Release}"
  rm -rf "$bld"
  cmake -S "$src" -B "$bld" \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_BUILD_TYPE="$config"
  cmake --build "$bld" --config "$config" --parallel
}
