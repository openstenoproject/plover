# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Configuration management."""

# Import standard library modules.
import os
import logging
import logging.handlers
import ConfigParser
import serial
import shutil

# Configuration paths.
ASSETS_DIR =  os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           'assets')
CONFIG_DIR = os.path.expanduser('~/.config/plover')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'plover.cfg')

# General configuration sections and options.
MACHINE_CONFIG_SECTION = 'Machine Configuration'
MACHINE_TYPE_OPTION = 'machine_type'
MACHINE_AUTO_START_OPTION = 'auto_start'
DICTIONARY_CONFIG_SECTION = 'Dictionary Configuration'
DICTIONARY_FILE_OPTION = 'dictionary_file'
DICTIONARY_FORMAT_OPTION = 'dictionary_format'
LOGGING_CONFIG_SECTION = 'Logging Configuration'
LOG_FILE_OPTION = 'log_file'
ENABLE_STROKE_LOGGING_OPTION = 'enable_stroke_logging'
ENABLE_TRANSLATION_LOGGING_OPTION = 'enable_translation_logging'

# Default values for configuration options.
DEFAULT_MACHINE_TYPE = 'Microsoft Sidewinder X4'
DEFAULT_MACHINE_AUTO_START = 'false'
DEFAULT_DICTIONARY_FILE = 'dict.json'
DEFAULT_DICTIONARY_FORMAT = 'Eclipse'
DEFAULT_LOG_FILE = 'plover.log'
DEFAULT_ENABLE_STROKE_LOGGING = 'true'
DEFAULT_ENABLE_TRANSLATION_LOGGING = 'true'

# Dictionary constants.
JSON_EXTENSION = '.json'
ALTERNATIVE_ENCODING = 'latin-1'

# Logging constants.
LOG_EXTENSION = '.log'
LOGGER_NAME = 'plover_logger'
LOG_FORMAT = '%(asctime)s %(message)s'
LOG_MAX_BYTES = 10000000
LOG_COUNT = 9

# Serial port options.
SERIAL_PORT_OPTION = 'port'
SERIAL_BAUDRATE_OPTION = 'baudrate'
SERIAL_BYTESIZE_OPTION = 'bytesize'
SERIAL_PARITY_OPTION = 'parity'
SERIAL_STOPBITS_OPTION = 'stopbits'
SERIAL_TIMEOUT_OPTION = 'timeout'
SERIAL_XONXOFF_OPTION = 'xonxoff'
SERIAL_RTSCTS_OPTION = 'rtscts'
SERIAL_ALL_OPTIONS = (SERIAL_PORT_OPTION,
                      SERIAL_BAUDRATE_OPTION,
                      SERIAL_BYTESIZE_OPTION,
                      SERIAL_PARITY_OPTION,
                      SERIAL_STOPBITS_OPTION,
                      SERIAL_TIMEOUT_OPTION,
                      SERIAL_XONXOFF_OPTION,
                      SERIAL_RTSCTS_OPTION)
SERIAL_DEFAULT_TIMEOUT = 2.0

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
        with open(config_file, 'w') as f:
            f.close()
        
    # Read in the configuration file.
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    verify_config(config)
    return config

def verify_config(config):
    """Checks that the configuration contains values for all parameters.

    Arguments:

    config -- A ConfigParser.RawConfigParser object.

    Returns True if all parameters were found. Otherwise returns False
    and adds default values for all parameters.

    """
    config_file = CONFIG_FILE
    # Verify options exist.
    for section, option, default  in (\
      (LOGGING_CONFIG_SECTION, LOG_FILE_OPTION,
                               DEFAULT_LOG_FILE),
      (LOGGING_CONFIG_SECTION, ENABLE_TRANSLATION_LOGGING_OPTION,
                               DEFAULT_ENABLE_TRANSLATION_LOGGING),
      (LOGGING_CONFIG_SECTION, ENABLE_STROKE_LOGGING_OPTION,
                               DEFAULT_ENABLE_STROKE_LOGGING),
      (DICTIONARY_CONFIG_SECTION, DICTIONARY_FORMAT_OPTION,
                                  DEFAULT_DICTIONARY_FORMAT),
      (DICTIONARY_CONFIG_SECTION, DICTIONARY_FILE_OPTION,
                                  DEFAULT_DICTIONARY_FILE),
      (MACHINE_CONFIG_SECTION, MACHINE_TYPE_OPTION,
                               DEFAULT_MACHINE_TYPE),
      (MACHINE_CONFIG_SECTION, MACHINE_AUTO_START_OPTION,
                               DEFAULT_MACHINE_AUTO_START),
      ):
        if not config.has_section(section):
            config.add_section(section)
        if not config.has_option(section, option):
            config.set(section, option, default)
    
    # Write the file to disk.
    with open(config_file, 'w') as f:
        config.write(f)


def get_serial_params(section, config):
    """Returns the serial.Serial parameters stored in the given configuration.

    Arguments:

    section -- A string representing the section name containing the
    parameters of interest.

    config -- The ConfigParser object containing the parameters of
    interest.

    If config does not contain section, then a the default
    serial.Serial parameters are returned. If not all parameters are
    included in the section, then default values for the missing
    parameters are used in their place.

    """
    serial_params = {}
    default_serial_port = serial.Serial()
    for opt in SERIAL_ALL_OPTIONS:
        serial_params[opt] = default_serial_port.__getattribute__(opt)
    for opt in (SERIAL_PORT_OPTION,
                SERIAL_PARITY_OPTION):
        if config.has_option(section, opt):
            serial_params[opt] = config.get(section, opt)
    for opt in (SERIAL_BAUDRATE_OPTION,
                SERIAL_BYTESIZE_OPTION,
                SERIAL_STOPBITS_OPTION):
        if config.has_option(section, opt):
            serial_params[opt] = config.getint(section, opt)
    for opt in (SERIAL_XONXOFF_OPTION,
                SERIAL_RTSCTS_OPTION):
        if config.has_option(section, opt):
            serial_params[opt] = config.getboolean(section, opt)
    if config.has_option(section, SERIAL_TIMEOUT_OPTION):
        timeout = config.get(section, SERIAL_TIMEOUT_OPTION)
        if timeout == 'None':
            timeout = None
        else:
            timeout = float(timeout)
    else:
        timeout = SERIAL_DEFAULT_TIMEOUT
    serial_params[SERIAL_TIMEOUT_OPTION] = timeout
    # Helper class to convert a dictionary to an object.
    class _Struct(object):
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    return _Struct(**serial_params)

def set_serial_params(serial_port, section, config):
    """Writes a serial.Serial object to a section of a ConfigParser object.

    Arguments:

    serial_port -- A serial.Serial object or an object with the same
    constructor parameters. The parameters of this object will be
    written to the configuration. If None, no action is taken.

    section -- A string representing the section name in which to
    write the serial port parameters.

    config -- The ConfigParser object containing to which to write.

    """
    if serial_port is None:
        return
    if not config.has_section(section):
        config.add_section(section)
    for opt in SERIAL_ALL_OPTIONS:
        config.set(section, opt, serial_port.__getattribute__(opt))
