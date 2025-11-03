cmake_build_windows() {
  local src="$1" bld="$2" config="${3:-RelWithDebInfo}"
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
