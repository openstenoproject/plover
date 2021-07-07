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

.. toctree::
    :maxdepth: 1

    plugin-dev/setup

    plugin-dev/commands
    plugin-dev/metas

    plugin-dev/publishing

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
