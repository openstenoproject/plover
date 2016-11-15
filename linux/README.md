# Linux Development

## Automatic development environment setup

On Arch Linux and Ubuntu, you should be able to have everything setup automatically by using: `./bootstrap.sh`.

Note: you can use `./bootstrap.sh -n` to get a list of the commands that would be run.

## Manual development environment setup

You need Python 3 installed with pip support.

Some of the other dependencies cannot be installed with pip:

* PyQt5
* wmctrl: for additional window management support
* system libraries used by python-hidapi (e.g. libusb)

Those need to be installed using your distribution package manager.

### Arch Linux

Most dependencies can be installed with pacman:

`sudo pacman --sync base-devel cython libusb python-appdirs python-babel python-dbus python-mock python-pip python-pyqt5 python-pyserial python-pytest python-setuptools python-setuptools-scm python-six python-wheel python-xlib wmctrl`

For the missing dependencies, follow the generic procedure.

### Ubuntu

The latest stable release should be installable by the using the following PPA: [ppa:benoit.pierre/plover](https://launchpad.net/~benoit.pierre/+archive/ubuntu/plover).

For the development version, most dependencies can be installed with APT:

`sudo apt-get install cython3 debhelper devscripts libudev-dev libusb-1.0-0-dev pyqt5-dev-tools python3-appdirs python3-babel python3-dbus python3-dev python3-hid python3-mock python3-pip python3-pkg-resources python3-pyqt5 python3-pytest python3-serial python3-setuptools python3-setuptools-pyqt python3-setuptools-scm python3-six python3-wheel python3-xlib wmctrl`

Note: some of those packages are not available from the standard repositories. you can install them by using the aforementioned PPA: [ppa:benoit.pierre/plover](https://launchpad.net/~benoit.pierre/+archive/ubuntu/plover), or you can install them manually by following the generic install procedure with pip.

For the missing dependencies, follow the generic procedure.

### Generic procedure using pip

You can create a pip compatible requirements file with:

`./setup.py write_requirements`

And then using pip, e.g. for a user install:

`pip3 install --user -r requirements.txt -c requirements_constraints.txt`

Notes:
- if your version of pip is too old, you may get parsing errors on the lines with conditional directives (like `python-xlib>=0.17; "linux" in sys_platform`). You can fix those with the following sed command: `sed -i '/; "/{/; "linux" in sys_platform$/!d;s/; .*//}' requirements.txt`.
- on Ubuntu 14.04 LTS (Trusty Tahr), the site imports are borked, and the user site-packages directory does not get priority over the standard distribution directories, so you may need to manually add it to your Python path: `export PYTHONPATH="$HOME/.local/lib/python3.4/site-packages/${PYTHONPATH:+:}${PYTHONPATH}"`.

## Running from source

To run from source, use: `./launch.sh`.

## Installing and running

### Using a wheel file with pip

A wheel file can be created with: `./setup.py bdist_wheel`. The resulting file can then be installed using pip, e.g. for a user install:

`pip3 install dist/plover-4.0.0.dev0-py2.py3-none-any.whl`

### Using `setup.py`

You can install with `sudo ./setup.py install --record install.txt`. The list of installed files will be saved to `install.txt`.

Note: this method is not recommended as it's harder to uninstall (you have to do it manually, with the help of `install.txt`) and can mess with your distribution files.
