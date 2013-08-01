To create a windows dev environment you need to install:
- python 2.7
- pywin32
- pyserial
- wxpython for python2.7
- appdirs
- pywinusb
- mock
- pyhook
- pywinauto

The starting point for plover is application\plover. You will need to add the root dir of the distribution to the PYTHONPATH environment variable. Alternatively, you can temporarily move application\plover to the root and change its name to launch.py (it may not be called plover.py) and call it from there.

To create a windows distribution get pyinstaller-2.0 and run build.bat with the first argument being the path to pyinstaller-2.0 (relative to the working directory).

You have to add a (empty) __init__.py file to the pywinusb dir in site-packages.
