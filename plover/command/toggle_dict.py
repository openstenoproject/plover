
import os

from plover.misc import expand_path, shorten_path

from plover.config import DictionaryConfig


def toggle_dictionaries(selections, dictionaries):
    dictionaries = [shorten_path(config.path) for config in dictionaries]
    selections = [os.path.normpath(path) for path in selections]
    toggles = {}
    for selected in selections:
        if not selected[0] in '-+!':
            raise ValueError('Invalid dictionary toggle: "%s".' % selected[0])
        selection_path = selected[1:]
        matches = [
            (len(dictionary_path), n)
            for n, dictionary_path in enumerate(dictionaries)
            if (os.sep + dictionary_path).endswith(os.sep + selection_path)
        ]
        if not matches:
            raise ValueError('No dictionary matching "%s" found.' % selection_path)
        matches.sort()
        dictionary_path = expand_path(dictionaries[matches[0][1]])
        toggles[dictionary_path] = selected[0]
    return toggles

def toggle_dict(engine, cmdline):
    selections = [path.strip() for path in cmdline.split(',')]
    dictionaries = engine.config['dictionaries'][:]
    toggles = toggle_dictionaries(selections, dictionaries)
    for n, config in enumerate(dictionaries):
        t = toggles.get(config.path, None)
        if t == '+':
            dictionaries[n] = DictionaryConfig(config.path, True)
        elif t == '-':
            dictionaries[n] = DictionaryConfig(config.path, False)
        elif t == '!':
            dictionaries[n] = DictionaryConfig(config.path, not config.enabled)

    engine.config = {'dictionaries': dictionaries}
