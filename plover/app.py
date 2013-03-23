# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Configuration, initialization, and control of the Plover steno pipeline.

This module's single class, StenoEngine, encapsulates the
configuration, initialization, and control (starting and stopping) of
a complete stenographic processing pipeline, from reading stroke keys
from a stenotype machine to outputting translated English text to the
screen. Configuration parameters are read from a user-editable
configuration file. In addition, application log files are maintained
by this module. This module does not provide a graphical user
interface.

"""

# Import standard library modules.
from os.path import join, isfile, splitext
import logging
from logging.handlers import RotatingFileHandler
try:
    import simplejson as json
except ImportError:
    import json

# Import plover modules.
import plover.config as conf
import plover.formatting as formatting
import plover.oslayer.keyboardcontrol as keyboardcontrol
import plover.steno as steno
from plover.machine import SUPPORTED_DICT as SUPPORTED_MACHINES_DICT
import plover.machine.base
import plover.machine.sidewinder
from plover.dictionary import SUPPORTED_DICT as SUPPORTED_DICTIONARIES_DICT
from plover.exception import InvalidConfigurationError


def check_steno_config(config_params):
    """This will do several check on the given configuration

    This method can be used in StenoEngine's __init__ method, but also
    when exiting the configuration dialog.

    @return: a tuple composed of:
        - a list of configuration errors
        - a tuple of the following values:
            * machine_type
            * dictionary_format
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

    # Set the steno dictionary format module.
    dictionary_format = config_params.get(conf.DICTIONARY_CONFIG_SECTION,
                                          conf.DICTIONARY_FORMAT_OPTION)
    if dictionary_format not in SUPPORTED_DICTIONARIES_DICT:
        # The dictionary format isn't supported
        error = InvalidConfigurationError(
            'Invalid configuration value for %s: %s' %
            (conf.DICTIONARY_FORMAT_OPTION, dictionary_format))
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
    try:
        try:
            with open(dictionary_path, 'r') as f:
                user_dictionary = json.load(f)
        except UnicodeDecodeError:
            with open(dictionary_path, 'r') as f:
                user_dictionary = json.load(f, conf.ALTERNATIVE_ENCODING)
    except ValueError:
        error = InvalidConfigurationError(
            'The dictionary file contains incorrect json.')
        errors.append(error)

    return errors, (machine_type, dictionary_format, user_dictionary)


class StenoEngine:
    """Top-level class for using a stenotype machine for text input.

    This class combines all the non-GUI pieces needed to use a
    stenotype machine as a general purpose text entry device in an X11
    environment. The entire pipeline consists of the following elements:

    machine: Typically an instance of the Stenotype class from one of
    the submodules of plover.machine. This object is responsible for
    monitoring a particular type of hardware for stenotype output and
    passing that output on to the translator.

    translator: Typically an instance of the plover.steno.Translator
    class. This object converts raw steno keys into strokes and
    strokes into translations. The translation objects are then passed
    on to the formatter.

    formatter: Typically an instance of the
    plover.formatting.Formatter class. This object converts
    translation objects into printable English text that can be
    displayed to the user. Orthographic and lexical rules, such as
    capitalization at the beginning of a sentence and pluralizing a
    word, are taken care of here. The formatted text is then passed on
    to the output.

    output: Typically an instance of the
    plover.oslayer.keyboardcontrol.KeyboardEmulation class. This object
    displays text on the screen.

    In addition to the above pieces, a logger records timestamped
    strokes and translations. Many of these pieces can be configured
    by the user via a configuration file, which is by default located
    at ~/.config/plover/plover.cfg and will be automatically generated
    with reasonable default values if it doesn't already exist.

    In general, the only methods of interest in an instance of this
    class are start and stop.

    """

    def __init__(self):
        """Creates and configures a single steno pipeline."""
        self.subscribers = []
        self.is_running = False
        self.machine = None
        self.machine_init = {}
        self.translator = None
        self.formatter = None
        self.output = None

        # Check and use configuration
        config_params_dict = conf.get_config()
        config_errors, config_values = check_steno_config(config_params_dict)
        machine_type, dictionary_format, user_dictionary = config_values
        self.config = config_params_dict

        for error in config_errors:
            # This will raise one of the configuration errors.
            raise error

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

        # Set the steno dictionary format module.
        self.dictionary_module = conf.import_named_module(
                                                dictionary_format,
                                                SUPPORTED_DICTIONARIES_DICT)
        if self.dictionary_module is None:
            raise InvalidConfigurationError(
                'Invalid configuration value for %s: %s' %
                (conf.DICTIONARY_FORMAT_OPTION, dictionary_format))

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
        self.output = keyboardcontrol.KeyboardEmulation()
        self.translator = steno.Translator(self.machine,
                                           user_dictionary,
                                           self.dictionary_module)
        self.formatter = formatting.Formatter(self.translator)
        auto_start = self.config.getboolean(conf.MACHINE_CONFIG_SECTION,
                                            conf.MACHINE_AUTO_START_OPTION)
        self.set_is_running(auto_start)

        # Add hooks for logging.
        if self.config.getboolean(conf.LOGGING_CONFIG_SECTION,
                                  conf.ENABLE_STROKE_LOGGING_OPTION):
            self.machine.add_callback(self._log_stroke)
        if self.config.getboolean(conf.LOGGING_CONFIG_SECTION,
                                  conf.ENABLE_TRANSLATION_LOGGING_OPTION):
            self.translator.add_callback(self._log_translation)

        # Start the machine monitoring for steno strokes.
        self.machine.start_capture()

    def set_is_running(self, value):
        self.is_running = value
        if self.is_running:
            self.formatter.text_output = self.output
        else:
            self.formatter.text_output = None
        if isinstance(self.machine, plover.machine.sidewinder.Stenotype):
            self.machine.suppress_keyboard(self.is_running)
        for callback in self.subscribers:
            callback()

    def destroy(self):
        """Halts the stenography capture-translate-format-display pipeline.

        Calling this method causes all worker threads involved to
        terminate. This method should be called at least once if the
        start method had been previously called. Calling this method
        more than once or before the start method has been called has
        no effect.

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

    def _log_translation(self, translation, overflow):
        self.logger.info(translation)
