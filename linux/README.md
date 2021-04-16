# Linux Development

## Environment setup

To be able to setup a complete development environment, you'll need to manually
install some system libraries (including the development version of your
distribution corresponding packages):
- [`hidapi` package](https://pypi.org/project/hidapi/) (Treal support) needs
  `libusb` (1.0) and `libudev`.
- [`dbus-python` package](https://pypi.org/project/dbus-python/) (log /
  notifications support) needs `libdbus`.

For the rest of the steps, follow the [developer guide](../doc/developer_guide.md).
