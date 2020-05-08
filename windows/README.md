# Windows Development
These instructions apply to at least commit 1788f74.

## Environment setup
Running Plover from source requires Python 3.6 (32 bits) installed
with pip support.

Once Python is installed, clone the Plover project.  This will create
a local copy within a folder named `plover/`:

```
c:\projects> git clone https://github.com/openstenoproject/plover.git

```

Within the `plover/` directory, create a virtual environment.  A
virtual environment will ensure that Plover dependencies do not
conflict with other Python installs.  This will create a Python
[`venv` virtual
environment](https://docs.python.org/3.6/library/venv.html) named
"venv":

```
c:\projects> cd plover
c:\projects\plover> python -m venv venv
```

Activate the virtual environment.  The virtual environment is
activated when `(venv)` appears at the beginning of the command line:

```
c:\projects\plover> venv\Scripts\activate
(venv) c:\projects\plover>
```

Plover has several dependencies.  These are defined in
`requirements.txt`, `requirements_plugins.txt`, and
`requirements_distribution.txt`.  The plugin and distribution
requirements are only necessary if you intend to use plugins or build
a Plover executable.  This will install the minimum number of external
requirements:

```
(venv) c:\projects\plover> pip install -r requirements.txt
```

The Plover package itself is a requirement.  This will install the
Plover package as "editable", meaning Python will use the files in
this folder and not a copy located in `venv\Lib\site-packages\`.
Changes made to the Plover source code will be effective immediately
without needing to re-install it.

```
(venv) c:\projects\plover> pip install -e .
```

Finally, to run Plover using the graphical user interface, various
`ui` files must be generated:

```
(venv) c:\projects\plover> python setup.py build_ui
```

You should now be able to run Plover using:

```
(venv) c:\projects\plover> python plover\main.py
```

## Development helpers

* `./launch.bat`: run from source
* `./test.bat`: run tests
* `./setup.py bdist_win`: create a standalone distribution
