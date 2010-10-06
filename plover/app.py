# Copyright (c) 2010 Joshua Harlan Lifton.
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
import os
import sys
import logging
import logging.handlers
import ConfigParser
import shutil

# Import third-party modules.
try :
    import simplejson as json
except ImportError :
    import json

# Import plover modules.
import formatting
import keyboardcontrol
import steno

# Configuration paths.
ASSETS_DIR =  os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           'assets')
DEFAULT_CONFIG_DIR = os.path.expanduser('~/.config/plover')
DEFAULT_CONFIG_FILE = 'plover.cfg'

# Configuration sections and options.
MACHINE_CONFIG_SECTION = 'Machine Configuration'
MACHINE_TYPE_OPTION = 'machine_type'
DICTIONARY_CONFIG_SECTION = 'Dictionary Configuration'
DICTIONARY_FILE_OPTION = 'dictionary_file'
DICTIONARY_FORMAT_OPTION = 'dictionary_format'
DICTIONARY_ENCODING_OPTION = 'dictionary_encoding'
LOGGING_CONFIG_SECTION = 'Logging Configuration'
LOG_FILE_OPTION = 'log_file'
ENABLE_STROKE_LOGGING_OPTION = 'enable_stroke_logging'
ENABLE_TRANSLATION_LOGGING_OPTION = 'enable_translation_logging'

# Default values for configuration options.
DEFAULT_MACHINE_TYPE = 'Microsoft Sidewinder X4'
DEFAULT_DICTIONARY_FILE = 'dict.json'
DEFAULT_DICTIONARY_FORMAT = 'Eclipse'
DEFAULT_DICTIONARY_ENCODING = 'latin-1'
DEFAULT_LOG_FILE = 'plover.log'
DEFAULT_ENABLE_STROKE_LOGGING = 'true'
DEFAULT_ENABLE_TRANSLATION_LOGGING = 'true'

# Stenotype machines.
MACHINE_SIDEWINDER_X4 = 'Microsoft Sidewinder X4'
MACHINE_GEMINI_PR = 'Gemini PR'

# Dictionary formats.
DICTIONARY_ECLIPSE = 'Eclipse'
DICTIONARY_DCAT = 'DCAT'
JSON_EXTENSION = '.json'

# Logging constants.
LOGGER_NAME = 'plover_logger'
LOG_FORMAT = '%(asctime)s %(message)s'
LOG_MAX_BYTES = 10000000
LOG_COUNT = 9

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
    plover.keyboardcontrol.KeyboardEmulation class. This object
    displays text on the screen.

    In addition to the above pieces, a logger records timestamped
    strokes and translations. Many of these pieces can be configured
    by the user via a configuration file, which is by default located
    at ~/.config/plover/plover.cfg and will be automatically generated
    with reasonable default values if it doesn't already exist.

    In general, the only methods of interest in an instance of this
    class are start and stop.

    """

    def __init__(self, config_dir=None, config_file=None):
        """Creates and configures a single instance of this class.

        Keyword arguments:
        
        config_dir -- The configuration directory to use, or
        ~/.config/plover if None.

        config_file -- The configuration file to use, or plover.cfg if
        None. This file is relative to the config_dir unless an
        absolute path is given.

        """

        # Set default values if arguments aren't given.
        if config_dir is None:
            config_dir = DEFAULT_CONFIG_DIR
        if config_file is None:
            config_file = os.path.join(config_dir, DEFAULT_CONFIG_FILE)
        self.config_dir = config_dir
        self.config_file = config_file

        # Build the core application.
        self.is_running = False
        self.machine = None
        self.translator = None
        self.formatter = None
        self.output = None
        self._configure()

    def start(self):
        """Initiates the stenography capture-translate-format-display pipeline.

        Calling this method causes a worker thread to begin capturing
        stenotype machine output and feeding the output to other
        elements of the pipeline.

        """
        # Don't run more than one steno machine at a time.
        if self.machine:
            self.machine.stop_capture()
            
        # Create the pipeline from machine to output.
        self.machine = self.machine_module.Stenotype(**self.machine_init_vars)
        self.output = keyboardcontrol.KeyboardEmulation()
        self.translator = steno.Translator(self.machine,
                                           self.dictionary,
                                           self.dictionary_module)
        self.formatter = formatting.Formatter(self.translator, self.output)

        # Add hooks for logging.
        if self.config.getboolean(LOGGING_CONFIG_SECTION,
                                  ENABLE_STROKE_LOGGING_OPTION):
            self.machine.add_callback(self._log_stroke)
        if self.config.getboolean(LOGGING_CONFIG_SECTION,
                                  ENABLE_TRANSLATION_LOGGING_OPTION):
            self.translator.add_callback(self._log_translation)

        # Start the machine monitoring for steno strokes.
        self.machine.start_capture()
        self.is_running = True

    def stop(self):
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

    def _configure(self):
        # Initialization based on user configuration file. If no
        # configuration file exists, a default configuration file is
        # created. This method should only be called if at start up or
        # if the user configuration file has changed, though creating
        # a new StenoEngine object is preferable to calling this
        # method.
        
        # Create config directory structure if it doesn't already exist.
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            # Copy the default dictionary to the configuration directory.
            shutil.copyfile(os.path.join(ASSETS_DIR, DEFAULT_DICTIONARY_FILE),
                            os.path.join(self.config_dir,
                                         DEFAULT_DICTIONARY_FILE))

        # Create a default configuration file if one doesn't already
        # exist. Add default settings in reverse order so they appear
        # in the correct order when written to the file.
        if not os.path.exists(self.config_file):
            default_config = ConfigParser.RawConfigParser()

            # Set default logging parameters.
            default_config.add_section(LOGGING_CONFIG_SECTION)
            default_config.set(LOGGING_CONFIG_SECTION,
                               ENABLE_TRANSLATION_LOGGING_OPTION,
                               DEFAULT_ENABLE_TRANSLATION_LOGGING)
            default_config.set(LOGGING_CONFIG_SECTION,
                               ENABLE_STROKE_LOGGING_OPTION,
                               DEFAULT_ENABLE_STROKE_LOGGING)
            default_config.set(LOGGING_CONFIG_SECTION,
                               LOG_FILE_OPTION,
                               DEFAULT_LOG_FILE)

            # Set default dictionary parameters.
            default_config.add_section(DICTIONARY_CONFIG_SECTION)
            default_config.set(DICTIONARY_CONFIG_SECTION,
                               DICTIONARY_ENCODING_OPTION,
                               DEFAULT_DICTIONARY_ENCODING)
            default_config.set(DICTIONARY_CONFIG_SECTION,
                               DICTIONARY_FORMAT_OPTION,
                               DEFAULT_DICTIONARY_FORMAT)
            default_config.set(DICTIONARY_CONFIG_SECTION,
                               DICTIONARY_FILE_OPTION,
                               DEFAULT_DICTIONARY_FILE)

            # Set default machine parameters.
            default_config.add_section(MACHINE_CONFIG_SECTION)
            default_config.set(MACHINE_CONFIG_SECTION,
                               MACHINE_TYPE_OPTION,
                               DEFAULT_MACHINE_TYPE)

            # Write the file to disk.
            with open(self.config_file, 'w') as f:
                default_config.write(f)

        # Read in the configuration file.
        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.config_file)

        # Set the machine module and any initialization variables.
        machine_type = self.config.get(MACHINE_CONFIG_SECTION,
                                       MACHINE_TYPE_OPTION)
        if self.config.has_section(machine_type):
            self.machine_init_vars = dict(config.items(machine_type))
        else:
            self.machine_init_vars = {}
        if machine_type == MACHINE_SIDEWINDER_X4:
            import plover.machine.sidewinder as machine_module
        elif machine_type == MACHINE_GEMINI_PR:
            import plover.machine.geminipr as machine_module
        else:
            raise ValueError('Invalid configuration value for %s: %s' %
                             (MACHINE_TYPE_OPTION, machine_type))
        self.machine_module = machine_module

        # Set the steno dictionary format module.
        dictionary_format = self.config.get(DICTIONARY_CONFIG_SECTION,
                                            DICTIONARY_FORMAT_OPTION)
        if dictionary_format == DICTIONARY_ECLIPSE:
            import plover.dictionary.eclipse as dictionary_module
        elif dictionary_format == DICTIONARY_DCAT:
            import plover.dictionary.dcat as dictionary_module
        else:
            raise ValueError('Invalid configuration value for %s: %s' %
                             (DICTIONARY_FORMAT_OPTION, dictionary_format))
        self.dictionary_module = dictionary_module

        # Load the dictionary. The dictionary path can be either
        # absolute or relative to the configuration directory.
        dictionary_encoding = self.config.get(DICTIONARY_CONFIG_SECTION,
                                              DICTIONARY_ENCODING_OPTION)
        dictionary_filename = self.config.get(DICTIONARY_CONFIG_SECTION,
                                              DICTIONARY_FILE_OPTION)
        dictionary_path = os.path.join(self.config_dir, dictionary_filename)
        if not os.path.isfile(dictionary_path):
            raise ValueError('Invalid configuration value for %s: %s' %
                             (DICTIONARY_FILE_OPTION, dictionary_path))
        dictionary_extension = os.path.splitext(dictionary_path)[1]
        if dictionary_extension == JSON_EXTENSION:
            with open(dictionary_path, 'r') as f:
                self.dictionary = json.load(f, dictionary_encoding)
        else:
            raise ValueError('The value of %s must end with %s.' %
                             (DICTIONARY_FILE_OPTION, JSON_EXTENSION))

        # Initialize the logger.
        log_file = os.path.join(self.config_dir,
                                self.config.get(LOGGING_CONFIG_SECTION,
                                                LOG_FILE_OPTION))
        self.logger = logging.getLogger(LOGGER_NAME)
        self.logger.setLevel(logging.DEBUG)
        handler = logging.handlers.RotatingFileHandler(log_file,
                                                       maxBytes=LOG_MAX_BYTES,
                                                       backupCount=LOG_COUNT)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        self.logger.addHandler(handler)


    def _log_stroke(self, steno_keys):
        self.logger.info('Stroke(%s)' % ' '.join(steno_keys))


    def _log_translation(self, translation, overflow):
        self.logger.info(translation)
