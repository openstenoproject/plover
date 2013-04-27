# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Configuration, initialization, and control of the Plover steno pipeline.

This module's single class, StenoEngine, encapsulates the configuration,
initialization, and control (starting and stopping) of a complete stenographic
processing pipeline, from reading stroke keys from a stenotype machine to
outputting translated English text to the screen. Configuration parameters are
read from a user-editable configuration file. In addition, application log files
are maintained by this module. This module does not provide a graphical user
interface.

"""

# Import standard library modules.
from os.path import join, isfile, splitext
import logging
from logging.handlers import RotatingFileHandler

# Import plover modules.
import plover.config as conf
import plover.formatting as formatting
import plover.oslayer.keyboardcontrol as keyboardcontrol
import plover.steno as steno
from plover.machine import SUPPORTED_DICT as SUPPORTED_MACHINES_DICT
import plover.machine.base
import plover.machine.sidewinder
from plover.exception import InvalidConfigurationError
import steno_dictionary
import steno
import translation

# Because 2.7 doesn't have this yet.
class SimpleNamespace(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def __repr__(self):
        keys = sorted(self.__dict__)
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        return "{}({})".format(type(self).__name__, ", ".join(items))
        

def check_steno_config(config_params):
    """This will do several check on the given configuration

    This method can be used in StenoEngine's __init__ method, but also when
    exiting the configuration dialog.

    @return: a tuple composed of:
        - a list of configuration errors
        - a tuple of the following values:
            * machine_type
            * user_dictionary
    """
    errors = []
    machine_type = config_params.get(conf.MACHINE_CONFIG_SECTION,
                                     conf.MACHINE_TYPE_OPTION)
    if machine_type not in SUPPORTED_MACHINES_DICT:
        # The machine isn't supported
        error = InvalidConfigurationError(
            'Invalid configuration value for %s: %s' %
            (conf.MACHINE_TYPE_OPTION, machine_type))
        errors.append(error)

    # Load the dictionary. The dictionary path can be either
    # absolute or relative to the configuration directory.
    dictionary_filename = config_params.get(conf.DICTIONARY_CONFIG_SECTION,
                                            conf.DICTIONARY_FILE_OPTION)
    dictionary_path = join(conf.CONFIG_DIR, dictionary_filename)
    if not isfile(dictionary_path):
        error = InvalidConfigurationError(
            'Invalid configuration value for %s: %s' %
            (conf.DICTIONARY_FILE_OPTION, dictionary_path))
        errors.append(error)

    dictionary_extension = splitext(dictionary_path)[1]
    if dictionary_extension != conf.JSON_EXTENSION:
        error = InvalidConfigurationError(
            'The value of %s must end with %s.' %
            (conf.DICTIONARY_FILE_OPTION, conf.JSON_EXTENSION))
        errors.append(error)

    # Load the dictionary. The dictionary path can be either
    # absolute or relative to the configuration directory.
    user_dictionary = None
    try:
        with open(dictionary_path, 'r') as f:
            user_dictionary = steno_dictionary.load_dictionary(f.read())
    except ValueError:
        error = InvalidConfigurationError(
            'The dictionary file contains incorrect json.')
        errors.append(error)

    return errors, (machine_type, user_dictionary)


class StenoEngine(object):
    """Top-level class for using a stenotype machine for text input.

    This class combines all the non-GUI pieces needed to use a stenotype machine
    as a general purpose text entry device in an X11 environment. The entire
    pipeline consists of the following elements:

    machine: Typically an instance of the Stenotype class from one of the
    submodules of plover.machine. This object is responsible for monitoring a
    particular type of hardware for stenotype output and passing that output on
    to the translator.

    translator: Typically an instance of the plover.steno.Translator class. This
    object converts raw steno keys into strokes and strokes into translations.
    The translation objects are then passed on to the formatter.

    formatter: Typically an instance of the plover.formatting.Formatter class.
    This object converts translation objects into printable English text that
    can be displayed to the user. Orthographic and lexical rules, such as
    capitalization at the beginning of a sentence and pluralizing a word, are
    taken care of here. The formatted text is then passed on to the output.

    output: Typically an instance of the
    plover.oslayer.keyboardcontrol.KeyboardEmulation class. This object displays
    text on the screen.

    In addition to the above pieces, a logger records timestamped strokes and
    translations. Many of these pieces can be configured by the user via a
    configuration file, which is by default located at
    ~/.config/plover/plover.cfg and will be automatically generated with
    reasonable default values if it doesn't already exist.

    In general, the only methods of interest in an instance of this class are
    start and stop.

    """

    def __init__(self, engine_command_callback):
        """Creates and configures a single steno pipeline."""
        self.subscribers = []
        self.is_running = False
        self.machine = None
        self.machine_init = {}
        self.translator = None
        self.formatter = None
        self.output = None

        # Check and use configuration
        self.config = conf.get_config()
        config_errors, config_values = check_steno_config(self.config)
        for error in config_errors:
            # This will raise one of the configuration errors.
            raise error
            
        machine_type, user_dictionary = config_values

        # Set the machine module and any initialization variables.
        self.machine_module = conf.import_named_module(
                                                machine_type,
                                                SUPPORTED_MACHINES_DICT)
        if self.machine_module is None:
            raise InvalidConfigurationError(
                'Invalid configuration value for %s: %s' %
                (conf.MACHINE_TYPE_OPTION, machine_type))

        if issubclass(self.machine_module.Stenotype,
                      plover.machine.base.SerialStenotypeBase):
            serial_params = conf.get_serial_params(machine_type, self.config)
            self.machine_init.update(serial_params.__dict__)

        # Initialize the logger.
        log_file = join(conf.CONFIG_DIR,
                        self.config.get(conf.LOGGING_CONFIG_SECTION,
                                        conf.LOG_FILE_OPTION))
        self.logger = logging.getLogger(conf.LOGGER_NAME)
        self.logger.setLevel(logging.DEBUG)
        handler = RotatingFileHandler(log_file, maxBytes=conf.LOG_MAX_BYTES,
                                      backupCount=conf.LOG_COUNT,)
        handler.setFormatter(logging.Formatter(conf.LOG_FORMAT))
        self.logger.addHandler(handler)

        # Construct the stenography capture-translate-format-display pipeline.
        self.machine = self.machine_module.Stenotype(**self.machine_init)
        self.translator = translation.Translator()
        self.translator.set_dictionary(user_dictionary)
        self.formatter = formatting.Formatter()
        
        # Add hooks for logging. Do this first so logs appear in order.
        if self.config.getboolean(conf.LOGGING_CONFIG_SECTION,
                                  conf.ENABLE_STROKE_LOGGING_OPTION):
            self.machine.add_callback(self._log_stroke)
        if self.config.getboolean(conf.LOGGING_CONFIG_SECTION,
                                  conf.ENABLE_TRANSLATION_LOGGING_OPTION):
            self.translator.add_listener(self._log_translation)
        
        self.machine.add_callback(
            lambda x: self.translator.translate(steno.Stroke(x)))
        self.translator.add_listener(self.formatter.format)
        # This seems like a reasonable number. If this becomes a problem it can
        # be parameterized.
        self.translator.set_min_undo_length(10)
        keyboard_control = keyboardcontrol.KeyboardEmulation()
        bag = SimpleNamespace()
        bag.send_backspaces = keyboard_control.send_backspaces
        bag.send_string = keyboard_control.send_string
        bag.send_key_combination = keyboard_control.send_key_combination
        bag.send_engine_command = engine_command_callback
        self.full_output = bag
        bag = SimpleNamespace()
        bag.send_engine_command = engine_command_callback
        self.command_only_output = bag
        self.running_state = self.translator.get_state()
        
        auto_start = self.config.getboolean(conf.MACHINE_CONFIG_SECTION,
                                            conf.MACHINE_AUTO_START_OPTION)
        self.set_is_running(auto_start)
        
        # Start the machine monitoring for steno strokes.
        self.machine.start_capture()

    def set_is_running(self, value):
        self.is_running = value
        if self.is_running:
            self.translator.set_state(self.running_state)
            self.formatter.set_output(self.full_output)
        else:
            self.translator.clear_state()
            self.formatter.set_output(self.command_only_output)
        if isinstance(self.machine, plover.machine.sidewinder.Stenotype):
            self.machine.suppress_keyboard(self.is_running)
        for callback in self.subscribers:
            callback()

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
        """Subscribes a function to receive changes of the is_running  state.

        Arguments:

        callback -- A function that takes no arguments.

        """
        self.subscribers.append(callback)

    def _log_stroke(self, steno_keys):
        self.logger.info('Stroke(%s)' % ' '.join(steno_keys))

    def _log_translation(self, undo, do, prev):
        # TODO: Figure out what to actually log here.
        for u in undo:
            self.logger.info('*%s', u)
        for d in do:
            self.logger.info(d)
