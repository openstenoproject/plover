Plugin Development Guide
========================

Plover plugins are generally implemented as separate Python packages installed
into the Python environment that Plover uses. In most cases, this environment
will be within Plover's installation directory; if you installed from source,
it will be the system Python distribution.

Plover uses a dynamic plugin discovery system via ``setuptools``'s
|entry_points|_ configuration to allow other packages to define themselves as
certain types of plugins for Plover. After collecting the registry of plugins
in the active Python environment on initialization, Plover has hooks in its
code to call into each of the different types in the registry at various parts
of its life cycle.

Most types of plugins will interact with Plover's steno engine using these
hooks. See the documentation on :class:`StenoEngine<plover.engine.StenoEngine>`
for more information on hooks and how to integrate them into your plugin code.

Much of Plover's built-in functionality is implemented within this plugin
architecture; for example, JSON and RTF/CRE dictionaries are both implemented
with dictionary plugins, and the English Stenotype layout is a system plugin.

.. |entry_points| replace:: ``entry_points``
.. _`entry_points`: https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins

Initial Setup
-------------

To create a Plover plugin, first
`create a Python package <https://packaging.python.org/tutorials/packaging-projects/>`__
with the following directory structure:

.. highlight:: none

::

    plover-my-plugin/
     |-- plover_my_plugin/
     |    '-- __init__.py
     |-- setup.cfg
     '-- setup.py

``setup.py``:

.. code-block:: python

    #!/usr/bin/env python3

    from setuptools import setup

    setup()

``setup.cfg``:

.. highlight:: ini

::

    [metadata]
    name = plover-my-plugin
    keywords = plover plover_plugin

    [options]
    zip_safe = True
    setup_requires =
      setuptools>=30.3.0
    install_requires =
      plover>=4.0.0.dev8
    packages =
      plover_my_plugin

    [options.entry_points]
    ...  # Your plugin components go here

Entry Points
^^^^^^^^^^^^

The ``entry_points`` section at the bottom of ``setup.cfg`` is where you will
add entry points for each plugin item you want to add. Each entry point should
refer to a certain module, function or class, depending on the plugin type.

The different types of entry points are:

.. describe:: plover.command

    Command plugins.

.. describe:: plover.dictionary

    Dictionary format plugins.

.. describe:: plover.extension

    Extension plugins.

.. describe:: plover.gui.qt.tool

    GUI tool plugins. Plugins of this type are only available when the Qt GUI
    is used.

.. describe:: plover.machine

    Machine plugins.

    .. describe:: plover.gui.qt.machine_option

        Machine configuration GUI widgets. Machine plugins that require
        configuration in addition to the default keyboard or serial
        options should have this entry point.

.. describe:: plover.macro

    Macro plugins.

.. describe:: plover.meta

    Meta plugins.

.. describe:: plover.system

    System plugins.

For example, the code below creates a dictionary entry point named ``custom``,
and two commands named ``foo_start`` and ``foo_stop``:

::

    [options.entry_points]
    plover.dictionary =
      custom = plover_my_plugin.dictionary:CustomDictionary
    plover.command =
      foo_start = plover_my_plugin.foo_cmd:foo_start
      foo_stop = plover_my_plugin.foo_cmd:foo_stop

Installation
^^^^^^^^^^^^

To install your plugin for development, use the command-line plugin installer:

.. highlight:: none

::

    cd plover-my-plugin
    plover -s plover_plugins install -e .

Make sure to use the ``-e`` flag to mark this package as editable. This allows
you to make changes to the plugin code without uninstalling and reinstalling
the plugin.

.. note::
    If you make any changes to ``setup.cfg`` during development, you will still
    need to uninstall and reinstall the plugin.

.. highlight:: python

Dictionaries
------------

To define a dictionary format with the file extension ``.abc``, add this name
(without the ``.``) as an entry point:

.. code-block:: ini

    [options.entry_points]
    plover.dictionary =
      abc = plover_my_plugin.dictionary:ExampleDictionary

Dictionary plugins are implemented as **classes** inheriting from
:class:`StenoDictionary<plover.steno_dictionary.StenoDictionary>`. Override the
``_load`` and ``_save`` methods *at least* to provide functionality to read and
write your desired dictionary format.

::

    from plover.steno_dictionary import StenoDictionary

    class ExampleDictionary(StenoDictionary):

      def _load(self, filename):
        # If you are not maintaining your own state format, self.update is usually
        # called here to add strokes / definitions to the dictionary state.
        pass

      def _save(self, filename):
        pass

Some dictionary formats, such as Python dictionaries, may require implementing
other parts of the class as well. See the documentation for
:class:`StenoDictionary<plover.steno_dictionary.StenoDictionary>` for more
information.

Note that setting ``readonly`` to ``True`` on your dictionary class will make
it so the user is not able to modify a dictionary of that type in the UI.

Machines
--------

To define a new machine called ``Example Machine``, add the name as an entry
point to your ``setup.py``:

.. code-block:: ini

    [options.entry_points]
    plover.machine =
      Example Machine = plover_my_plugin.machine:ExampleMachine

Machines are implemented as **classes** that inherit from one of a few machine
classes. The example shown uses the
:class:`ThreadedStenotypeBase<plover.machine.base.ThreadedStenotypeBase>` class
as it is the most common use case, but you can build machine plugins off of the
:class:`StenotypeBase<plover.machine.base.StenotypeBase>`,
:class:`SerialStenotypeBase<plover.machine.base.SerialStenotypeBase>`, or other
classes depending on your needs.

::

    from plover.machine.base import ThreadedStenotypeBase

    class ExampleMachine(ThreadedStenotypeBase):
      KEYS_LAYOUT: str = '0 1 2 3 4 5 6 7 8 9 10'
   
      def __init__(self, params):
        super().__init__()
        self._params = params

      def run(self):
        self._ready()
        while not self.finished.wait(1):
          self._notify(self.keymap.keys_to_actions(['1']))

      def start_capture(self):
        super().start_capture()

      def stop_capture(self):
        super().stop_capture()

      @classmethod
      def get_option_info(cls):
        pass

The ``_notify`` method should be called whenever a stroke is received. It takes
a set of key names in the current system (it's possible to convert from machine
key names to system key names (actions) with ``self.keymap.keys_to_actions``
function) and then tells the steno engine the key input that just occurred.

There are 3 ways to configure the keymap:

  * Add an entry for the machine in a system plugin's default bindings
    definition (``KEYMAPS`` variable)
  * The user can manually set the keymap in the Machine section in the
    configuration, along with any other additional configuration if a
    machine_option plugin is available for the machine type
  * Define a class variable ``KEYMAP_MACHINE_TYPE``, which means that the
    default configuration is the same as the default configuration of the
    specified machine.

See :doc:`api/machine` for more information.

Machine Options
^^^^^^^^^^^^^^^

If your machine requires additional configuration options, add a machine
options entry point:

.. code-block:: ini

    [options.entry_points]
    plover.gui_qt.machine_options =
      plover_my_plugin.machine:ExampleMachine = plover_my_plugin.machine:ExampleMachineOption

Machine options plugins are implemented as Qt widget **classes**:

::

    from PyQt5.QtWidgets import QWidget

    class ExampleMachineOption(QWidget):
      def setValue(self, value):
        pass

The process for developing these is similar to that for :ref:`gui_tools`.
See :ref:`qt_machine_options` for more information.

Systems
-------

To define a new system called ``Example System``, add it as an entry point:

.. code-block:: ini

    [options.entry_points]
    plover.system =
      Example System = plover_my_plugin.system

If you have any dictionaries, also add the following line to your
``MANIFEST.in``, to ensure that the dictionaries are copied when you distribute
the plugin:

.. code-block:: none

    include plover_my_plugin/dictionaries/*

System plugins are implemented as **modules** with all of the necessary fields
to create a custom key layout.

::

    # The keys in your system, defined in steno order
    KEYS: Tuple[str, ...]
    # Keys that serve as an implicit hyphen between the two sides of a stroke
    IMPLICIT_HYPHEN_KEYS: Tuple[str, ...]

    # Singular keys that are defined with suffix strokes in the dictionary
    # to allow for folding them into a stroke without an explicit definition
    SUFFIX_KEYS: Tuple[str, ...]

    # The key that serves as the "number key" like # in English
    NUMBER_KEY: Optional[str]
    # A mapping of keys to number aliases, e.g. {"S-": "1-"} means "#S-" can be
    # written as "1-"
    NUMBERS: Dict[str, str]

    # The stroke to undo the last stroke
    UNDO_STROKE_STENO: str

    # A list of rules mapping regex inputs to outputs for orthography.
    ORTHOGRAPHY_RULES: List[Tuple[str, str]]
    # Aliases for similar or interchangeable suffixes, e.g. "able" and "ible"
    ORTHOGRAPHY_RULES_ALIASES: Dict[str, str]
    # Name of a file containing words that can be used to resolve ambiguity
    # when applying suffixes.
    ORTHOGRAPHY_WORDLIST: Optional[str]

    # Default key mappins for machine plugins to system keys.
    KEYMAPS: Dict[str, Dict[str, Union[str, Tuple[str, ...]]]]

    # Root location for default dictionaries
    DICTIONARIES_ROOT: str
    # File names of default dictionaries
    DEFAULT_DICTIONARIES: Tuple[str, ...]

Note that there are a lot of possible fields in a system plugin. You must set
them all to something but you don't necessarily have to set them to something
*meaningful* (i.e. some can be empty), so they can be pretty straightforward.

Since it is a Python file rather than purely declarative you can run code for
logic as needed, but Plover will try to directly access all of these fields,
which does not leave much room for that. However, it does mean that if for
example you wanted to make a slight modification on the standard English system
to add a key, you could import it and set your system's fields to its fields
as desired with changes to ``KEYS`` only; or, you could make a base system
class that you import and expand with slightly different values in the various
fields for multiple system plugins like Michela does for Italian.

See the documentation for :mod:`plover.system` for information on all the fields.

Commands
--------

To define a new command called ``example_command``, add this name as an
entry point in ``setup.cfg``:

.. code-block:: ini

    [options.entry_points]
    plover.command =
      example_command = plover_my_plugin.command:example

The command can be used in dictionary entries:

.. code-block:: json

    {
      "S-": "{PLOVER:EXAMPLE_COMMAND:argument}",
      "T-": "{PLOVER:EXAMPLE_COMMAND}"
    }

Command plugins are implemented as **functions** that take a
:class:`StenoEngine<plover.engine.StenoEngine>` and an optional string
argument. If an argument is not passed in the dictionary entry, it will be
``''``.

::

    def example_command(engine, argument):
      pass

Macros
------

To define a macro called ``example_macro``, add the name as an entry point:

.. code-block:: ini

    [options.entry_points]
    plover.macro =
      example_macro = plover_my_plugin.macro:example

The macro can be used in dictionary entries:

.. code-block:: json

    {
      "S-": "=example_macro:argument",
      "T-": "=example_macro"
    }

Macros are implemented as **functions** that take a
:class:`Translator<plover.translation.Translator>` object, a
:class:`Stroke<plover.steno.Stroke>` object, and an optional string argument.
If an argument is not passed in the dictionary entry, it will be ``''``.

::

    def example(translator, stroke, argument) -> None:
      pass

Various methods of the translator can be used to either access or undo
previously translated entries, as well as apply new translations. See the
documentation for :class:`Translator<plover.translation.Translator>`
for more information.

Metas
-----

To define a meta called ``example_meta``, add the name as an entry point:

.. code-block:: ini

    [options.entry_points]
    plover.meta =
      example_meta = plover_my_plugin.meta:example

The meta can be used in dictionary entries:

.. code-block:: json

    {
      "S-": "{:example_meta:argument}",
      "T-": "{:example_meta}"
    }

Metas are implemented as **functions** that take a
:class:`formatting._Context<plover.formatting._Context>` and an optional string
argument. If an argument is not passed in the dictionary entry, it will be ``''``.
The meta function returns a :class:`formatting._Action<plover.formatting._Action>`
which will then be applied to the existing output.

You will want to use either
:meth:`context.new_action()<plover.formatting._Context.new_action>` or
:meth:`context.copy_last_action()<plover.formatting._Context.copy_last_action>`
as the basis for the output value. Previously translated text can also be accessed.

::

    def example(ctx, argument) -> None:
      pass

Various methods of the translator can be used to either access or undo
previously translated entries, as well as apply new translations. See the
documentation for :class:`Translator<plover.translation.Translator>` for more
information.

.. _gui_tools:

GUI Tools
---------

Plugins containing GUI tools will also require modifying the ``setup.py``
as follows:

::

    from setuptools import setup
    from plover_build_utils.setup import BuildPy, BuildUi

    BuildPy.build_dependencies.append("build_ui")
    BuildUi.hooks = ["plover_build_utils.pyqt:fix_icons"]
    CMDCLASS = {
      "build_py": BuildPy,
      "build_ui": BuildUi,
    }

    setup(cmdclass=CMDCLASS)

By making these changes, you get commands to generate Python files from your
Qt Designer UI and resource files:

.. code-block:: none

    python3 setup.py build_py build_ui

In addition, create a file named ``MANIFEST.in`` in your plugin directory as
follows. Change the paths as needed, but make sure to only include the Qt
Designer ``.ui`` files and resources, and not the generated Python files.

.. code-block:: none

    exclude plover_my_plugin/tool/*_rc.py
    exclude plover_my_plugin/tool/*_ui.py
    include plover_my_plugin/tool/*.ui
    recursive-include plover_my_plugin/tool/resources *

.. code-block:: ini

    [options.entry_points]
    plover.gui.qt.tool =
      example_tool = plover_my_plugin.tool:Main

GUI tools are implemented as Qt widget **classes** inheriting from
:class:`Tool<plover.gui_qt.tool.Tool>`:

::

    from plover.gui_qt.tool import Tool

    # You will also want to import / inherit for your Python class generated by
    # your .ui file if you are using Qt Designer for creating your UI rather
    # than only from code
    class Main(Tool):
      TITLE = 'Example Tool'
      ICON = ''
      ROLE = 'example_tool'

      def __init__(self, engine):
        super().__init__(engine)
        # If you are inheriting from your .ui generated class, also call
        # self.setupUi(self) before any additional setup code

Keep in mind that when you need to make changes to the UI, you will need to
generate new Python files.

See the documentation on :class:`Tool<plover.gui_qt.tool.Tool>` for more
information.

Extensions
----------

Extension plugins are implemented as **classes**. The initializer should take
only a :class:`StenoEngine<plover.engine.StenoEngine>` as a parameter.

.. code-block:: ini

    [options.entry_points]
    plover.extension =
      example_extension = plover_my_plugin.extension:Extension

::

    class Extension:
      def __init__(self, engine):
        # Called once to initialize an instance which lives until Plover exits.
        pass

      def start(self):
        # Called to start the extension or when the user enables the extension.
        # It can be used to start a new thread for example.
        pass

      def stop(self):
        # Called when Plover exits or the user disables the extension.
        pass

Publishing
----------

Once you've finished testing your plugin works as expected, you're ready to
publish it to be installed by other users that are not developers. This is done
by uploading your package to `Python Package Index`_ (PyPI) with some
guidelines around it.

.. _`Python Package Index`: https://pypi.org/

Those guidelines up front:

  * Your plugin's name as defined in your setup files should start with
    ``plover-`` to avoid clashing with general Python package namespaces
  * Your plugin's setup files must define one of its keywords to be
    ``plover_plugin`` as this is how the plugin manager finds it on PyPI
  * Your plugin's setup files must define a ``long_description``. The plugin
    manager can display plain text, ``.rst``, or ``.md`` files specified here.
  * Your plugin should only use features that the distributed version of Plover
    supports in order to prevent errors for end users; that version can be
    verified by looking at Plover's setup files.

The first thing you need to do to actually publish is make an account on PyPI
which should be relatively straightforward.

There are a myriad of ways to actually build and publish a package but the
easiest and most recommended way to publish to PyPI is by running ``twine`` in
your plugin directory like so:

.. code-block:: none

    python setup.py sdist bdist_wheel
    twine upload dist/*

See its documentation for more information on how to install it and set it up.
You don't need to publish to Test PyPI as it suggests unless you want to as
part of your workflow. One thing to note about ``twine`` is it will
automatically convert your ``plover_x_name`` snake case name for your plugin
into a ``plover-x-name`` hyphenated name for the package it uploads.

Once published, your plugin will appear in the plugin manager anywhere from
right away to a few hours later depending on end user caching. If you make
updates to your plugin and need to publish that, just make sure to bump the
version in your setup files and otherwise the steps are exactly the same.
