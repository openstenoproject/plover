
import os

from plover.misc import expand_path, shorten_path


def prioritize_dictionaries(selections, dictionaries):
    dictionaries = [shorten_path(path) for path in dictionaries]
    selections = [os.path.normpath(path) for path in selections]
    for selection_path in selections:
        matches = [
            (len(dictionary_path), n)
            for n, dictionary_path in enumerate(dictionaries)
            if (os.sep + dictionary_path).endswith(os.sep + selection_path)
        ]
        if not matches:
            raise ValueError('No dictionary matching "%s" found.' % selection_path)
        matches.sort()
        dictionary_path = dictionaries.pop(matches[0][1])
        dictionaries.append(dictionary_path)
    return [expand_path(path) for path in dictionaries]

def priority_dict(engine, cmdline):
    selections = [path.strip() for path in cmdline.split(',')]
    old_file_names = engine.config['dictionary_file_names']
    new_file_names = prioritize_dictionaries(selections, old_file_names)
    engine.config = { 'dictionary_file_names': new_file_names }
