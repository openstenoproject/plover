# Plover Development on OS X

## Dependencies

### Python

You need Python 2.7. We build with brewed Python, as Apple's Python will cause you a few unexpected issues. `brew install python --framework`

### XCode Tools

You need XCode commandline tools. Check by running `gcc` in the terminal. You will receive a prompt if they are not installed.

### wxPython

Get wxPython 3+. `brew install wxpython`

### Pip

Pip dependencies can be grabbed with:

`pip install appdirs pyserial simplejson py2app Cython mock hidapi pyobjc-core pyobjc-framework-cocoa pyobjc-framework-quartz`

### Running

To run in development, you need access to Assistive Devices. We can circumvent this by running as sudo. To run Plover in development, use:

`sudo python launch.py`

### Building

In the `/osx` folder, you can run `make app` to build `/dist/Plover.app`. To package into a `dmg` instead, use `make dmg`. There is also `make clean` in order to clear out the build and dist folders.

After each build, you need to approve Plover as an Assistive Device. Do `System Preferences / Security & Privacy / Privacy / Accessiblity / + Plover.app`, and then you can launch the `.app` (`open ../dist/Plover.app`).

