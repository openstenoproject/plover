# Plugin Development Guide

Plover plugins are generally implemented as separate Python packages installed
into the Python environment that Plover uses. In most cases, this environment
will be within Plover's installation directory; if you installed from source,
it will be the system Python distribution.

Plover uses a dynamic plugin discovery system via `setuptools`'s
[`entry_points`](https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins)
configuration to allow other packages to define themselves as
certain types of plugins for Plover. After collecting the registry of plugins
in the active Python environment on initialization, Plover has hooks in its
code to call into each of the different types in the registry at various parts
of its life cycle.

Most types of plugins will interact with Plover's steno engine using these
hooks. See the documentation on {class}`StenoEngine<plover.engine.StenoEngine>`
for more information on hooks and how to integrate them into your plugin code.

Much of Plover's built-in functionality is implemented within this plugin
architecture; for example, JSON and RTF/CRE dictionaries are both implemented
with dictionary plugins, and the English Stenotype layout is a system plugin.

```{toctree}
:maxdepth: 1

plugin-dev/setup

plugin-dev/commands
plugin-dev/metas
plugin-dev/macros
plugin-dev/dictionaries
plugin-dev/systems
plugin-dev/machines
plugin-dev/extensions
plugin-dev/gui_tools

plugin-dev/publishing
```
