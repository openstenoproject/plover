# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Configuration management."""

# Import standard library modules.
import os
import logging
import logging.handlers
import ConfigParser
import shutil

# Configuration paths.
ASSETS_DIR =  os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           'assets')
CONFIG_DIR = os.path.expanduser('~/.config/plover')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'plover.cfg')

# Configuration sections and options.
MACHINE_CONFIG_SECTION = 'Machine Configuration'
MACHINE_TYPE_OPTION = 'machine_type'
DICTIONARY_CONFIG_SECTION = 'Dictionary Configuration'
DICTIONARY_FILE_OPTION = 'dictionary_file'
DICTIONARY_FORMAT_OPTION = 'dictionary_format'
LOGGING_CONFIG_SECTION = 'Logging Configuration'
LOG_FILE_OPTION = 'log_file'
ENABLE_STROKE_LOGGING_OPTION = 'enable_stroke_logging'
ENABLE_TRANSLATION_LOGGING_OPTION = 'enable_translation_logging'

# Default values for configuration options.
DEFAULT_MACHINE_TYPE = 'Microsoft Sidewinder X4'
DEFAULT_DICTIONARY_FILE = 'dict.json'
DEFAULT_DICTIONARY_FORMAT = 'Eclipse'
DEFAULT_LOG_FILE = 'plover.log'
DEFAULT_ENABLE_STROKE_LOGGING = 'true'
DEFAULT_ENABLE_TRANSLATION_LOGGING = 'true'

# Dictionary constants.
JSON_EXTENSION = '.json'
ALTERNATIVE_ENCODING = 'latin-1'

# Logging constants.
LOGGER_NAME = 'plover_logger'
LOG_FORMAT = '%(asctime)s %(message)s'
LOG_MAX_BYTES = 10000000
LOG_COUNT = 9

def import_named_module(name, module_dictionary):
    """Returns the Python module corresponding to the given name.

    Arguments:

    name -- A string that serves as a key to a Python module.

    module_dictionary -- A dictionary containing name-module key
    pairs. Both name and module are strings; name is an arbitrary
    string and module is a string that specifies a module that can be
    imported.

    Returns the references module, or None if the name is not a key in
    the module_dictionary.
    
    """
    mod_name =  module_dictionary.get(name, None)
    if mod_name is not None:
        hierarchy = mod_name.rsplit('.', 1)
        if len(hierarchy) == 2:
            fromlist = hierarchy[0]
        else:
            fromlist = []
        return __import__(mod_name, fromlist=fromlist)
    return None

def get_config():
    """Return Plover's ConfigParser object.

    If the given configuration file does not exist, a default
    configuration file is created.
    
    """
    config_dir = CONFIG_DIR
    config_file = CONFIG_FILE

    # Create the configuration directory if needed.
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        # Copy the default dictionary to the configuration directory.
        shutil.copyfile(os.path.join(ASSETS_DIR, DEFAULT_DICTIONARY_FILE),
                        os.path.join(config_dir,
                                     DEFAULT_DICTIONARY_FILE))

    # Create a default configuration file if one doesn't already
    # exist. Add default settings in reverse order so they appear
    # in the correct order when written to the file.
    if not os.path.exists(config_file):
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
        with open(config_file, 'w') as f:
            default_config.write(f)

    # Read in the configuration file.
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    return config
