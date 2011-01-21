# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Configuration management."""

# Import standard library modules.
import os
import logging
import logging.handlers
import ConfigParser
import shutil
import serial

# Configuration paths.
ASSETS_DIR =  os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           'assets')
CONFIG_DIR = os.path.expanduser('~/.config/plover')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'plover.cfg')

# General configuration sections and options.
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
DEFAULT_SERIAL_ARGUMENTS = {'timeout' : 2.0}

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
      ):
        if not config.has_section(section):
            config.add_section(section)
        if not config.has_option(section, option):
            config.set(section, option, default)
    
    # Write the file to disk.
    with open(config_file, 'w') as f:
        config.write(f)


def get_serial_port(section, config):
    """Returns a serial.Serial object built from configuration options.

    Arguments:

    section -- A string representing the section name containing the
    parameters of interest.

    config -- The ConfigParser object containing the parameters of
    interest.

    If config does not contain section, then a default serial.Serial
    object is returned.

    """
    if config.has_section(section):
        serial_args = {'port': config.get(section, SERIAL_PORT_OPTION),
                       'baudrate': config.getint(section, SERIAL_BAUDRATE_OPTION),
                       'bytesize': config.getint(section, SERIAL_BYTESIZE_OPTION),
                       'parity': config.get(section, SERIAL_PARITY_OPTION),
                       'stopbits': config.getint(section, SERIAL_STOPBITS_OPTION),
                       'xonxoff': config.getboolean(section, SERIAL_XONXOFF_OPTION),
                       'rtscts': config.getboolean(section, SERIAL_RTSCTS_OPTION),
                       }
        timeout = config.get(section, SERIAL_TIMEOUT_OPTION)
        if timeout == 'None':
            serial_args['timeout'] = None
        else:
            serial_args['timeout'] = float(timeout)
    else:
        serial_args = DEFAULT_SERIAL_ARGUMENTS
    try:
        return serial.Serial(**serial_args)
    except serial.SerialException:
        return None

def set_serial_port(serial_port, section, config):
    """Writes a serial.Serial object to a section of a ConfigParser object.

    Arguments:

    serial_port -- The serial.Serial object to write to the
    configuration. If None, no action is taken.

    section -- A string representing the section name in which to
    write the serial port parameters.

    config -- The ConfigParser object containing to which to write.

    """
    if serial_port is None:
        return
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, SERIAL_PORT_OPTION, serial_port.port)
    config.set(section, SERIAL_BAUDRATE_OPTION, serial_port.baudrate)
    config.set(section, SERIAL_BYTESIZE_OPTION, serial_port.bytesize)
    config.set(section, SERIAL_PARITY_OPTION, serial_port.parity)
    config.set(section, SERIAL_STOPBITS_OPTION, serial_port.stopbits)
    config.set(section, SERIAL_TIMEOUT_OPTION, serial_port.timeout)
    config.set(section, SERIAL_XONXOFF_OPTION, serial_port.xonxoff)
    config.set(section, SERIAL_RTSCTS_OPTION, serial_port.rtscts)

