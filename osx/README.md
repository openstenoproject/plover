# Plover Development on OS X

## Dependencies

### Python

You need Python 2.7, with 32-bit support. `brew install python --universal --framework`

### XCode Tools

You need XCode commandline tools. Check by running `gcc` in the terminal. You will receive a prompt if they are not installed.

### wxPython

Get wxPython 3+. `brew install wxpython`

### cython-hidapi

Installing hidapi through pip only creates a 64-bit binary on my system, so when it is stripped to 32-bit for Plover, you cannot use the module. The workaround for this is to install `hidapi` from another source. I've forked `cython-hidapi` for this purpose. Please [build and install the fork](https://github.com/morinted/cython-hidapi).

### Pip

Pip dependencies can be grabbed with:

`pip install appdirs pyserial simplejson py2app Cython mock pyobjc-core pyobjc-framework-cocoa pyobjc-framework-quartz`

### Building

In the `/osx` folder, you can run `make app` to build `/dist/Plover.app`. To package into a `dmg` instead, use `make dmg`. There is also `make clean` in order to clear out the build and dist folders. I tend to use `make clean app` in development for testing builds.

After each build, you need to approve Plover as an Assistive Device. Do `System Preferences / Security & Privacy / Privacy / Accessiblity / + Plover.app`, and then you can launch the `.app` (`open ../dist/Plover.app`).

## Usage with VirtualEnv

If you would like to use virtualenv, you will need to follow additional instructions.

Create an environment using virtualenv (1.11.6) from virtualenv.org. Once in the virtualenv (i.e. activate the environment) you’ll want to update pip and setuptools.

### Hacking wxPython into your virtualenv

You need to hack your virtualenv to have wxPython. This is only necessary if you’re using virtualenv but it’s still highly recommended. If you want to understand what you’re about to do you can read more at the following link: http://wiki.wxpython.org/wxPythonVirtualenvOnMac

Run these commands while in the top directory of your plover virtualenv:

```
ln -s /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/wxredirect.pth lib/python2.7/site-packages
mv bin/python bin/bad_python
ln -s /Library/Frameworks/Python.framework/Versions/2.7/bin/python bin/python
echo 'PYTHONHOME=$VIRTUAL_ENV; export PYTHONHOME' >> bin/activate
```

### Fix a bug in py2app or modulegraph

There is a bug right now between py2app and modulegraph:

https://bitbucket.org/ronaldoussoren/modulegraph/issue/22/scan_code-in-modulegraphpy-contains-a

Until it’s fixed, we need to fix it ourselves. A quick fix that you can run from the root of the virtualenv:

`sed -i .bak -e 's/\.scan_code/._scan_code/' -e 's/\.load_module/._load_module/' lib/python2.7/site-packages/py2app/recipes/virtualenv.py`
