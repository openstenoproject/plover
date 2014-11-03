How to set up a Plover development environment on OSX:

Install the following packages. The version numbers in parens are those I last used successfully.

These can be installed from .pkg files downloaded from the specified website. If you get an error saying a pkg is corrupt then you need to allow apps to be downloaded from anywhere: http://avid.force.com/pkb/articles/en_US/Troubleshooting/Gatekeeper-blocking-installer
- python 2.7 from python.org (2.7.8)
- wxpython  from wxpython.org (3.0.1.1 osx-cocoa (classic))

Create an environment using virtualenv (1.11.6) from virtualenv.org. Once in the virtualenv (i.e. activate the environment) you’ll want to update pip (1.5.6) and setuptools (7.0).

Various modules below require the Xcode command line tools, which you may not have installed. Enter the command ‘gcc’ in the terminal to see if you have it installed. It may prompt you to install them right there. Otherwise try searching for “how to install Xcode command line tools”. This will also install git, which you’ll need.

The following packages can be installed with pip:
- appdirs (1.4.0)
- pyserial (2.7)
- simplejson (3.6.5)
- py2app (0.9)
- Cython (0.21.1)
- mock (1.0.1)
- pyobjc-core (3.0.3) 
- pyobjc-framework-Cocoa (3.0.3)
- pyobjc-framework-Quartz (3.0.3)
- wxversion 

Hacking wxPython into your virtualenv:
You need to hack your virtualenv to have wxPython. This is only necessary if you’re using virtualenv but it’s still highly recommended. If you want to understand what you’re about to do you can read more at the following link: http://wiki.wxpython.org/wxPythonVirtualenvOnMac

Run these commands while in the top directory of your plover virtualenv:
ln -s /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/wxredirect.pth lib/python2.7/site-packages
mv bin/python bin/bad_python
ln -s /Library/Frameworks/Python.framework/Versions/2.7/bin/python bin/python
echo 'PYTHONHOME=$VIRTUAL_ENV; export PYTHONHOME' >> bin/activate

Install cython-hidapi:
git clone --recursive https://github.com/qdot/cython-hidapi
cd cython-hidapi
python setup-mac.py install

Fix a bug in py2app or modulegraph:
There is a bug right now between py2app and modulegraph: https://bitbucket.org/ronaldoussoren/modulegraph/issue/22/scan_code-in-modulegraphpy-contains-a
Until it’s fixed, we need to fix it ourselves. A quick fix that you can run from the root of the virtualenv:
sed -i .bak -e 's/\.scan_code/._scan_code/' -e 's/\.load_module/._load_module/' lib/python2.7/site-packages/py2app/recipes/virtualenv.py

Now that your environment is ready you’ll want Plover itself:
git clone https://github.com/openstenoproject/plover

To build the app cd into plover/osx and type ‘make’. If you just want the app and not the while .dmg then: make dist/Plover.app

In order to run the app you must give it permission. You may need to do this for every new build:
Open system preferences, open “Security and Privacy”, click on the “Privacy” tab, make sure the lock on the bottom left is unlocked, drag the new version of Plover into the list on the left. If there is already a Plover listed then it may not look like anything has happened, but it has.

It’s probably possible to automate a large part of all of the above with a pip requirements file and/or this: 
https://virtualenv.pypa.io/en/latest/virtualenv.html#creating-your-own-bootstrap-scripts
