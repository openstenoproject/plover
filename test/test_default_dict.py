# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

import io
import json
import unittest
from collections import defaultdict


DICT_NAMES = ['main.json',
              'commands.json',
              'user.json']
DICT_PATH = 'plover/assets/'


class TestCase(unittest.TestCase):

    def test_no_duplicates_categorized_files(self):
        d = defaultdict(list)
        dictionary = None
        def read_key_pairs(pairs):
            for key, value in pairs:
                d[key].append((value, dictionary))
            return d
        for dictionary in map(lambda x: DICT_PATH + x, DICT_NAMES):
            with io.open(dictionary, encoding='utf-8') as fp:
                json.load(fp, object_pairs_hook=read_key_pairs)
        msg_list = []
        has_duplicate = False
        for key, value_list in d.items():
            if len(value_list) > 1:
                has_duplicate = True
                msg_list.append('key: %s\n' % key)
                for value in value_list:
                    msg_list.append('%r in %s\n' % value)
        msg = '\n' + ''.join(msg_list)
        self.assertFalse(has_duplicate, msg)
