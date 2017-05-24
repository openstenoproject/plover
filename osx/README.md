# Mac Development

## Environment setup

You need Python 3.5 installed with pip support.

For installing all the required dependencies, you can use:

`pip3 install --user -r requirements.txt`

## Development helpers

* `./launch.sh`: run from source
* `./test.sh`: run tests
* `./setup.py bdist_app`: build an **application bundle**
* `./setup.py bdist_dmg`: create a **disk image**

## Gotcha: Assistive Devices Permissions

To grab user inputs and use the keyboard as a steno machine, Plover requires [Assistive Devices permissions to be granted (instructions included).](https://support.apple.com/kb/ph18391?locale=en_US)

When running from source, your terminal application must be granted Assistive Devices permissions.

If you are running from an application bundle (both in development and for releases), every new build will require re-granting the permissions.
