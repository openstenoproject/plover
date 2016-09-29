
from collections import namedtuple
from functools import wraps
import threading

# Python 2/3 compatibility.
from six.moves.queue import Queue

from plover import log
from plover.config import copy_default_dictionaries
from plover.dictionary.loading_manager import DictionaryLoadingManager
from plover.exception import InvalidConfigurationError
from plover.formatting import Formatter
from plover.machine.registry import machine_registry, NoSuchMachineException
from plover.steno import Stroke
from plover.suggestions import Suggestions
from plover.translation import Translator


StartingStrokeState = namedtuple('StartingStrokeState', 'attach capitalize')

MachineParams = namedtuple('MachineParams', 'type options keymap')


def with_lock(func):
    # To keep __doc__/__name__ attributes of the initial function.
    @wraps(func)
    def _with_lock(self, *args, **kwargs):
        with self:
            return func(self, *args, **kwargs)
    return _with_lock


class StenoEngine(object):

    HOOKS = '''
    stroked
    translated
    machine_state_changed
    output_changed
    config_changed
    send_string
    send_backspaces
    send_key_combination
    add_translation
    focus
    configure
    lookup
    quit
    '''.split()

    def __init__(self, config, keyboard_emulation):
        self._config = config
        self._is_running = False
        self._queue = Queue()
        self._lock = threading.RLock()
        self._machine = None
        self._machine_state = None
        self._machine_params = MachineParams(None, None, None)
        self._formatter = Formatter()
        self._formatter.set_output(self)
        self._formatter.add_listener(self._on_translated)
        self._translator = Translator()
        self._translator.add_listener(log.translation)
        self._translator.add_listener(self._formatter.format)
        self._dictionaries = self._translator.get_dictionary()
        self._dictionaries_manager = DictionaryLoadingManager()
        self._running_state = self._translator.get_state()
        self._suggestions = Suggestions(self._dictionaries)
        self._keyboard_emulation = keyboard_emulation
        self._hooks = { hook: [] for hook in self.HOOKS }

    def __enter__(self):
        self._lock.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._lock.__exit__(exc_type, exc_value, traceback)

    def _in_engine_thread(self):
        raise NotImplementedError()

    def _same_thread_hook(self, func, *args, **kwargs):
        if self._in_engine_thread():
            func(*args, **kwargs)
        else:
            self._queue.put((func, args, kwargs))

    def run(self):
        while True:
            func, args, kwargs = self._queue.get()
            try:
                with self._lock:
                    if func(*args, **kwargs):
                        break
            except Exception:
                log.error('engine %s failed', func.__name__[1:], exc_info=True)

    def _stop(self):
        if self._machine is not None:
            self._machine.stop_capture()
            self._machine = None

    def _start(self):
        self._set_output(self._config.get_auto_start())
        copy_default_dictionaries(self._config)
        self._update(full=True)

    def _update(self, config_update=None, full=False, reset_machine=False):
        original_config = self._config.as_dict()
        # Update configuration.
        if config_update is not None:
            self._config.update(**config_update)
            config = self._config.as_dict()
        else:
            config = original_config
        # Create configuration update.
        if full:
            config_update = config
        else:
            config_update = {
                option: value
                for option, value in config.items()
                if value != original_config[option]
            }
            if 'machine_type' in config_update:
                for opt in (
                    'machine_specific_options',
                    'system_keymap',
                ):
                    config_update[opt] = config[opt]
        # Update logging.
        log.set_stroke_filename(config['log_file_name'])
        log.enable_stroke_logging(config['enable_stroke_logging'])
        log.enable_translation_logging(config['enable_translation_logging'])
        # Update output.
        self._formatter.set_space_placement(config['space_placement'])
        self._formatter.start_attached = config['start_attached']
        self._formatter.start_capitalized = config['start_capitalized']
        self._translator.set_min_undo_length(config['undo_levels'])
        # Update machine.
        update_keymap = False
        start_machine = False
        machine_params = MachineParams(config['machine_type'],
                                       config['machine_specific_options'],
                                       config['system_keymap'])
        if reset_machine or machine_params != self._machine_params:
            if self._machine is not None:
                self._machine.stop_capture()
                self._machine = None
            machine_type = config['machine_type']
            machine_options = config['machine_specific_options']
            try:
                machine_class = machine_registry.get(machine_type)
            except NoSuchMachineException as e:
                raise InvalidConfigurationError(str(e))
            self._machine = machine_class(machine_options)
            self._machine.set_suppression(self._is_running)
            self._machine.add_state_callback(self._machine_state_callback)
            self._machine.add_stroke_callback(self._machine_stroke_callback)
            self._machine_params = machine_params
            update_keymap = True
            start_machine = True
        elif self._machine is not None:
            update_keymap = 'system_keymap' in config_update
        if update_keymap:
            machine_keymap = config['system_keymap']
            if machine_keymap is not None:
                self._machine.set_keymap(machine_keymap)
        if start_machine:
            self._machine.start_capture()
        # Update dictionaries.
        dictionaries_files = config['dictionary_file_names']
        dictionaries = self._dictionaries_manager.load(dictionaries_files)
        self._dictionaries.set_dicts(dictionaries)
        # Trigger `config_changed` hook.
        if config_update:
            self._trigger_hook('config_changed', config_update)

    def _quit(self):
        self._stop()
        return True

    def _toggle_output(self):
        self._set_output(not self._is_running)

    def _set_output(self, enabled):
        if enabled == self._is_running:
            return
        self._is_running = enabled
        if enabled:
            self._translator.set_state(self._running_state)
        else:
            self._translator.clear_state()
        if self._machine is not None:
            self._machine.set_suppression(enabled)
        self._trigger_hook('output_changed', enabled)

    def _machine_state_callback(self, machine_state):
        self._same_thread_hook(self._on_machine_state_changed, machine_state)

    def _machine_stroke_callback(self, steno_keys):
        self._same_thread_hook(self._on_stroked, steno_keys)

    @with_lock
    def _on_machine_state_changed(self, machine_state):
        assert machine_state is not None
        self._machine_state = machine_state
        machine_type = self._config.get_machine_type()
        self._trigger_hook('machine_state_changed', machine_type, machine_state)

    def _consume_engine_command(self, command):
        # The first commands can be used whether plover has output enabled or not.
        if command == 'RESUME':
            self._set_output(True)
            return True
        elif command == 'TOGGLE':
            self._toggle_output()
            return True
        elif command == 'QUIT':
            self._trigger_hook('quit')
            return True
        if not self._is_running:
            return False
        # These commands can only be run when plover has output enabled.
        if command == 'SUSPEND':
            self._set_output(False)
        elif command == 'CONFIGURE':
            self._trigger_hook('configure')
        elif command == 'FOCUS':
            self._trigger_hook('focus')
        elif command == 'ADD_TRANSLATION':
            self._trigger_hook('add_translation')
        elif command == 'LOOKUP':
            self._trigger_hook('lookup')
        return False

    def _on_stroked(self, steno_keys):
        stroke = Stroke(steno_keys)
        log.stroke(stroke)
        self._translator.translate(stroke)
        self._trigger_hook('stroked', stroke)

    def _on_translated(self, old, new):
        if not self._is_running:
            return
        self._trigger_hook('translated', old, new)

    def send_backspaces(self, b):
        if not self._is_running:
            return
        self._keyboard_emulation.send_backspaces(b)
        self._trigger_hook('send_backspaces', b)

    def send_string(self, s):
        if not self._is_running:
            return
        self._keyboard_emulation.send_string(s)
        self._trigger_hook('send_string', s)

    def send_key_combination(self, c):
        if not self._is_running:
            return
        self._keyboard_emulation.send_key_combination(c)
        self._trigger_hook('send_key_combination', c)

    def send_engine_command(self, command):
        suppress = not self._is_running
        suppress &= self._consume_engine_command(command)
        if suppress:
            self._machine.suppress_last_stroke(self._keyboard_emulation.send_backspaces)

    def toggle_output(self):
        self._same_thread_hook(self._toggle_output)

    def set_output(self, enabled):
        self._same_thread_hook(self._set_output, enabled)

    @property
    @with_lock
    def machine_state(self):
        return self._machine_state

    @property
    @with_lock
    def output(self):
        return self._is_running

    @output.setter
    def output(self, enabled):
        self._same_thread_hook(self._set_output, enabled)

    @property
    @with_lock
    def config(self):
        return self._config.as_dict()

    @config.setter
    @with_lock
    def config(self, update):
        self._same_thread_hook(self._update, config_update=update)

    def reset_machine(self):
        self._same_thread_hook(self._update, reset_machine=True)

    def load_config(self):
        try:
            with open(self._config.target_file, 'rb') as f:
                self._config.load(f)
        except Exception:
            log.error('loading configuration failed, reseting to default', exc_info=True)
            self._config.clear()
            return False
        return True

    def start(self):
        self._same_thread_hook(self._start)

    def quit(self):
        self._same_thread_hook(self._quit)

    @property
    @with_lock
    def machines(self):
        return sorted(machine_registry.get_all_names())

    @with_lock
    def machine_specific_options(self, machine_type):
        return self._config.get_machine_specific_options(machine_type)

    @with_lock
    def system_keymap(self, machine_type):
        return self._config.get_system_keymap(machine_type)

    @with_lock
    def lookup(self, translation):
        return self._dictionaries.lookup(translation)

    @with_lock
    def raw_lookup(self, translation):
        return self._dictionaries.raw_lookup(translation)

    @with_lock
    def reverse_lookup(self, translation):
        matches = self._dictionaries.reverse_lookup(translation)
        return [] if matches is None else matches

    @with_lock
    def casereverse_lookup(self, translation):
        matches = self._dictionaries.casereverse_lookup(translation)
        return set() if matches is None else matches

    @with_lock
    def add_dictionary_filter(self, dictionary_filter):
        self._dictionaries.add_filter(dictionary_filter)

    @with_lock
    def remove_dictionary_filter(self, dictionary_filter):
        self._dictionaries.remove_filter(dictionary_filter)

    @with_lock
    def get_suggestions(self, translation):
        return self._suggestions.find(translation)

    @property
    @with_lock
    def translator_state(self):
        return self._translator.get_state()

    @translator_state.setter
    @with_lock
    def translator_state(self, state):
        self._translator.set_state(state)

    @with_lock
    def clear_translator_state(self, undo=False):
        if undo:
            state = self._translator.get_state()
            self._formatter.format(state.translations, (), None)
        self._translator.clear_state()

    @property
    @with_lock
    def starting_stroke_state(self):
        return StartingStrokeState(self._formatter.start_attached,
                                   self._formatter.start_capitalized)

    @starting_stroke_state.setter
    @with_lock
    def starting_stroke_state(self, state):
        self._formatter.start_attached = state.attach
        self._formatter.start_capitalized = state.capitalize

    @with_lock
    def add_translation(self, strokes, translation, dictionary=None):
        if dictionary is None:
            dictionary = self._dictionaries.dicts[0].get_path()
        self._dictionaries.set(strokes, translation,
                               dictionary=dictionary)
        self._dictionaries.save(path_list=(dictionary,))

    @property
    @with_lock
    def dictionaries(self):
        return self._dictionaries

    # Hooks.

    def _trigger_hook(self, hook, *args, **kwargs):
        for callback in self._hooks[hook]:
            try:
                callback(*args, **kwargs)
            except Exception:
                log.error('hook %r callback %r failed',
                          hook, callback,
                          exc_info=True)

    @with_lock
    def hook_connect(self, hook, callback):
        self._hooks[hook].append(callback)

    @with_lock
    def hook_disconnect(self, hook, callback):
        self._hooks[hook].remove(callback)
