import json
from collections import OrderedDict
from plover import log
from plover import system

class Keymap():

    def __init__(self, assignments):
        assignments = dict(assignments)
        self.keymap = OrderedDict()
        bound_keys = {}
        # Keep only valid entries, and add missing entries.
        for action, _ in system.KEYBOARD_KEYMAP:
            keylist = assignments.get(action, ())
            for key in keylist:
                if key in bound_keys:
                    bound_keys[key].append(action)
                else:
                    bound_keys[key] = [action]
            self.keymap[action] = keylist
        errors = []
        for key, action_list in bound_keys.items():
            if len(action_list) > 1:
                errors.append('key %s is bound multiple times: %s' % (key, str(action_list)))
        if len(errors) > 0:
            log.warning('Keymap is invalid, behavior undefined:\n\n- ' + '\n- '.join(errors))

    def get(self):
        return self.keymap

    def __str__(self):
        return json.dumps(self.keymap.items())

    def to_dict(self):
        """Return a dictionary from keys to actions."""
        result = {}
        for action, keys in self.keymap.items():
            for k in keys:
                result[k] = action
        return result

    @staticmethod
    def from_string(string):
        assignments = json.loads(string)
        return Keymap(assignments)

    @staticmethod
    def from_rows(rows):
        """Convert a nested list of strings (e.g. from a ListCtrl) to a keymap."""
        assignments = []
        for row in rows:
            action = row[0]
            keylist = row[1].strip().split()
            assignments.append((action, keylist))
        return Keymap(assignments)

    @staticmethod
    def default():
        return Keymap(system.KEYBOARD_KEYMAP)

