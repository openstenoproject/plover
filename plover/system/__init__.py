
from collections.abc import Sequence
from io import open
import os
import re

from plover.oslayer.config import CONFIG_DIR, ASSETS_DIR
from plover.registry import registry


def _load_wordlist(filename):
    if filename is None:
        return {}
    path = None
    for dir in (CONFIG_DIR, ASSETS_DIR):
        path = os.path.realpath(os.path.join(dir, filename))
        if os.path.exists(path):
            break
    words = {}
    with open(path, encoding='utf-8') as f:
        pairs = [word.strip().rsplit(' ', 1) for word in f]
        pairs.sort(reverse=True, key=lambda x: int(x[1]))
        words = {p[0]: int(p[1]) for p in pairs}
    return words

def _key_order(keys, numbers):
    key_order = {}
    for order, key in enumerate(keys):
        key_order[key] = order
        number_key = numbers.get(key)
        if number_key is not None:
            key_order[number_key] = order
    return key_order

def _suffix_keys(keys):
    assert isinstance(keys, Sequence)
    return keys

_EXPORTS = {
    'KEYS'                     : lambda mod: mod.KEYS,
    'KEY_ORDER'                : lambda mod: _key_order(mod.KEYS, mod.NUMBERS),
    'NUMBER_KEY'               : lambda mod: mod.NUMBER_KEY,
    'NUMBERS'                  : lambda mod: dict(mod.NUMBERS),
    'SUFFIX_KEYS'              : lambda mod: _suffix_keys(mod.SUFFIX_KEYS),
    'UNDO_STROKE_STENO'        : lambda mod: mod.UNDO_STROKE_STENO,
    'IMPLICIT_HYPHEN_KEYS'     : lambda mod: set(mod.IMPLICIT_HYPHEN_KEYS),
    'IMPLICIT_HYPHENS'         : lambda mod: {l.replace('-', '')
                                              for l in mod.IMPLICIT_HYPHEN_KEYS},
    'ORTHOGRAPHY_WORDS'        : lambda mod: _load_wordlist(mod.ORTHOGRAPHY_WORDLIST),
    'ORTHOGRAPHY_RULES'        : lambda mod: [(re.compile(pattern, re.I), replacement)
                                              for pattern, replacement in mod.ORTHOGRAPHY_RULES],
    'ORTHOGRAPHY_RULES_ALIASES': lambda mod: dict(mod.ORTHOGRAPHY_RULES_ALIASES),
    'KEYMAPS'                  : lambda mod: mod.KEYMAPS,
    'DICTIONARIES_ROOT'        : lambda mod: mod.DICTIONARIES_ROOT,
    'DEFAULT_DICTIONARIES'     : lambda mod: mod.DEFAULT_DICTIONARIES,
}

def setup(system_name):
    system_symbols = {}
    mod = registry.get_plugin('system', system_name).obj
    for symbol, init in _EXPORTS.items():
        system_symbols[symbol] = init(mod)
    system_symbols['NAME'] = system_name
    globals().update(system_symbols)

NAME = None
