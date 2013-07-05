# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Configuration management."""

from ConfigParser import RawConfigParser
import os
import shutil
from cStringIO import StringIO
from plover.exception import InvalidConfigurationError
from plover.machine.registry import machine_registry
from plover.oslayer.config import ASSETS_DIR, CONFIG_DIR


# Config path.
CONFIG_FILE = os.path.join(CONFIG_DIR, 'plover.cfg')

# General configuration sections, options and defaults.
MACHINE_CONFIG_SECTION = 'Machine Configuration'
MACHINE_TYPE_OPTION = 'machine_type'
DEFAULT_MACHINE_TYPE = 'NKRO Keyboard'
MACHINE_AUTO_START_OPTION = 'auto_start'
DEFAULT_MACHINE_AUTO_START = False

DICTIONARY_CONFIG_SECTION = 'Dictionary Configuration'
DICTIONARY_FILE_OPTION = 'dictionary_file'
DEFAULT_DICTIONARY_FILE = 'dict.json'

LOGGING_CONFIG_SECTION = 'Logging Configuration'
LOG_FILE_OPTION = 'log_file'
DEFAULT_LOG_FILE = 'plover.log'
ENABLE_STROKE_LOGGING_OPTION = 'enable_stroke_logging'
DEFAULT_ENABLE_STROKE_LOGGING = True
ENABLE_TRANSLATION_LOGGING_OPTION = 'enable_translation_logging'
DEFAULT_ENABLE_TRANSLATION_LOGGING = True

# Dictionary constants.
JSON_EXTENSION = '.json'
RTF_EXTENSION = '.rtf'

# Logging constants.
LOG_EXTENSION = '.log'

# TODO: Unit test this class

class Config(object):

    def __init__(self):
        self._config = RawConfigParser()

    def load(self, fp):
        self._config = RawConfigParser()
        try:
            self._config.readfp(fp)
        except ConfigParser.Error as e:
            raise InvalidConfigurationError(str(e))

    def save(self, fp):
        self._config.write(fp)

    def clone(self):
        f = StringIO()
        self.save(f)
        c = Config()
        f.seek(0, 0)
        c.load(f)
        return c

    def set_machine_type(self, machine_type):
        self._set(MACHINE_CONFIG_SECTION, MACHINE_TYPE_OPTION, 
                         machine_type)

    def get_machine_type(self):
        return self._get(MACHINE_CONFIG_SECTION, MACHINE_TYPE_OPTION, 
                         DEFAULT_MACHINE_TYPE)

    def set_machine_specific_options(self, machine_name, options):
        if not self._config.has_section(machine_name):
            self._config.add_section(machine_name)
        for k, v in options.items():
            self._config.set(machine_name, k, str(v))

    def get_machine_specific_options(self, machine_name):
        machine = machine_registry.get(machine_name)
        option_info = machine.get_option_info()
        if self._config.has_section(machine_name):
            options = dict((o, self._config.get(machine_name, o)) 
                           for o in self._config.options(machine_name))
            return dict((k, option_info[k][1](v)) for k, v in options.items()
                        if k in option_info)
        return dict((k, v[0]) for k, v in option_info.items())

    def set_dictionary_file_name(self, filename):
        self._set(DICTIONARY_CONFIG_SECTION, DICTIONARY_FILE_OPTION, filename)

    def get_dictionary_file_name(self):
        return self._get(DICTIONARY_CONFIG_SECTION, DICTIONARY_FILE_OPTION, 
                         DEFAULT_DICTIONARY_FILE)

    def set_log_file_name(self, filename):
        self._set(LOGGING_CONFIG_SECTION, LOG_FILE_OPTION, filename)

    def get_log_file_name(self):
        return self._get(LOGGING_CONFIG_SECTION, LOG_FILE_OPTION, 
                         DEFAULT_LOG_FILE)

    def set_enable_stroke_logging(self, log):
        self._set(LOGGING_CONFIG_SECTION, ENABLE_STROKE_LOGGING_OPTION, log)

    def get_enable_stroke_logging(self):
        return self._get_bool(LOGGING_CONFIG_SECTION, 
                              ENABLE_STROKE_LOGGING_OPTION, 
                              DEFAULT_ENABLE_STROKE_LOGGING)

    def set_enable_translation_logging(self, log):
      self._set(LOGGING_CONFIG_SECTION, ENABLE_TRANSLATION_LOGGING_OPTION, log)

    def get_enable_translation_logging(self):
        return self._get_bool(LOGGING_CONFIG_SECTION, 
                              ENABLE_TRANSLATION_LOGGING_OPTION, 
                              DEFAULT_ENABLE_TRANSLATION_LOGGING)

    def set_auto_start(self, b):
        self._set(MACHINE_CONFIG_SECTION, MACHINE_AUTO_START_OPTION, b)

    def get_auto_start(self):
        return self._get_bool(MACHINE_CONFIG_SECTION, MACHINE_AUTO_START_OPTION, 
                              DEFAULT_MACHINE_AUTO_START)

    def _set(self, section, option, value):
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, option, str(value))

    def _get(self, section, option, default):
        if self._config.has_option(section, option):
            return self._config.get(section, option)
        return default

    def _get_bool(self, section, option, default):
        if self._config.has_option(section, option):
            return self._config.getboolean(section, option)
        return default
