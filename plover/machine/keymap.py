import json
from collections import defaultdict, OrderedDict

# Python 2/3 compatibility.
from six import string_types

from plover import log


class Keymap(object):

    def __init__(self, keys, actions):
        # List of supported actions.
        self._actions = OrderedDict((action, n)
                                    for n, action
                                    in enumerate(actions))
        # List of supported keys.
        self._keys = OrderedDict((key, n)
                                 for n, key
                                 in enumerate(keys))
        # action -> keys
        self._mappings = {}
        # key -> action
        self._bindings = {}

    def set_bindings(self, bindings):
        # Set from:
        # { key1: action1, key2: action1, ... keyn: actionn }
        mappings = defaultdict(list)
        for key, action in dict(bindings).items():
            mappings[action].append(key)
        self.set_mappings(mappings)

    def set_mappings(self, mappings):
        # When setting from a string, assume a list of mappings:
        # [[action1, [key1, key2]], [action2, [key3]], ...]
        if isinstance(mappings, string_types):
            mappings = json.loads(mappings)
        mappings = dict(mappings)
        # Set from:
        # { action1: [key1, key2], ... actionn: [keyn] }
        self._mappings = OrderedDict()
        self._bindings = {}
        bound_keys = defaultdict(list)
        errors = []
        for action in self._actions:
            key_list = mappings.get(action)
            if not key_list:
                # Not an issue if 'no-op' is not mapped...
                if action != 'no-op':
                    errors.append('action %s is not bound' % action)
                # Add dummy mapping for each missing action
                # so it's shown in the configurator.
                self._mappings[action] = ()
                continue
            if isinstance(key_list, string_types):
                key_list = (key_list,)
            self._mappings[action] = tuple(sorted(key_list, key=self._keys.get))
            for key in key_list:
                if key not in self._keys:
                    errors.append('invalid key %s bound to action %s' % (key, action))
                    continue
                bound_keys[key].append(action)
                self._bindings[key] = action
        for action in (set(mappings) - set(self._actions)):
            key_list = mappings.get(action)
            if isinstance(key_list, string_types):
                key_list = (key_list,)
            errors.append('invalid action %s mapped to key(s) %s' % (action, ' '.join(key_list)))
        for key, action_list in bound_keys.items():
            if len(action_list) > 1:
                errors.append('key %s is bound multiple times: %s' % (key, str(action_list)))
        if len(errors) > 0:
            log.warning('Keymap is invalid, behavior undefined:\n\n- ' + '\n- '.join(errors))

    def get_bindings(self):
        return self._bindings

    def get_mappings(self):
        return self._mappings

    def get_action(self, key, default=None):
        return self._bindings.get(key, default)

    def keys_to_actions(self, key_list):
        action_list = []
        for key in key_list:
            assert key in self._keys, "'%s' not in %s" % (key, self._keys)
            action = self._bindings[key]
            if 'no-op' != action:
                action_list.append(action)
        return action_list

    def __str__(self):
        # Use the more compact list of mappings format:
        # [[action1, [key1, key2]], [action2, [key3]], ...]
        return json.dumps(self._mappings.items())

