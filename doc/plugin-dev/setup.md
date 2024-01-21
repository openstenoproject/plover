# Initial Setup

To create a Plover plugin, first
[create a Python package](https://packaging.python.org/tutorials/packaging-projects/)
with the following directory structure:

    plover-my-plugin/
     |-- setup.cfg
     '-- setup.py

`setup.py`:

```python
#!/usr/bin/env python3

from setuptools import setup

setup()
```

`setup.cfg`:
```ini
[metadata]
name = plover-my-plugin
keywords = plover plover_plugin

[options]
zip_safe = True
setup_requires =
  setuptools>=30.3.0
install_requires =
  plover>=4.0.0.dev10
packages =
  ...  # Your packages go here
py_modules =
  ...  # Your modules go here

[options.entry_points]
...  # Your plugin components go here
```

## Directory Structure

In terms of the actual plugin code, there are two main options to organize it,
a package-based approach and a module-based approach. Some plugins may choose
to use a mix of both depending on the complexity.

### Package-based Structure

To organize the plugin in a package-based structure, we put all plugin code
inside a Python package, which is just a directory with an `__init__.py` file.

    plover-my-plugin/
     |-- plover_my_plugin/
     |    '-- __init__.py
     '-- plover_my_plugin_2/
          '-- __init__.py

For each directory you create under the plugin directory, add an entry to
`packages` in the `[options]` section of the config file:

```ini
[options]
...
packages =
  plover_my_plugin
  plover_my_plugin_2
  ...  # Other packages go here
```

The advantage of using a package approach is that you can keep all of your
plugin code in the same directory for a more complex plugin, but if your plugin
is really simple and only needs one module this might be overkill, and in that
case it would be better to use the module-based structure:

### Module-based Structure

To organize the plugin in a module-based structure, your plugin code can go
directly in the plugin directory:

    plover-my-plugin/
     '-- my_plugin.py

For each file you add under the plugin directory, add an entry to `py_modules`
in the `[options]` section of the config file:

```ini
[options]
...
py_modules =
  my_plugin
  ...  # Other modules go here
```

This works best for very simple plugins since there isn't much of a need for
a file hierarchy. However, module names are global, so avoid naming files
with common names like `util` as they may conflict with other Python packages.

## Entry Points

The `[options.entry_points]` section at the bottom of `setup.cfg` is where
you will add entry points for each plugin item you want to add. Each entry point
should refer to a certain module, function or class, depending on the plugin type.

The different types of entry points are:

```{describe} plover.command
Command plugins.
```

```{describe} plover.dictionary
Dictionary format plugins.
```

```{describe} plover.extension
Extension plugins.
```

```{describe} plover.gui.qt.tool
GUI tool plugins. Plugins of this type are only available when the Qt GUI
is used.
```

````{describe} plover.machine
Machine plugins.

```{describe} plover.gui.qt.machine_option
Machine configuration GUI widgets. Machine plugins that require
configuration in addition to the default keyboard or serial
options should have this entry point.
```
````

```{describe} plover.macro
Macro plugins.
```

```{describe} plover.meta
Meta plugins.
```

```{describe} plover.system
System plugins.
```

For example, the code below creates a dictionary entry point named `custom`,
and two commands named `foo_start` and `foo_stop`:

```ini
[options.entry_points]
plover.dictionary =
  custom = plover_my_plugin.dictionary:CustomDictionary
plover.command =
  foo_start = plover_my_plugin.foo_cmd:foo_start
  foo_stop = plover_my_plugin.foo_cmd:foo_stop
```

## Installation

To install your plugin for development, use the command-line plugin installer:

    cd plover-my-plugin
    plover -s plover_plugins install -e .

Make sure to use the `-e` flag to mark this package as editable. This allows
you to make changes to the plugin code without uninstalling and reinstalling
the plugin.

```{note}
If you make any changes to `setup.cfg` during development, you will still
need to uninstall and reinstall the plugin.
```
