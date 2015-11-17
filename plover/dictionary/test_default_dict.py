# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

import json
import unittest

DICT_NAMES = ['main.json',
              'commands.json',
              'user.json']
DICT_PATH = 'plover/assets/'


def read_key_pairs(pairs):
    d = {}
    for key, value in pairs:
        holder = []
        if key in d:
            holder = d[key]
        else:
            d[key] = holder
        holder.append(value)
    return d


class TestCase(unittest.TestCase):

    def test_no_duplicates_categorized_files(self):
        d = {}
        for dictionary in map(lambda x: DICT_PATH + x, DICT_NAMES):
            d.update(json.load(open(dictionary),
                               object_pairs_hook=read_key_pairs))

        msg_list = []
        has_duplicate = False
        for key, value_list in d.items():
            if len(value_list) > 1:
                has_duplicate = True
                msg_list.append('key: %s\n' % key)
                for value in value_list:
                    msg_list.append('%s\n' % value)
        msg = ''.join(msg_list)
        self.assertFalse(has_duplicate, msg)
