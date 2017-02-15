# Windows Development

## Automatic development environment setup

Everything required for Plover development can automatically be installed by executing: `bootstrap.bat`.

## Manual development environment setup

### Python

It is best to develop using 32 bit tools for Plover.

- [Python 2.7 x86_32](https://www.python.org/downloads/windows/)

### Externally hosted dependencies

- [Cython](http://cython.org/)
- [Microsoft Visual C++ Compiler for Python 2.7](https://www.microsoft.com/en-us/download/details.aspx?id=44266)
- [wxPython](http://www.wxpython.org/)

### Other dependencies

Most dependencies can be retrieved with pip:

- `python setup.py write_requirements`
- `pip install -r requirements.txt -c requirements_constraints.txt`

## Running Plover in development

To run from source, from the root of the Git repository, use `launch.bat`.

## Building

To build to an `exe`, you can `pip install pyinstaller`. Then, run `python windows\helper.py dist`; the result will be in `dist`.
