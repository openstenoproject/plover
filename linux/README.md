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


## Setup on Ubuntu 18.04
Check Python3 version - version 3.6 or higher required
`python3 -v`

Install pip 

`sudo apt install python3-pip`

Install other required libraries

`sudo apt install python-hidapi python-dbus libdbus-1-dev libdbus-glib-1-dev`

Clone plover repository

`git clone https://github.com/openstenoproject/plover.git`

Change to plover directory

`cd plover`

Install plover dependencies using pip

`pip3 install --user -r requirements.txt`
