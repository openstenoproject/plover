import json
from collections import OrderedDict

class Keymap():

    DEFAULT = [
        ["S-", ["a","q"]],
        ["T-", ["w"]],
        ["K-", ["s"]],
        ["P-", ["e"]],
        ["W-", ["d"]],
        ["H-", ["r"]],
        ["R-", ["f"]],
        ["A-", ["c"]],
        ["O-", ["v"]],
        ["*" , ["t","g","y","h"]],
        ["-E", ["n"]],
        ["-U", ["m"]],
        ["-F", ["u"]],
        ["-R", ["j"]],
        ["-P", ["i"]],
        ["-B", ["k"]],
        ["-L", ["o"]],
        ["-G", ["l"]],
        ["-T", ["p"]],
        ["-S", [";"]],
        ["-D", ["["]],
        ["-Z", ["'"]],
        ["#" , ["1","2","3","4","5","6","7","8","9","0","-","="]],
        ["no-op", ["z","x","b",",",".","/","\\"]],
    ]

    def __init__(self, assignments):
        assignments = dict(assignments)
        self.keymap = OrderedDict()
        # Keep only valid entries, and add missing entries.
        for action, keys in Keymap.DEFAULT:
            keys = assignments.get(action, ())
            self.keymap[action] = keys

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
        return Keymap(Keymap.DEFAULT)
