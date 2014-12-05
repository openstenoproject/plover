import json
from collections import OrderedDict

class Keymap():
    def __init__(self, assignments):
        self.keymap = OrderedDict(assignments)
        self.assignments = assignments

    def get(self):
        return self.keymap

    def __str__(self):
        return json.dumps(self.assignments)

    def to_dict(self):
        """Return a dictionary from keys to steno keys."""
        result = {}
        for stenoKey, producers in self.keymap.items():
            for key in producers:
                result[key] = stenoKey
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
            stenoKey = row[0]
            keylist = row[1].strip().split()
            assignments.append([stenoKey, keylist])
        return Keymap(assignments)

    @staticmethod
    def default():
        return Keymap([
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
            ["#" , ["1","2","3","4","5","6","7","8","9","0","-","="]]
        ])
