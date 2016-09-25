
from plover.oslayer.config import CONFIG_DIR, ASSETS_DIR

from io import open
import os
import re


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
        words = {p[0].lower(): int(p[1]) for p in pairs}
    return words

def _key_order(keys, numbers):
    key_order = {}
    for order, key in enumerate(keys):
        key_order[key] = order
        number_key = numbers.get(key)
        if number_key is not None:
            key_order[number_key] = order
    return key_order

_EXPORTS = {
    'KEYS'                     : lambda mod: mod.KEYS,
    'KEY_ORDER'                : lambda mod: _key_order(mod.KEYS, mod.NUMBERS),
    'NUMBER_KEY'               : lambda mod: mod.NUMBER_KEY,
    'NUMBERS'                  : lambda mod: dict(mod.NUMBERS),
    'SUFFIX_KEYS'              : lambda mod: set(mod.SUFFIX_KEYS),
    'UNDO_STROKE_STENO'        : lambda mod: mod.UNDO_STROKE_STENO,
    'IMPLICIT_HYPHEN_KEYS'     : lambda mod: set(mod.IMPLICIT_HYPHEN_KEYS),
    'IMPLICIT_HYPHENS'         : lambda mod: set(l.replace('-', '')
                                                 for l in mod.IMPLICIT_HYPHEN_KEYS),
    'ORTHOGRAPHY_WORDS'        : lambda mod: _load_wordlist(mod.ORTHOGRAPHY_WORDLIST),
    'ORTHOGRAPHY_RULES'        : lambda mod: [(re.compile(pattern, re.I), replacement)
                                              for pattern, replacement in mod.ORTHOGRAPHY_RULES],
    'ORTHOGRAPHY_RULES_ALIASES': lambda mod: dict(mod.ORTHOGRAPHY_RULES_ALIASES),
    'KEYMAPS'                  : lambda mod: mod.KEYMAPS,
}

def setup():
    from plover.system import english_stenotype as mod
    globs = globals()
    for symbol, init in _EXPORTS.items():
        globs[symbol] = init(mod)
    globs['NAME'] = 'English Stenotype'


# Setup default system.
setup()

