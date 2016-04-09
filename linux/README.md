# Linux Development

## Installing dependencies

Some of the dependencies cannot be installed with pip:

* python-xlib
* wxPython

Those need to be installed using your distribution package manager.

### Arch Linux

All dependencies can be installed with pacman:

`sudo pacman --sync python2-appdirs python2-hidapi python2-mock python2-pyserial python2-pytest python2-pytest-runner python2-setuptools python2-xlib wmctrl wxpython`

### Ubuntu

Most dependencies can be installed with APT:

`sudo apt-get install cython libusb-1.0-0-dev libudev-dev python-appdirs python-mock python-pip python-pytest python-serial python-setuptools python-wxgtk3.0 python-xlib wmctrl`

Note: `python-wxgtk3.0` is only available starting with Ubuntu 15.10 (Wily Werewolf). It can be installed on older versions, like Ubuntu 14.04 LTS (Trusty Tahr), by using the following PPA: `ppa:adamwolf/kicad-trusty-backports`.

For the missing dependencies, follow the generic procedure.

### Generic procedure using pip

You can create a pip compatible requirements file with:

`./setup.py write_requirements`

And then using pip, e.g. for a user install:

`pip2 install --user -r requirements.txt`

Notes:
- if your version of pip is too old, you may get parsing errors on the lines with conditional directives (like `python-xlib>=0.14; "linux" in sys_platform`). You can fix those with the following sed command: `sed -i '/; "/{/; "linux" in sys_platform$/!d;s/; .*//}' requirements.txt`.
- on Ubuntu 14.04 LTS (Trusty Tahr), the site imports are borked, and the user site-packages directory does not get priority over the standard distribution directories, so you may need to manually add it to your Python path: `export PYTHONPATH="$HOME/.local/lib/python2.7/site-packages/${PYTHONPATH:+:}${PYTHONPATH}"`.

## Running from source

To run from source, use: `./launch.sh`.

## Installing and running

### Using an egg

A self-contained executable egg can be created with: `./setup.py bdist_egg`. The egg will be created in `dist`, `chmod +x` it and you can run Plover directly from it:

`chmod +x dist/Plover-2.5.8-py2.7.egg && ./dist/Plover-2.5.8-py2.7.egg`

Note: the egg file can be moved, but it cannot however be renamed (as the package version is encoded in the name).

### Using a wheel file with pip

A wheel file can be created with: `./setup.py bdist_wheel`. The resulting file can then be installed using pip, e.g. for a user install:

`pip2 install dist/Plover-2.5.8-py2-none-any.whl`

### Using `setup.py`

You can install with `sudo ./setup.py install --record install.txt`. The list of installed files will be saved to `install.txt`.

Note: this method is not recommended as it's harder to uninstall (you have to do it manually, with the help of `install.txt`) and can mess with your distribution files.
