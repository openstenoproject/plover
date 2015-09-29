## Windows Development

### Python

It is best to develop using 32 bit tools for Plover.

- Python 2.7 x86_32

*Note: Python 2.7.9+ comes with pip*

### Pip Packages

Most dependencies can be retrieve with pip:

`pip install pyserial appdirs pywinusb mock pywinauto`

### Externally hosted dependencies

- [pywin32](http://sourceforge.net/projects/pywin32/)
- [wxpython](http://www.wxpython.org/index.php)
- [pyhook](http://sourceforge.net/projects/pyhook/)

### Running Plover in Development

To run in development, you must have the root of Plover's Git repository in the `PYTHONPATH` environment variable.

Then, from the root of the Git repository, you can run `python application\plover`.

### Building

As a prerequesite, ensure that there is a file named `__init__.py` in the pywinusb directory in site-packages. If not, create it (as an empty file)

To build to an `exe`, you can `pip install pyinstaller`. Then, run `windows\build.bat` passing the relative path to pyinstaller as the first argument.
