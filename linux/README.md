# Linux Development

## Environment setup

You need Python 3.6 installed with pip support.

Some of the dependencies cannot be installed with pip:

* system libraries needed to build python-hidapi and dbus-python

For the other dependencies, you can use:

`pip3 install --user -r requirements.txt`

To install the standard plugins, you can use:

`pip3 install --user -e . -r requirements_plugins.txt`

## Development helpers

* `./launch.sh`: run from source
* `./test.sh`: run tests
