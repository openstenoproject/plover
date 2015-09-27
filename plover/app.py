# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

# TODO: unit test this module

"""Configuration, initialization, and control of the Plover steno pipeline.

This module's single class, StenoEngine, encapsulates the configuration,
initialization, and control (starting and stopping) of a complete stenographic
processing pipeline, from reading stroke keys from a stenotype machine to
outputting translated English text to the screen. Configuration parameters are
read from a user-editable configuration file. In addition, application log files
are maintained by this module. This module does not provide a graphical user
interface.

"""


# Import plover modules.
import plover.config as conf
import plover.formatting as formatting
import plover.oslayer.keyboardcontrol as keyboardcontrol
import plover.steno as steno
import plover.machine.base
import plover.machine.sidewinder
import plover.machine.kinesis
import plover.steno_dictionary as steno_dictionary
import plover.steno as steno
import plover.translation as translation
from plover.dictionary.base import load_dictionary
from plover.exception import InvalidConfigurationError,DictionaryLoaderException
import plover.dictionary.json_dict as json_dict
import plover.dictionary.rtfcre_dict as rtfcre_dict
from plover.machine.registry import machine_registry, NoSuchMachineException
from plover.logger import Logger
from plover.dictionary.loading_manager import manager as dict_manager

# Because 2.7 doesn't have this yet.
class SimpleNamespace(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def __repr__(self):
        keys = sorted(self.__dict__)
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        return "{}({})".format(type(self).__name__, ", ".join(items))


def init_engine(engine, config):
    """Initialize a StenoEngine from a config object."""
    reset_machine(engine, config)
    
    dictionary_file_names = config.get_dictionary_file_names()
    try:
        dicts = dict_manager.load(dictionary_file_names)
    except DictionaryLoaderException as e:
        raise InvalidConfigurationError(unicode(e))
    engine.get_dictionary().set_dicts(dicts)

    log_file_name = config.get_log_file_name()
    if log_file_name:
        engine.set_log_file_name(log_file_name)

    engine.enable_stroke_logging(config.get_enable_stroke_logging())
    engine.enable_translation_logging(config.get_enable_translation_logging())
    engine.set_space_placement(config.get_space_placement())
    
    engine.set_is_running(config.get_auto_start())

def reset_machine(engine, config):
    """Set the machine on the engine based on config."""
    machine_type = config.get_machine_type()
    machine_options = config.get_machine_specific_options(machine_type)
    try:
        instance = machine_registry.get(machine_type)(machine_options)
    except NoSuchMachineException as e:
        raise InvalidConfigurationError(unicode(e))
    engine.set_machine(instance)

def update_engine(engine, old, new):
    """Modify a StenoEngine using a before and after config object.
    
    Using the before and after allows this function to not make unnecessary 
    changes.
    """
    machine_type = new.get_machine_type()
    machine_options = new.get_machine_specific_options(machine_type)
    if (old.get_machine_type() != machine_type or 
        old.get_machine_specific_options(machine_type) != machine_options):
        try:
            machine_class = machine_registry.get(machine_type)
        except NoSuchMachineException as e:
            raise InvalidConfigurationError(unicode(e))
        engine.set_machine(machine_class(machine_options))

    dictionary_file_names = new.get_dictionary_file_names()
    if old.get_dictionary_file_names() != dictionary_file_names:
        try:
            dicts = dict_manager.load(dictionary_file_names)
        except DictionaryLoaderException as e:
            raise InvalidConfigurationError(unicode(e))
        engine.get_dictionary().set_dicts(dicts)

    log_file_name = new.get_log_file_name()
    if old.get_log_file_name() != log_file_name:
        engine.set_log_file_name(log_file_name)

    enable_stroke_logging = new.get_enable_stroke_logging()
    if old.get_enable_stroke_logging() != enable_stroke_logging:
        engine.enable_stroke_logging(enable_stroke_logging)

    enable_translation_logging = new.get_enable_translation_logging()
    if old.get_enable_translation_logging() != enable_translation_logging:
        engine.enable_translation_logging(enable_translation_logging)

    space_placement = new.get_space_placement()
    if old.get_space_placement() != space_placement:
        engine.set_space_placement(space_placement)

def same_thread_hook(fn, *args):
    fn(*args)

class StenoEngine(object):
    """Top-level class for using a stenotype machine for text input.

    This class combines all the non-GUI pieces needed to use a stenotype machine
    as a general purpose text entry device. The pipeline consists of the 
    following elements:

    machine: An instance of the Stenotype class from one of the submodules of 
    plover.machine. This object is responsible for monitoring a particular type 
    of hardware for stenotype output and passing that output on to the 
    translator.

    translator: An instance of the plover.steno.Translator class. This object 
    converts raw steno keys into strokes and strokes into translations. The 
    translation objects are then passed on to the formatter.

    formatter: An instance of the plover.formatting.Formatter class. This object 
    converts translation objects into printable text that can be displayed to 
    the user. Orthographic and lexical rules, such as capitalization at the 
    beginning of a sentence and pluralizing a word, are taken care of here. The 
    formatted text is then passed on to the output.

    output: An instance of plover.oslayer.keyboardcontrol.KeyboardEmulation 
    class plus a hook to the application allows output to the screen and control
    of the app with steno strokes.

    In addition to the above pieces, a logger records timestamped strokes and
    translations.

    """

    def __init__(self, thread_hook=same_thread_hook):
        """Creates and configures a single steno pipeline."""
        self.subscribers = []
        self.stroke_listeners = []
        self.is_running = False
        self.machine = None
        self.thread_hook = thread_hook

        self.translator = translation.Translator()
        self.formatter = formatting.Formatter()
        self.logger = Logger()
        self.translator.add_listener(self.logger.log_translation)
        self.translator.add_listener(self.formatter.format)
        # This seems like a reasonable number. If this becomes a problem it can
        # be parameterized.
        self.translator.set_min_undo_length(10)

        self.full_output = SimpleNamespace()
        self.command_only_output = SimpleNamespace()
        self.running_state = self.translator.get_state()
        self.set_is_running(False)

    def set_machine(self, machine):
        if self.machine:
            self.machine.remove_state_callback(self._machine_state_callback)
            self.machine.remove_stroke_callback(
                self._translator_machine_callback)
            self.machine.remove_stroke_callback(self.logger.log_stroke)
            self.machine.stop_capture()
        self.machine = machine
        if self.machine:
            self.machine.add_state_callback(self._machine_state_callback)
            self.machine.add_stroke_callback(self.logger.log_stroke)
            self.machine.add_stroke_callback(self._translator_machine_callback)
            self.machine.start_capture()
            self.set_is_running(self.is_running)
        else:
            self.set_is_running(False)

    def set_dictionary(self, d):
        self.translator.set_dictionary(d)

    def get_dictionary(self):
        return self.translator.get_dictionary()

    def set_is_running(self, value):
        self.is_running = value
        if self.is_running:
            self.translator.set_state(self.running_state)
            self.formatter.set_output(self.full_output)
        else:
            self.translator.clear_state()
            self.formatter.set_output(self.command_only_output)
        if (isinstance(self.machine, plover.machine.sidewinder.Stenotype)
            or isinstance(self.machine, plover.machine.kinesis.Stenotype)):
            self.machine.suppress_keyboard(self.is_running)
        for callback in self.subscribers:
            callback(None)

    def set_output(self, o):
        self.full_output.send_backspaces = o.send_backspaces
        self.full_output.send_string = o.send_string
        self.full_output.send_key_combination = o.send_key_combination
        self.full_output.send_engine_command = o.send_engine_command
        self.command_only_output.send_engine_command = o.send_engine_command

    def destroy(self):
        """Halts the stenography capture-translate-format-display pipeline.

        Calling this method causes all worker threads involved to terminate.
        This method should be called at least once if the start method had been
        previously called. Calling this method more than once or before the
        start method has been called has no effect.

        """
        if self.machine:
            self.machine.stop_capture()
        self.is_running = False

    def add_callback(self, callback):
        """Subscribes a function to receive changes of the is_running state.

        Arguments:

        callback -- A function that takes no arguments.

        """
        self.subscribers.append(callback)
        
    def set_log_file_name(self, filename):
        """Set the file name for log output."""
        self.logger.set_filename(filename)

    def enable_stroke_logging(self, b):
        """Turn stroke logging on or off."""
        self.logger.enable_stroke_logging(b)

    def set_space_placement(self, s):
        """Set whether spaces will be inserted before the output or after the output."""
        self.formatter.set_space_placement(s)
        
    def enable_translation_logging(self, b):
        """Turn translation logging on or off."""
        self.logger.enable_translation_logging(b)

    def add_stroke_listener(self, listener):
        self.stroke_listeners.append(listener)
        
    def remove_stroke_listener(self, listener):
        self.stroke_listeners.remove(listener)

    def _translate_stroke(self, s):
        stroke = steno.Stroke(s)
        self.translator.translate(stroke)
        for listener in self.stroke_listeners:
            listener(stroke)

    def _translator_machine_callback(self, s):
        self.thread_hook(self._translate_stroke, s)

    def _notify_listeners(self, s):
        for callback in self.subscribers:
            callback(s)

    def _machine_state_callback(self, s):
        self.thread_hook(self._notify_listeners, s)


