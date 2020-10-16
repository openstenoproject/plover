# Mac Development

## Environment setup

You need Python 3.6 installed with pip support.

If you plan on building Plover for distribution, you'll need to be using Python as distributed on [python.org](https://www.python.org/downloads/). For running from source, a brew or pyenv python should suffice.

For installing all the required dependencies, you can use:

`python3 -m pip install -r requirements.txt`

To install the standard plugins, you can use:

`python3 -m pip install --user -e . -r requirements_plugins.txt`

## Development helpers

* `./launch.sh`: run from source
* `./test.sh`: run tests
* `./setup.py bdist_app`: build an **application bundle**
* `./setup.py bdist_dmg`: create a **disk image**

## Gotcha: Assistive Devices Permissions

To grab user inputs and use the keyboard as a steno machine, Plover requires [Assistive Devices permissions to be granted (instructions included).](https://support.apple.com/kb/ph18391?locale=en_US)

When running from source, your terminal application must be granted Assistive Devices permissions.

If you are running from an application bundle (both in development and for releases), every new build will require re-granting the permissions.
