
from plover.oslayer.config import CONFIG_DIR, ASSETS_DIR
from plover import plugins
from plover import log

import imp
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
    with open(path) as f:
        pairs = [word.strip().rsplit(' ', 1) for word in f]
        pairs.sort(reverse=True, key=lambda x: int(x[1]))
        words = {p[0].lower(): int(p[1]) for p in pairs}
    return words

_EXPORTS = {
    'STENO_KEY_ORDER'          : lambda mod: dict((l, n) for n, l in enumerate(mod.KEYS)),
    'STENO_NUMBER_KEY'         : lambda mod: mod.NUMBER_KEY,
    'STENO_KEY_NUMBERS'        : lambda mod: dict(mod.NUMBERS),
    'STENO_KEY_SUFFIXES'       : lambda mod: set(mod.SUFFIX_KEYS),
    'UNDO_STROKE_STENO'        : lambda mod: mod.UNDO_STROKE_STENO,
    'IMPLICIT_HYPHEN_KEYS'     : lambda mod: set(mod.IMPLICIT_HYPHEN_KEYS),
    'IMPLICIT_HYPHENS'         : lambda mod: set(l.replace('-', '')
                                                 for l in mod.IMPLICIT_HYPHEN_KEYS),
    'ORTHOGRAPHY_WORDS'        : lambda mod: _load_wordlist(mod.ORTHOGRAPHY_WORDLIST),
    'ORTHOGRAPHY_RULES'        : lambda mod: [(re.compile(pattern, re.I), replacement)
                                              for pattern, replacement in mod.ORTHOGRAPHY_RULES],
    'ORTHOGRAPHY_RULES_ALIASES': lambda mod: dict(mod.ORTHOGRAPHY_RULES_ALIASES),
    'KEYBOARD_KEYMAP'          : lambda mod: [((action, binding)
                                               if isinstance(binding, (list, tuple))
                                               else (action, (binding,)))
                                              for action, binding in mod.KEYBOARD_KEYMAP],
}

def setup(name):
    systems = plugins.get_systems()
    print 'loading system', name
    mod = systems[name].load()
    globs = globals()
    for symbol, init in _EXPORTS.items():
        globs[symbol] = init(mod)

