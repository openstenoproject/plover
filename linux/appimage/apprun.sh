#!/bin/bash

appimage_setenv()
{
  export LD_LIBRARY_PATH="${APPDIR}/usr/lib:${LD_LIBRARY_PATH+:$LD_LIBRARY_PATH}"
  export PATH="${APPDIR}/usr/bin:${PATH}"
  # Patch LDFLAGS so installing some Python packages from source can work.
  export LDFLAGS="-L${APPDIR}/usr/lib"
}

appimage_install()
{
  if [ "$EUID" -eq 0 ]
  then
    prefix=/usr/local
  else
    prefix="$HOME/.local"
  fi
  binary_main="$prefix/bin/$(basename "$APPIMAGE")"
  binary_symlink="$prefix/bin/plover"
  desktop_entry="$prefix/share/applications/plover.desktop"
  icon="$prefix/share/icons/hicolor/128x128/apps/plover.png"
  # Check if we're upgrading a previous AppImage.
  if [ -r "$desktop_entry" ] && previous_appimage="$(sed -n '/^Exec=\(.*\.AppImage\)$/{s//\1/p;Q0};$Q1' "$desktop_entry")"
  then
    "$previous_appimage" --uninstall
  fi
  existing_install=()
  for f in "$binary_main" "$binary_symlink" -r "$desktop_entry" "$icon"
  do
    [ -r "$f" ] && existing_install+=("$f")
  done
  if [ ${#existing_install[@]} -ne 0 ]
  then
    echo 1>&2 "aborting install: another version of Plover is already installed in '$prefix':"
    ls -l "${existing_install[@]}"
    return 1
  fi
  install -v -m755 -D "$APPIMAGE" "$binary_main"
  ln -v -snf "$(basename "$binary_main")" "$binary_symlink"
  install -v -m644 -D "$APPDIR/plover.desktop" "$desktop_entry"
  sed -i "s,^Exec=.*,Exec=$binary_main," "$desktop_entry"
  install -v -m644 -D "$APPDIR/plover.png" "$icon"
  update-desktop-database "$prefix/share/applications"
  gtk-update-icon-cache -f -t "$prefix/share/icons/hicolor"
}

appimage_uninstall()
{
  prefix="$(dirname "$(dirname "$APPIMAGE")")"
  binary_main="$APPIMAGE"
  binary_symlink="$prefix/bin/plover"
  desktop_entry="$prefix/share/applications/plover.desktop"
  icon="$prefix/share/icons/hicolor/128x128/apps/plover.png"
  rm -vf "$binary_main" "$binary_symlink" "$desktop_entry" "$icon"
  update-desktop-database "$prefix/share/applications"
  gtk-update-icon-cache -q -f -t "$prefix/share/icons/hicolor"
}

appimage_python()
{
  exec "${APPDIR}/usr/bin/python" "$@"
}

install_udev_rule()
{
  # Pass through variables because pkexec doesn't pass through env
  local UDEV_RULE_FILE="$1"
  local USER="$2"
  if ! grep -q "^plover:" /etc/group; then
    groupadd plover
  fi
  # NOTE: this requires a reboot!
  if ! groups "$USER" | grep -qw "plover"; then
    usermod -aG plover "$USER"
  fi
  if [ ! -f "$UDEV_RULE_FILE" ]; then
    echo 'KERNEL=="uinput", GROUP="plover", MODE="0660", OPTIONS+="static_node=uinput"' > "$UDEV_RULE_FILE"
    chmod 644 "$UDEV_RULE_FILE"
    udevadm control --reload-rules
    udevadm trigger
    # Temporarily give the current user access
    # This is done because the groupadd does not take effect until next reboot
    # And this temporary solution works *until* the next reboot
    # FIXME if someone can find a better solution
    chown "${USER}:plover" /dev/uinput
    chmod 660 /dev/uinput
  fi
}

appimage_launch()
{
  # Install the udev rule required for uinput
  UDEV_RULE_FILE="/etc/udev/rules.d/99-plover-uinput.rules"
  # It's done like this to have the lowest possible number of pkexec calls
  # Each time it's called, the user gets shown a new password input dialog
  # FIXME if there is an easier way to do it
  if [ ! -f "$UDEV_RULE_FILE" ] || ! grep -q "^plover:" /etc/group || ! groups | grep -qw "plover"; then
    notify-send -t 10000 "Installing udev rules" "You will be prompted for your password"
    pkexec bash -c "$(declare -f install_udev_rule); install_udev_rule '$UDEV_RULE_FILE' '$USER'"
    notify-send -t 10000 "Successfully installed udev rules" "A reboot may be required for output to work"
  fi
  appimage_python -s -m plover.scripts.dist_main "$@"
}

set -e

APPDIR="$(dirname "$(readlink -e "$0")")"

appimage_setenv

# Handle AppImage specific options.
[ -n "$APPIMAGE" ] && case "$1" in
  --install|--uninstall)
    [ $# -eq 1 ]
    "appimage_${1#--}"
    exit
    ;;
esac

# Handle custom launcher options.
case "$1" in
  --python)
    shift 1
    appimage_python "$@"
    ;;
  *)
    appimage_launch "$@"
    ;;
esac
