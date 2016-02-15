# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Configuration management."""

import ConfigParser
from ConfigParser import RawConfigParser
import os
from cStringIO import StringIO
from plover.exception import InvalidConfigurationError
from plover.machine.registry import machine_registry
from plover.oslayer.config import ASSETS_DIR, CONFIG_DIR

SPINNER_FILE = os.path.join(ASSETS_DIR, 'spinner.gif')

# Config path.
CONFIG_FILE = os.path.join(CONFIG_DIR, 'plover.cfg')

# General configuration sections, options and defaults.
MACHINE_CONFIG_SECTION = 'Machine Configuration'
MACHINE_TYPE_OPTION = 'machine_type'
DEFAULT_MACHINE_TYPE = 'Keyboard'
MACHINE_AUTO_START_OPTION = 'auto_start'
DEFAULT_MACHINE_AUTO_START = False

DEFAULT_DICTIONARIES = ['main.json',
                        'commands.json',
                        'user.json']

DICTIONARY_CONFIG_SECTION = 'Dictionary Configuration'
DICTIONARY_FILE_OPTION = 'dictionary_file'

LOGGING_CONFIG_SECTION = 'Logging Configuration'
LOG_FILE_OPTION = 'log_file'
DEFAULT_LOG_FILE = 'strokes.log'
ENABLE_STROKE_LOGGING_OPTION = 'enable_stroke_logging'
DEFAULT_ENABLE_STROKE_LOGGING = True
ENABLE_TRANSLATION_LOGGING_OPTION = 'enable_translation_logging'
DEFAULT_ENABLE_TRANSLATION_LOGGING = True

STROKE_DISPLAY_SECTION = 'Stroke Display'
STROKE_DISPLAY_SHOW_OPTION = 'show'
DEFAULT_STROKE_DISPLAY_SHOW = False
STROKE_DISPLAY_ON_TOP_OPTION = 'on_top'
DEFAULT_STROKE_DISPLAY_ON_TOP = True
STROKE_DISPLAY_STYLE_OPTION = 'style'
DEFAULT_STROKE_DISPLAY_STYLE = 'Paper'
STROKE_DISPLAY_X_OPTION = 'x'
DEFAULT_STROKE_DISPLAY_X = -1
STROKE_DISPLAY_Y_OPTION = 'y'
DEFAULT_STROKE_DISPLAY_Y = -1

SUGGESTIONS_DISPLAY_SECTION = 'Suggestions Display'
SUGGESTIONS_DISPLAY_SHOW_OPTION = 'show'
DEFAULT_SUGGESTIONS_DISPLAY_SHOW = False
SUGGESTIONS_DISPLAY_ON_TOP_OPTION = 'on_top'
DEFAULT_SUGGESTIONS_DISPLAY_ON_TOP = True
SUGGESTIONS_DISPLAY_X_OPTION = 'x'
DEFAULT_SUGGESTIONS_DISPLAY_X = -1
SUGGESTIONS_DISPLAY_Y_OPTION = 'y'
DEFAULT_SUGGESTIONS_DISPLAY_Y = -1

OUTPUT_CONFIG_SECTION = 'Output Configuration'
OUTPUT_CONFIG_SPACE_PLACEMENT_OPTION = 'space_placement'
DEFAULT_OUTPUT_CONFIG_SPACE_PLACEMENT = 'Before Output'

CONFIG_FRAME_SECTION = 'Config Frame'
CONFIG_FRAME_X_OPTION = 'x'
DEFAULT_CONFIG_FRAME_X = -1
CONFIG_FRAME_Y_OPTION = 'y'
DEFAULT_CONFIG_FRAME_Y = -1
CONFIG_FRAME_WIDTH_OPTION = 'width'
DEFAULT_CONFIG_FRAME_WIDTH = -1
CONFIG_FRAME_HEIGHT_OPTION = 'height'
DEFAULT_CONFIG_FRAME_HEIGHT = -1

MAIN_FRAME_SECTION = 'Main Frame'
MAIN_FRAME_X_OPTION = 'x'
DEFAULT_MAIN_FRAME_X = -1
MAIN_FRAME_Y_OPTION = 'y'
DEFAULT_MAIN_FRAME_Y = -1

TRANSLATION_FRAME_SECTION = 'Translation Frame'
TRANSLATION_FRAME_X_OPTION = 'x'
DEFAULT_TRANSLATION_FRAME_X = -1
TRANSLATION_FRAME_Y_OPTION = 'y'
DEFAULT_TRANSLATION_FRAME_Y = -1

LOOKUP_FRAME_SECTION = 'Lookup Frame'
LOOKUP_FRAME_X_OPTION = 'x'
DEFAULT_LOOKUP_FRAME_X = -1
LOOKUP_FRAME_Y_OPTION = 'y'
DEFAULT_LOOKUP_FRAME_Y = -1

DICTIONARY_EDITOR_FRAME_SECTION = 'Dictionary Editor Frame'
DICTIONARY_EDITOR_FRAME_X_OPTION = 'x'
DEFAULT_DICTIONARY_EDITOR_FRAME_X = -1
DICTIONARY_EDITOR_FRAME_Y_OPTION = 'y'
DEFAULT_DICTIONARY_EDITOR_FRAME_Y = -1

SERIAL_CONFIG_FRAME_SECTION = 'Serial Config Frame'
SERIAL_CONFIG_FRAME_X_OPTION = 'x'
DEFAULT_SERIAL_CONFIG_FRAME_X = -1
SERIAL_CONFIG_FRAME_Y_OPTION = 'y'
DEFAULT_SERIAL_CONFIG_FRAME_Y = -1

KEYBOARD_CONFIG_FRAME_SECTION = 'Keyboard Config Frame'
KEYBOARD_CONFIG_FRAME_X_OPTION = 'x'
DEFAULT_KEYBOARD_CONFIG_FRAME_X = -1
KEYBOARD_CONFIG_FRAME_Y_OPTION = 'y'
DEFAULT_KEYBOARD_CONFIG_FRAME_Y = -1

# Dictionary constants.
JSON_EXTENSION = '.json'
RTF_EXTENSION = '.rtf'

# Logging constants.
LOG_EXTENSION = '.log'

# TODO: Unit test this class

class Config(object):

    def __init__(self):
        self._config = RawConfigParser()
        # A convenient place for other code to store a file name.
        self.target_file = None

    def _path_to_config_value(self, path):
        ''' Return config value for a path.

            If the path is below CONFIG_DIR, a relative path to it is returned,
            otherwise, an absolute path is returned.

            Note: relative path are automatically assumed to be relative to CONFIG_DIR.
        '''
        path = os.path.realpath(os.path.join(CONFIG_DIR, path))
        config_dir = os.path.realpath(CONFIG_DIR) + os.sep
        if path.startswith(config_dir):
            return path[len(config_dir):]
        else:
            return path

    def _path_from_config_value(self, value):
        ''' Return a path from a config value.

            If value is an absolute path, it is returned as is
            otherwise, an absolute path relative to CONFIG_DIR is returned.
        '''
        return os.path.realpath(os.path.join(CONFIG_DIR, value))

    def load(self, fp):
        self._config = RawConfigParser()
        try:
            self._config.readfp(fp)
        except ConfigParser.Error as e:
            raise InvalidConfigurationError(str(e))

    def clear(self):
        self._config = RawConfigParser()

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
        if self._config.has_section(machine_name):
            self._config.remove_section(machine_name)
        self._config.add_section(machine_name)
        for k, v in options.items():
            self._config.set(machine_name, k, str(v))

    def get_machine_specific_options(self, machine_name):
        def convert(p, v):
            try:
                return p[1](v)
            except ValueError:
                return p[0]
        machine = machine_registry.get(machine_name)
        info = machine.get_option_info()
        defaults = {k: v[0] for k, v in info.items()}
        if self._config.has_section(machine_name):
            options = {o: self._config.get(machine_name, o) 
                       for o in self._config.options(machine_name)
                       if o in info}
            options = {k: convert(info[k], v) for k, v in options.items()}
            defaults.update(options)
        return defaults

    def set_dictionary_file_names(self, filenames):
        if self._config.has_section(DICTIONARY_CONFIG_SECTION):
            self._config.remove_section(DICTIONARY_CONFIG_SECTION)
        self._config.add_section(DICTIONARY_CONFIG_SECTION)
        filenames = [self._path_to_config_value(path) for path in filenames]
        for ordinal, filename in enumerate(filenames, start=1):
            option = DICTIONARY_FILE_OPTION + str(ordinal)
            self._config.set(DICTIONARY_CONFIG_SECTION, option, filename)

    def get_dictionary_file_names(self):
        filenames = []
        if self._config.has_section(DICTIONARY_CONFIG_SECTION):
            options = filter(lambda x: x.startswith(DICTIONARY_FILE_OPTION),
                             self._config.options(DICTIONARY_CONFIG_SECTION))
            options.sort(key=_dict_entry_key)
            filenames = [self._config.get(DICTIONARY_CONFIG_SECTION, o)
                         for o in options]
        if not filenames:
            filenames = DEFAULT_DICTIONARIES
        filenames = [self._path_from_config_value(path) for path in filenames]
        return filenames

    def set_log_file_name(self, filename):
        filename = self._path_to_config_value(filename)
        self._set(LOGGING_CONFIG_SECTION, LOG_FILE_OPTION, filename)

    def get_log_file_name(self):
        filename = self._get(LOGGING_CONFIG_SECTION, LOG_FILE_OPTION,
                             DEFAULT_LOG_FILE)
        return self._path_from_config_value(filename)

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

    def set_show_stroke_display(self, b):
        self._set(STROKE_DISPLAY_SECTION, STROKE_DISPLAY_SHOW_OPTION, b)

    def get_show_stroke_display(self):
        return self._get_bool(STROKE_DISPLAY_SECTION, 
            STROKE_DISPLAY_SHOW_OPTION, DEFAULT_STROKE_DISPLAY_SHOW)

    def set_show_suggestions_display(self, b):
        self._set(SUGGESTIONS_DISPLAY_SECTION, SUGGESTIONS_DISPLAY_SHOW_OPTION, b)

    def get_show_suggestions_display(self):
        return self._get_bool(SUGGESTIONS_DISPLAY_SECTION,
            SUGGESTIONS_DISPLAY_SHOW_OPTION, DEFAULT_SUGGESTIONS_DISPLAY_SHOW)

    def get_space_placement(self):
        return self._get(OUTPUT_CONFIG_SECTION, OUTPUT_CONFIG_SPACE_PLACEMENT_OPTION, 
                         DEFAULT_OUTPUT_CONFIG_SPACE_PLACEMENT)

    def set_space_placement(self, s):
        self._set(OUTPUT_CONFIG_SECTION, OUTPUT_CONFIG_SPACE_PLACEMENT_OPTION, s)

    def set_stroke_display_on_top(self, b):
        self._set(STROKE_DISPLAY_SECTION, STROKE_DISPLAY_ON_TOP_OPTION, b)

    def get_stroke_display_on_top(self):
        return self._get_bool(STROKE_DISPLAY_SECTION, 
            STROKE_DISPLAY_ON_TOP_OPTION, DEFAULT_STROKE_DISPLAY_ON_TOP)

    def set_suggestions_display_on_top(self, b):
        self._set(SUGGESTIONS_DISPLAY_SECTION, SUGGESTIONS_DISPLAY_ON_TOP_OPTION, b)

    def get_suggestions_display_on_top(self):
        return self._get_bool(SUGGESTIONS_DISPLAY_SECTION,
            SUGGESTIONS_DISPLAY_ON_TOP_OPTION, DEFAULT_SUGGESTIONS_DISPLAY_ON_TOP)

    def set_stroke_display_style(self, s):
        self._set(STROKE_DISPLAY_SECTION, STROKE_DISPLAY_STYLE_OPTION, s)

    def get_stroke_display_style(self):
        return self._get(STROKE_DISPLAY_SECTION, STROKE_DISPLAY_STYLE_OPTION, 
                         DEFAULT_STROKE_DISPLAY_STYLE)

    def set_stroke_display_x(self, x):
        self._set(STROKE_DISPLAY_SECTION, STROKE_DISPLAY_X_OPTION, x)

    def get_stroke_display_x(self):
        return self._get_int(STROKE_DISPLAY_SECTION, STROKE_DISPLAY_X_OPTION, 
                             DEFAULT_STROKE_DISPLAY_X)

    def set_stroke_display_y(self, y):
        self._set(STROKE_DISPLAY_SECTION, STROKE_DISPLAY_Y_OPTION, y)

    def get_stroke_display_y(self):
        return self._get_int(STROKE_DISPLAY_SECTION, STROKE_DISPLAY_Y_OPTION, 
                             DEFAULT_STROKE_DISPLAY_Y)

    def set_suggestions_display_x(self, x):
        self._set(SUGGESTIONS_DISPLAY_SECTION, SUGGESTIONS_DISPLAY_X_OPTION, x)

    def get_suggestions_display_x(self):
        return self._get_int(SUGGESTIONS_DISPLAY_SECTION, SUGGESTIONS_DISPLAY_X_OPTION,
                             DEFAULT_SUGGESTIONS_DISPLAY_X)

    def set_suggestions_display_y(self, y):
        self._set(SUGGESTIONS_DISPLAY_SECTION, SUGGESTIONS_DISPLAY_Y_OPTION, y)

    def get_suggestions_display_y(self):
        return self._get_int(SUGGESTIONS_DISPLAY_SECTION, SUGGESTIONS_DISPLAY_Y_OPTION,
                             DEFAULT_SUGGESTIONS_DISPLAY_Y)

    def set_config_frame_x(self, x):
        self._set(CONFIG_FRAME_SECTION, CONFIG_FRAME_X_OPTION, x)
        
    def get_config_frame_x(self):
        return self._get_int(CONFIG_FRAME_SECTION, CONFIG_FRAME_X_OPTION,
                             DEFAULT_CONFIG_FRAME_X)

    def set_config_frame_y(self, y):
        self._set(CONFIG_FRAME_SECTION, CONFIG_FRAME_Y_OPTION, y)
    
    def get_config_frame_y(self):
        return self._get_int(CONFIG_FRAME_SECTION, CONFIG_FRAME_Y_OPTION,
                             DEFAULT_CONFIG_FRAME_Y)

    def set_config_frame_width(self, width):
        self._set(CONFIG_FRAME_SECTION, CONFIG_FRAME_WIDTH_OPTION, width)

    def get_config_frame_width(self):
        return self._get_int(CONFIG_FRAME_SECTION, CONFIG_FRAME_WIDTH_OPTION,
                             DEFAULT_CONFIG_FRAME_WIDTH)

    def set_config_frame_height(self, height):
        self._set(CONFIG_FRAME_SECTION, CONFIG_FRAME_HEIGHT_OPTION, height)

    def get_config_frame_height(self):
        return self._get_int(CONFIG_FRAME_SECTION, CONFIG_FRAME_HEIGHT_OPTION,
                             DEFAULT_CONFIG_FRAME_HEIGHT)

    def set_main_frame_x(self, x):
        self._set(MAIN_FRAME_SECTION, MAIN_FRAME_X_OPTION, x)
    
    def get_main_frame_x(self):
        return self._get_int(MAIN_FRAME_SECTION, MAIN_FRAME_X_OPTION,
                             DEFAULT_MAIN_FRAME_X)

    def set_main_frame_y(self, y):
        self._set(MAIN_FRAME_SECTION, MAIN_FRAME_Y_OPTION, y)

    def get_main_frame_y(self):
        return self._get_int(MAIN_FRAME_SECTION, MAIN_FRAME_Y_OPTION,
                             DEFAULT_MAIN_FRAME_Y)

    def set_translation_frame_x(self, x):
        self._set(TRANSLATION_FRAME_SECTION, TRANSLATION_FRAME_X_OPTION, x)
    
    def get_translation_frame_x(self):
        return self._get_int(TRANSLATION_FRAME_SECTION, 
                             TRANSLATION_FRAME_X_OPTION,
                             DEFAULT_TRANSLATION_FRAME_X)

    def set_translation_frame_y(self, y):
        self._set(TRANSLATION_FRAME_SECTION, TRANSLATION_FRAME_Y_OPTION, y)

    def get_translation_frame_y(self):
        return self._get_int(TRANSLATION_FRAME_SECTION, 
                             TRANSLATION_FRAME_Y_OPTION,
                             DEFAULT_TRANSLATION_FRAME_Y)
                             
    def set_lookup_frame_x(self, x):
        self._set(LOOKUP_FRAME_SECTION, LOOKUP_FRAME_X_OPTION, x)
    
    def get_lookup_frame_x(self):
        return self._get_int(LOOKUP_FRAME_SECTION, 
                             LOOKUP_FRAME_X_OPTION,
                             DEFAULT_LOOKUP_FRAME_X)

    def set_lookup_frame_y(self, y):
        self._set(LOOKUP_FRAME_SECTION, LOOKUP_FRAME_Y_OPTION, y)

    def get_lookup_frame_y(self):
        return self._get_int(LOOKUP_FRAME_SECTION, 
                             LOOKUP_FRAME_Y_OPTION,
                             DEFAULT_LOOKUP_FRAME_Y)

    def set_dictionary_editor_frame_x(self, x):
        self._set(DICTIONARY_EDITOR_FRAME_SECTION, DICTIONARY_EDITOR_FRAME_X_OPTION, x)

    def get_dictionary_editor_frame_x(self):
        return self._get_int(DICTIONARY_EDITOR_FRAME_SECTION,
                             DICTIONARY_EDITOR_FRAME_X_OPTION,
                             DEFAULT_DICTIONARY_EDITOR_FRAME_X)

    def set_dictionary_editor_frame_y(self, y):
        self._set(DICTIONARY_EDITOR_FRAME_SECTION, DICTIONARY_EDITOR_FRAME_Y_OPTION, y)

    def get_dictionary_editor_frame_y(self):
        return self._get_int(DICTIONARY_EDITOR_FRAME_SECTION,
                             DICTIONARY_EDITOR_FRAME_Y_OPTION,
                             DEFAULT_DICTIONARY_EDITOR_FRAME_Y)
    
    def set_serial_config_frame_x(self, x):
        self._set(SERIAL_CONFIG_FRAME_SECTION, SERIAL_CONFIG_FRAME_X_OPTION, x)
    
    def get_serial_config_frame_x(self):
        return self._get_int(SERIAL_CONFIG_FRAME_SECTION, 
                             SERIAL_CONFIG_FRAME_X_OPTION,
                             DEFAULT_SERIAL_CONFIG_FRAME_X)

    def set_serial_config_frame_y(self, y):
        self._set(SERIAL_CONFIG_FRAME_SECTION, SERIAL_CONFIG_FRAME_Y_OPTION, y)

    def get_serial_config_frame_y(self):
        return self._get_int(SERIAL_CONFIG_FRAME_SECTION, 
                             SERIAL_CONFIG_FRAME_Y_OPTION,
                             DEFAULT_SERIAL_CONFIG_FRAME_Y)

    def set_keyboard_config_frame_x(self, x):
        self._set(KEYBOARD_CONFIG_FRAME_SECTION, KEYBOARD_CONFIG_FRAME_X_OPTION, 
                  x)
    
    def get_keyboard_config_frame_x(self):
        return self._get_int(KEYBOARD_CONFIG_FRAME_SECTION, 
                             KEYBOARD_CONFIG_FRAME_X_OPTION,
                             DEFAULT_KEYBOARD_CONFIG_FRAME_X)

    def set_keyboard_config_frame_y(self, y):
        self._set(KEYBOARD_CONFIG_FRAME_SECTION, KEYBOARD_CONFIG_FRAME_Y_OPTION, 
                  y)

    def get_keyboard_config_frame_y(self):
        return self._get_int(KEYBOARD_CONFIG_FRAME_SECTION, 
                             KEYBOARD_CONFIG_FRAME_Y_OPTION,
                             DEFAULT_KEYBOARD_CONFIG_FRAME_Y)

    def _set(self, section, option, value):
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, option, str(value))

    def _get(self, section, option, default):
        if self._config.has_option(section, option):
            return self._config.get(section, option)
        return default

    def _get_bool(self, section, option, default):
        try:
            if self._config.has_option(section, option):
                return self._config.getboolean(section, option)
        except ValueError:
            pass
        return default

    def _get_int(self, section, option, default):
        try:
            if self._config.has_option(section, option):
                return self._config.getint(section, option)
        except ValueError:
            pass
        return default
        

def _dict_entry_key(s):
    try:
        return int(s[len(DICTIONARY_FILE_OPTION):])
    except ValueError:
        return -1
