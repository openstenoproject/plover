# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Configuration management."""

from collections import namedtuple
from io import BytesIO
import codecs
import configparser
import json
import os

from plover.exception import InvalidConfigurationError
from plover.machine.keymap import Keymap
from plover.registry import registry
from plover.oslayer.config import ASSETS_DIR, CONFIG_DIR
from plover.misc import expand_path, shorten_path
from plover import log


SPINNER_FILE = os.path.join(ASSETS_DIR, 'spinner.gif')

# Config path.
CONFIG_FILE = os.path.join(CONFIG_DIR, 'plover.cfg')

# General configuration sections, options and defaults.
MACHINE_CONFIG_SECTION = 'Machine Configuration'
MACHINE_TYPE_OPTION = 'machine_type'
DEFAULT_MACHINE_TYPE = 'Keyboard'
MACHINE_AUTO_START_OPTION = 'auto_start'
DEFAULT_MACHINE_AUTO_START = False

LEGACY_DICTIONARY_CONFIG_SECTION = 'Dictionary Configuration'
LEGACY_DICTIONARY_FILE_OPTION = 'dictionary_file'

LOGGING_CONFIG_SECTION = 'Logging Configuration'
LOG_FILE_OPTION = 'log_file'
DEFAULT_LOG_FILE = 'strokes.log'
ENABLE_STROKE_LOGGING_OPTION = 'enable_stroke_logging'
DEFAULT_ENABLE_STROKE_LOGGING = False
ENABLE_TRANSLATION_LOGGING_OPTION = 'enable_translation_logging'
DEFAULT_ENABLE_TRANSLATION_LOGGING = False

STARTUP_SECTION = 'Startup'
START_MINIMIZED_OPTION = 'Start Minimized'
DEFAULT_START_MINIMIZED = False

STROKE_DISPLAY_SECTION = 'Stroke Display'
STROKE_DISPLAY_SHOW_OPTION = 'show'
DEFAULT_STROKE_DISPLAY_SHOW = False

SUGGESTIONS_DISPLAY_SECTION = 'Suggestions Display'
SUGGESTIONS_DISPLAY_SHOW_OPTION = 'show'
DEFAULT_SUGGESTIONS_DISPLAY_SHOW = False

GUI_SECTION = 'GUI'
CLASSIC_DICTIONARIES_DISPLAY_ORDER_OPTION = 'classic_dictionaries_display_order'
DEFAULT_CLASSIC_DICTIONARIES_DISPLAY_ORDER = False

OUTPUT_CONFIG_SECTION = 'Output Configuration'
OUTPUT_CONFIG_SPACE_PLACEMENT_OPTION = 'space_placement'
DEFAULT_OUTPUT_CONFIG_SPACE_PLACEMENT = 'Before Output'
OUTPUT_CONFIG_UNDO_LEVELS = 'undo_levels'
DEFAULT_OUTPUT_CONFIG_UNDO_LEVELS = 100
MINIMUM_OUTPUT_CONFIG_UNDO_LEVELS = 1
OUTPUT_CONFIG_START_CAPITALIZED = 'start_capitalized'
DEFAULT_OUTPUT_CONFIG_START_CAPITALIZED = False
OUTPUT_CONFIG_START_ATTACHED = 'start_attached'
DEFAULT_OUTPUT_CONFIG_START_ATTACHED = False

TRANSLATION_FRAME_SECTION = 'Translation Frame'
TRANSLATION_FRAME_OPACITY_OPTION = 'opacity'
DEFAULT_TRANSLATION_FRAME_OPACITY = 100

BASE_SYSTEM_SECTION = 'System'
SYSTEM_NAME_OPTION = 'name'
DEFAULT_SYSTEM_NAME = 'English Stenotype'

SYSTEM_CONFIG_SECTION = 'System: %s'
SYSTEM_KEYMAP_OPTION = 'keymap[%s]'
SYSTEM_DICTIONARIES_OPTION = 'dictionaries'

PLUGINS_CONFIG_SECTION = 'Plugins'
ENABLED_EXTENSIONS_OPTION = 'enabled_extensions'

# Logging constants.
LOG_EXTENSION = '.log'


MIN_FRAME_OPACITY = 0
MAX_FRAME_OPACITY = 100


def raise_if_invalid_opacity(opacity):
    """
    Raises ValueError if opacity is out of range defined by
    [MIN_FRAME_OPACITY, MAX_FRAME_OPACITY].
    """
    if not (MIN_FRAME_OPACITY <= opacity <= MAX_FRAME_OPACITY):
        message = "opacity %u out of range [%u, %u]" \
            % (opacity, MIN_FRAME_OPACITY, MAX_FRAME_OPACITY)
        raise ValueError(message)


class DictionaryConfig(namedtuple('DictionaryConfig', 'path enabled')):

    def __new__(cls, path, enabled=True):
        return super(DictionaryConfig, cls).__new__(cls, expand_path(path), enabled)

    @property
    def short_path(self):
        return shorten_path(self.path)

    def to_dict(self):
        # Note: do not use _asdict because of
        # https://bugs.python.org/issue24931
        return {
            'path': self.short_path,
            'enabled': self.enabled,
        }

    def replace(self, **kwargs):
        return self._replace(**kwargs)

    @staticmethod
    def from_dict(d):
        return DictionaryConfig(**d)


# TODO: Unit test this class

class Config(object):

    def __init__(self):
        self._config = configparser.RawConfigParser()
        # A convenient place for other code to store a file name.
        self.target_file = None

    def load(self, fp):
        self._config = configparser.RawConfigParser()
        reader = codecs.getreader('utf8')(fp)
        try:
            self._config.read_file(reader)
        except configparser.Error as e:
            raise InvalidConfigurationError(str(e))

    def clear(self):
        self._config = configparser.RawConfigParser()

    def save(self, fp):
        writer = codecs.getwriter('utf8')(fp)
        self._config.write(writer)

    def clone(self):
        f = BytesIO()
        self.save(f)
        c = Config()
        f.seek(0, 0)
        c.load(f)
        return c

    def set_machine_type(self, machine_type):
        self._set(MACHINE_CONFIG_SECTION, MACHINE_TYPE_OPTION,
                         machine_type)

    def get_machine_type(self):
        machine_type = self._get(MACHINE_CONFIG_SECTION,
                                 MACHINE_TYPE_OPTION,
                                 None)
        if machine_type is not None:
            try:
                machine_type = registry.get_plugin('machine', machine_type).name
            except:
                log.error("invalid machine type: %s",
                          machine_type, exc_info=True)
                self.set_machine_type(DEFAULT_MACHINE_TYPE)
                machine_type = None
        if machine_type is None:
            machine_type = DEFAULT_MACHINE_TYPE
        return machine_type

    def set_machine_specific_options(self, options, machine_type=None):
        if machine_type is None:
            machine_type = self.get_machine_type()
        self._update(machine_type, sorted(options.items()))

    def get_machine_specific_options(self, machine_type=None):
        if machine_type is None:
            machine_type = self.get_machine_type()
        def convert(p, v):
            try:
                return p[1](v)
            except ValueError:
                return p[0]
        machine_class = registry.get_plugin('machine', machine_type).obj
        info = machine_class.get_option_info()
        defaults = {k: v[0] for k, v in info.items()}
        if self._config.has_section(machine_type):
            options = {o: self._config.get(machine_type, o)
                       for o in self._config.options(machine_type)
                       if o in info}
            options = {k: convert(info[k], v) for k, v in options.items()}
            defaults.update(options)
        return defaults

    def set_dictionaries(self, dictionaries):
        system_name = self.get_system_name()
        section = SYSTEM_CONFIG_SECTION % system_name
        option = SYSTEM_DICTIONARIES_OPTION
        if dictionaries is None:
            self._config.remove_option(section, option)
        else:
            self._set(section, option, json.dumps([
                d.to_dict() for d in dictionaries
            ], sort_keys=True))

    def get_dictionaries(self):
        system_name = self.get_system_name()
        try:
            system = registry.get_plugin('system', system_name).obj
        except:
            log.error("invalid system name: %s", system_name, exc_info=True)
            return []
        section = SYSTEM_CONFIG_SECTION % system_name
        option = SYSTEM_DICTIONARIES_OPTION
        dictionaries = self._get(section, option, None)
        if dictionaries is None:
            dictionaries = self._legacy_get_dictionary_file_names()
            if dictionaries is None:
                dictionaries = [DictionaryConfig(path)
                                for path in system.DEFAULT_DICTIONARIES]
            return dictionaries
        try:
            return [DictionaryConfig.from_dict(d)
                    for d in json.loads(dictionaries)]
        except:
            log.error("invalid system dictionaries, resetting to default", exc_info=True)
            self.set_dictionaries(None)
            return self.get_dictionaries()

    def _legacy_get_dictionary_file_names(self):
        if not self._config.has_section(LEGACY_DICTIONARY_CONFIG_SECTION):
            return None
        def _dict_entry_key(s):
            try:
                return int(s[len(LEGACY_DICTIONARY_FILE_OPTION):])
            except ValueError:
                return -1
        options = [x for x in self._config.options(LEGACY_DICTIONARY_CONFIG_SECTION)
                   if x.startswith(LEGACY_DICTIONARY_FILE_OPTION)]
        options.sort(key=_dict_entry_key)
        filenames = [self._config.get(LEGACY_DICTIONARY_CONFIG_SECTION, o)
                     for o in options]
        # Update to new format.
        self._config.remove_section(LEGACY_DICTIONARY_CONFIG_SECTION)
        if not filenames:
            return None
        dictionaries = [DictionaryConfig(path) for path in reversed(filenames)]
        self.set_dictionaries(dictionaries)
        return dictionaries

    def set_log_file_name(self, filename):
        filename = shorten_path(filename)
        self._set(LOGGING_CONFIG_SECTION, LOG_FILE_OPTION, filename)

    def get_log_file_name(self):
        filename = self._get(LOGGING_CONFIG_SECTION, LOG_FILE_OPTION,
                             DEFAULT_LOG_FILE)
        return expand_path(filename)

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

    def set_start_minimized(self, b):
        self._set(STARTUP_SECTION, START_MINIMIZED_OPTION, b)

    def get_start_minimized(self):
        return self._get_bool(STARTUP_SECTION, START_MINIMIZED_OPTION,
                              DEFAULT_START_MINIMIZED)

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

    def get_undo_levels(self):
        undo_levels = self._get_int(OUTPUT_CONFIG_SECTION, OUTPUT_CONFIG_UNDO_LEVELS,
                                    DEFAULT_OUTPUT_CONFIG_UNDO_LEVELS)
        if undo_levels < MINIMUM_OUTPUT_CONFIG_UNDO_LEVELS:
            log.error(
                "Undo limit %d is below minimum %d, using %d",
                undo_levels,
                MINIMUM_OUTPUT_CONFIG_UNDO_LEVELS,
                DEFAULT_OUTPUT_CONFIG_UNDO_LEVELS
            )
            undo_levels = DEFAULT_OUTPUT_CONFIG_UNDO_LEVELS
        return undo_levels

    def set_undo_levels(self, levels):
        assert levels >= MINIMUM_OUTPUT_CONFIG_UNDO_LEVELS
        self._set(OUTPUT_CONFIG_SECTION, OUTPUT_CONFIG_UNDO_LEVELS, levels)

    def get_start_capitalized(self):
        return self._get_bool(OUTPUT_CONFIG_SECTION, OUTPUT_CONFIG_START_CAPITALIZED,
                              DEFAULT_OUTPUT_CONFIG_START_CAPITALIZED)

    def set_start_capitalized(self, b):
        self._set(OUTPUT_CONFIG_SECTION, OUTPUT_CONFIG_START_CAPITALIZED, b)

    def get_start_attached(self):
        return self._get_bool(OUTPUT_CONFIG_SECTION, OUTPUT_CONFIG_START_ATTACHED,
                              DEFAULT_OUTPUT_CONFIG_START_ATTACHED)

    def set_start_attached(self, b):
        self._set(OUTPUT_CONFIG_SECTION, OUTPUT_CONFIG_START_ATTACHED, b)

    def set_translation_frame_opacity(self, opacity):
        raise_if_invalid_opacity(opacity)
        self._set(TRANSLATION_FRAME_SECTION,
                  TRANSLATION_FRAME_OPACITY_OPTION,
                  opacity)

    def get_translation_frame_opacity(self):
        opacity = self._get_int(TRANSLATION_FRAME_SECTION,
                                TRANSLATION_FRAME_OPACITY_OPTION,
                                DEFAULT_TRANSLATION_FRAME_OPACITY)
        try:
            raise_if_invalid_opacity(opacity)
        except ValueError as e:
            log.error("translation %s, reset to %u",
                      e, DEFAULT_TRANSLATION_FRAME_OPACITY)
            opacity = DEFAULT_TRANSLATION_FRAME_OPACITY
        return opacity

    def set_classic_dictionaries_display_order(self, b):
        self._set(GUI_SECTION, CLASSIC_DICTIONARIES_DISPLAY_ORDER_OPTION, bool(b))

    def get_classic_dictionaries_display_order(self):
        return self._get_bool(GUI_SECTION,
                              CLASSIC_DICTIONARIES_DISPLAY_ORDER_OPTION,
                              DEFAULT_CLASSIC_DICTIONARIES_DISPLAY_ORDER)

    def set_system_name(self, system_name):
        self._set(BASE_SYSTEM_SECTION, SYSTEM_NAME_OPTION, system_name)

    def get_system_name(self):
        system_name = self._get(BASE_SYSTEM_SECTION,
                                SYSTEM_NAME_OPTION,
                                None)
        if system_name is not None:
            try:
                system_name = registry.get_plugin('system', system_name).name
            except:
                log.error("invalid system name: %s",
                          system_name, exc_info=True)
                self.set_system_name(DEFAULT_SYSTEM_NAME)
                system_name = None
        if system_name is None:
            system_name = DEFAULT_SYSTEM_NAME
        return system_name

    def set_system_keymap(self, keymap, machine_type=None, system_name=None):
        if machine_type is None:
            machine_type = self.get_machine_type()
        if system_name is None:
            system_name = self.get_system_name()
        section = SYSTEM_CONFIG_SECTION % system_name
        option = SYSTEM_KEYMAP_OPTION % machine_type
        if keymap is None:
            self._config.remove_option(section, option)
        else:
            self._set(section, option, json.dumps(sorted(dict(keymap).items())))

    def get_system_keymap(self, machine_type=None, system_name=None):
        if machine_type is None:
            machine_type = self.get_machine_type()
        try:
            machine_class = registry.get_plugin('machine', machine_type).obj
        except:
            log.error("invalid machine type: %s", machine_type, exc_info=True)
            return None
        if system_name is None:
            system_name = self.get_system_name()
        try:
            system = registry.get_plugin('system', system_name).obj
        except:
            log.error("invalid system name: %s", system_name, exc_info=True)
            return None
        section = SYSTEM_CONFIG_SECTION % system_name
        option = SYSTEM_KEYMAP_OPTION % machine_type
        mappings = self._get(section, option, None)
        if mappings is None:
            # No user mappings, use system default.
            mappings = system.KEYMAPS.get(machine_type)
        else:
            try:
                mappings = dict(json.loads(mappings))
            except ValueError:
                log.error("invalid machine keymap, resetting to default",
                          exc_info=True)
                self.set_system_keymap(None, machine_type)
                mappings = system.KEYMAPS.get(machine_type)
        if mappings is None:
            if machine_class.KEYMAP_MACHINE_TYPE is not None:
                # Try fallback.
                return self.get_system_keymap(
                    machine_type=machine_class.KEYMAP_MACHINE_TYPE,
                    system_name=system_name
                )
            # No fallback...
            mappings = {}
        keymap = Keymap(machine_class.get_keys(), system.KEYS + machine_class.get_actions())
        keymap.set_mappings(mappings)
        return keymap

    def set_enabled_extensions(self, extensions):
        if extensions is None:
            self._config.remove_option(PLUGINS_CONFIG_SECTION,
                                       ENABLED_EXTENSIONS_OPTION)
        else:
            self._set(PLUGINS_CONFIG_SECTION,
                      ENABLED_EXTENSIONS_OPTION,
                      json.dumps(sorted(list(set(extensions)))))

    def get_enabled_extensions(self):
        extensions = ()
        value = self._get(PLUGINS_CONFIG_SECTION,
                          ENABLED_EXTENSIONS_OPTION,
                          None)
        if value is not None:
            try:
                extensions = set(json.loads(value))
            except ValueError:
                log.error("invalid enabled extensions set, resetting to default",
                          exc_info=True)
                self.set_enabled_extensions(None)
        return set(extensions)

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

    def _update(self, section, options):
        old_options = set()
        if self._config.has_section(section):
            old_options.update(self._config.options(section))
        for opt, val in options:
            old_options.discard(opt)
            self._set(section, opt, val)
        for opt in old_options:
            self._config.remove_option(section, opt)


    # Note: order matters, e.g. machine_type comes before
    # machine_specific_options and system_keymap because
    # the laters depend on the former.
    _OPTIONS = '''
    auto_start
    space_placement
    start_attached
    start_capitalized
    start_minimized
    undo_levels

    dictionaries

    enabled_extensions

    enable_stroke_logging
    enable_translation_logging
    log_file_name

    show_stroke_display
    show_suggestions_display
    translation_frame_opacity
    classic_dictionaries_display_order

    system_name
    machine_type
    machine_specific_options
    system_keymap
    '''.split()

    def as_dict(self):
        d = {}
        for option in self._OPTIONS:
            assert hasattr(self, 'set_%s' % option)
            getter = getattr(self, 'get_%s' % option)
            d[option] = getter()
        return d

    def update(self, **kwargs):
        for option in self._OPTIONS:
            if option not in kwargs:
                continue
            setter = getattr(self, 'set_%s' % option)
            setter(kwargs[option])
