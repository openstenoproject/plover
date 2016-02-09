#!/bin/bash

# set -x

# Trap errors
trap 'exit $?' ERR
# Inherit trap in subshells, functions.
set -E

# Helper to avoid errors trap.
notrap()
{
  "$@" || true
}

info()
{
  echo "[34m$@[0m"
}

err()
{
  echo 1>&2 "[31m$@[0m"
}

win32dir="$(realpath "$(dirname "$0")")"
ploverdir="$(realpath "$win32dir/..")"
winedir="$win32dir/.wine"
tmpdir="$winedir/tmp"
distdir="$win32dir/.dist"
installed="$winedir/installed"
programfiles="$winedir/drive_c/Program Files"

export WINEARCH='win32' WINEPREFIX="$winedir" WINEDEBUG="-all"
unset PYTHONPATH
# Make sure GTK environment variables don't spill over to the Wine environment.
unset \
  GDK_BACKEND \
  GDK_NATIVE_WINDOWS \
  GDK_PIXBUF_MODULE_FILE \
  GDK_RENDERING \
  GTK2_RC_FILES \
  GTK3_MODULES \
  GTK_DATA_PREFIX \
  GTK_EXE_PREFIX \
  GTK_IM_MODULE \
  GTK_IM_MODULE_FILE \
  GTK_MODULES \
  GTK_PATH \
  GTK_THEME \

add_to_wine_path()
{
  winepath="$(echo -n "$1" | sed 's,[^/]$,&/,;s,/,\\\\\\\\,g')"
  cat >"$winedir/path.reg" <<EOF
REGEDIT4

[HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\Environment]
EOF
  sed -n "/^\"PATH\"=str(2):\"/{h;/[\";]${winepath}[\";]/"'!'"{s/:\"/&${winepath};/};h;p;Q0};\$Q1" "$winedir/system.reg" >>"$winedir/path.reg"
  winecmd regedit "$winedir/path.reg"
}

winecmd()
{
  # Avoid errors trap.
  if "$@"
  then
    code=$?
  else
    code=$?
  fi
  wineserver -w
  return $code
}

winetricks()
{
  info "winetricks $@"
  env WINETRICKS_OPT_SHAREDPREFIX=1 winetricks "$@"
}

install()
{
  name="$1"
  src="$2"
  crc="$3"
  file="$(basename "$src")"
  dst="$distdir/$file"

  if grep -qxF "$file" "$installed"
  then
    return 0
  fi

  if [ ! -r "$dst" ]
  then
    info "downloading $name"
    wget -O "$dst" "$src"
  fi

  if ! sha1sum --quiet --check --status - <<<"$crc $dst"
  then
    err "SHA1 does not match: calculated $(sha1sum "$dst" | cut -d' ' -f1) (instead of $crc)"
    notrap rm -vf "$dst"
    return 1
  fi

  info "installing $name"

  shift 3
  if [ 0 -eq $# ]
  then
    return 1
  fi

  cmd="$1"
  shift
  "$cmd" "$file" "$@"

  echo "$file" >>"$installed"
}

install_7zip()
{
  file="$1"
  src="$distdir/$file"

  install_msi "$file" /q
  add_to_wine_path 'C:/Program Files/7-Zip'
}

install_unzip()
{
  file="$1"
  src="$distdir/$file"

  rm -rf "$programfiles/unzip"
  mkdir "$programfiles/unzip"
  (
    cd "$programfiles/unzip"
    winecmd wine "$src"
  )
  add_to_wine_path "C:/Program Files/unzip"
}

install_exe()
{
  file="$1"
  src="$distdir/$file"
  shift
  options=("$@")

  winecmd wine "$src" "${options[@]}"
}

install_msi()
{
  file="$1"
  src="$distdir/$file"
  shift
  options=("$@")

  winecmd msiexec /i "$src" "${options[@]}"
}

install_archive()
{
  file="$1"
  dstdir="$2"
  format="$3"

  cmd=(aunpack --save-outdir="$file.dir")
  if [[ -n "$format" ]]
  then
    cmd+=(--format="$format")
  fi
  cmd+=("$distdir/$file")

  rm -rf "$programfiles/$dstdir"
  (
    cd "$tmpdir"
    cat /dev/null >"$file.dir"
    "${cmd[@]}" >/dev/null
  )
  srcdir="$tmpdir/$(cat "$tmpdir/$file.dir")"
  mv -v "$srcdir" "$programfiles/$dstdir"
  add_to_wine_path "C:/Program Files/$dstdir"
}

install_wheel()
{
  file="$1"
  src="$distdir/$file"
  shift
  options=("$@")

  winecmd wine pip install "$src" "${options[@]}"
}

install_python_source()
{
  file="$1"
  build="$2"

  case "$file" in
    *.zip)
      dir="${file%.zip}"
      ;;
    *.tar.gz)
      dir="${file%.tar.gz}"
      ;;
    *)
      return 1
      ;;
  esac

  rm -rf "$tmpdir/$dir"

  aunpack --quiet --extract-to "$tmpdir" "$distdir/$file"

  (
    cd "$tmpdir/$dir"
    if [ -z "$build" ]
    then
      winecmd wine python.exe setup.py --quiet install
    else
      "$build"
    fi
  )

  rm -rf "$tmpdir/$dir"

  return 0
}

pip_install()
{
  for package in "$@"
  do
    if grep -qxF "$package" "$installed"
    then
      continue
    fi

    info "installing ${package%%[=>]*}"

    winecmd wine pip --disable-pip-version-check install "$package"

    echo "$package" >>"$installed"
  done
}

build_distribute()
{
  cp "$winedir/drive_c/Python27/Lib/site-packages/setuptools/cli-32.exe" setuptools/
  winecmd wine python.exe setup.py --quiet install
}

build_setuptools()
{
  sed -i -e "s/\<followlinks=True\>/followlinks=False/" setuptools/__init__.py
  winecmd wine python.exe setup.py --quiet install
}

install_mimetypes()
{
  file="$1"
  src="$distdir/$file"
  dst="$winedir/drive_c/Python27/Lib/$file"

  cp -v "$src" "$dst"
  winecmd wine python.exe -m py_compile "$dst"
}

install_pygobject()
{
  file="$1"
  shift
  srcdir="$tmpdir/${file%.exe}"
  dstdir="$winedir/drive_c/Python27/Lib/site-packages"

  rm -rf "$srcdir"
  aunpack --extract-to="$srcdir" --format=7z "$distdir/$file" >/dev/null
  python2 "$win32dir/pygi-aio-installer.py" "$srcdir" "$dstdir" "$@"
  rm -rf "$srcdir"
}

install_pygtk()
{
  file="$1"
  srcdir="$tmpdir/${file%.7z}"
  dstdir="$winedir/drive_c/Python27/Lib"

  rm -rf "$srcdir"
  aunpack --extract-to="$srcdir" "$distdir/$file" >/dev/null
  cp -auv "$srcdir/py27-32"/* "$dstdir/"
  rm -rf "$srcdir"
}

install_plover()
{
  file="$1"
  version="$2"

  aunpack --extract-to="$programfiles" "$distdir/$file" >/dev/null
}

helper_setup()
{
  winecmd wineboot --init
  mkdir -p "$distdir" "$tmpdir"
  touch "$installed"
  # Bare minimum for running Plover.
  install 'Python' 'https://www.python.org/ftp/python/2.7.10/python-2.7.10.msi' 9e62f37407e6964ee0374b32869b7b4ab050d12a install_msi /q
  install 'wxPython' 'http://downloads.sourceforge.net/wxpython/wxPython3.0-win32-3.0.2.0-py27.exe' 864d44e418a0859cabff71614a495bea57738c5d install_exe
  install 'pyhook' 'http://downloads.sourceforge.net/project/pyhook/pyhook/1.5.1/pyHook-1.5.1.win32-py2.7.exe' 9afb7a5b2858a69c6b0f6d2cb1b2eb2a3f4183d2 install_exe
  install 'pywin32' 'http://downloads.sourceforge.net/project/pywin32/pywin32/Build 219/pywin32-219.win32-py2.7.exe' 8bc39008383c646bed01942584117113ddaefe6b install_exe
  install 'setuptools' 'https://pypi.python.org/packages/source/s/setuptools/setuptools-14.3.1.zip' fb16eea8e9ddb5a973e98362aabb9675c8ec63ee install_python_source build_setuptools
  pip_install \
    appdirs   \
    mock      \
    pyserial  \
    pywinauto \
    pywinusb  \
    ;
  # Install PyInstaller and dependencies.
  pip_install 'pyinstaller>=3.1'
  # Install pytest and dependencies.
  pip_install pytest
  winetricks corefonts
  true
}

helper_dist()
{(
  src="$ploverdir/build/src"

  cd "$ploverdir"
  rm -rf build dist
  mkdir build
  version="$(python2 -c 'from plover import __version__; print __version__')"

  # Make a copy of the sources, keeping only versioned entries.
  mkdir -p build dist "$src"
  git ls-files -z | xargs -0 cp -a --no-dereference --parents --target-directory="$src"

  (
  cd "$src"
  winecmd wine python.exe setup.py egg_info
  )

  # Create install data.
  info "running pyinstaller"
  (
  cd "$src"
  winecmd wine pyinstaller.exe \
    --distpath="$ploverdir/dist" \
    --workpath="$ploverdir/build" \
    --additional-hooks-dir=windows \
    --icon=windows/plover.ico \
    --name=Plover \
    --onefile \
    launch.py
  )
  mkdir dist/Plover
  mv dist/Plover.exe dist/Plover/
  mv -v dist/Plover "dist/Plover-$version"

  # Pack archive.
  info "packing archive"
  (
  cd dist
  zip -9 -r "Plover-$version.win32.all-in-one.zip" "Plover-$version"
  )
)}

helper_dist_setup()
{(
  winedir="$win32dir/.wine-dist"
  tmpdir="$winedir/tmp"
  programfiles="$winedir/drive_c/Program Files"

  export WINEARCH='win32' WINEPREFIX="$winedir"

  cd "$ploverdir"
  rm -rf "$winedir"
  winecmd wineboot --init
  mkdir -p "$distdir" "$tmpdir"
  version="$(python2 -c 'from plover import __version__; print __version__')"
  cp "$ploverdir/dist/Plover-$version.win32.all-in-one.zip" "$distdir/"
  install_archive "Plover-$version.win32.all-in-one.zip" Plover
  winetricks corefonts
)}

helper_dist_plover()
{(
  winedir="$win32dir/.wine-dist"
  export WINEARCH='win32' WINEPREFIX="$winedir"
  cd "$winedir/drive_c/Program Files/Plover"
  wine plover.exe "$@"
)}

helper_dist_shell()
{(
  winedir="$win32dir/.wine-dist"
  export WINEARCH='win32' WINEPREFIX="$winedir"
  "$SHELL" "$@"
)}

helper_dist_test()
{
  helper_dist
  helper_dist_setup
  helper_dist_plover "$@"
}

helper_plover()
{
  execmd=(python.exe "$(winepath -w "$ploverdir/launch.py")")
  exeargs=()
  for arg in "$@"
  do
    case "$arg" in
      -src)
        ;;
      -[0-9]*)
        execmd=("$(winepath -w "$programfiles/Plover$arg/Plover.exe")" )
        ;;
      *)
        exeargs+=("$arg")
        ;;
    esac
  done
  wine "${execmd[@]}" "${exeargs[@]}"
}

helper_wine()
{
  winecmd wine "$@"
}

helper_python()
{
  winecmd wine python.exe "$@"
}

helper_test()
{
  helper_python test/run.py "$@"
}

helper_shell()
{
  "$SHELL" "$@"
}

helper_help()
{
  cat <<EOF

Usage: $(basename "$0") [command] [arguments...]

General commands:

  help                    Show this help.
  setup                   Initialize Wine prefix for development.
                          Note: the prefix is created in win32/.wine,
                          and contains everything needed to develop,
                          run, and package Plover Windows version.

Commands using the Wine prefix created by 'setup':

  plover [-ver] [args...] Run Windows version of Plover.
                          -ver handling:
                            - run from source with -src or when unspecifed
                            - -x.xx to run installed release version x.xx
  wine [args...]          Run 'wine' with the specified arguments.
  python [args...]        Run 'python' with the specified arguments.
  test [args...]          Run Windows version of Plover test suite.
  shell [args...]         Run \$SHELL with the specified arguments.
  dist                    Create Windows distribution from Plover source.
  dist-setup              Create Wine prefix for testing the distribution.
                          Note: depend on the result of the 'dist' command,
                          the prefix is created in win32/.wine-dist, and
                          deleted before being recreated if already existing.
  dist-test [args...]     Equivalent to using 'dist', followed by 'dist-setup'
                          and 'dist-plover' with the specified arguments.

Commands using the Wine prefix created by 'dist-setup':

  dist-plover [args...]   Run Windows distribution version of Plover.
  dist-shell [args...]    Run \$SHELL with the specified arguments.

EOF
}

helper="$(echo -n "$1" | tr - _)"
shift
helper_"$helper" "$@"

