# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

import json
import unittest

DICT_PATH='plover/assets/dict.json'

DICT_PATH_NUMBER_DECIMAL='plover/assets/dict_number_decimal.json'
DICT_PATH_NUMBER_FRACTIONS='plover/assets/dict_number_fractions.json'
DICT_PATH_NUMBER_INTEGERS='plover/assets/dict_number_integers.json'
DICT_PATH_NUMBER_MONEY='plover/assets/dict_number_money.json'
DICT_PATH_NUMBER_PERCENT='plover/assets/dict_number_percent.json'
DICT_PATH_NUMBER_S='plover/assets/dict_number_s.json'
DICT_PATH_NUMBER_TH='plover/assets/dict_number_th.json'
DICT_PATH_NUMBER_TIME='plover/assets/dict_number_time.json'
DICT_PATH_NUMBER_X='plover/assets/dict_number_x.json'
DICT_PATH_PREFIX='plover/assets/dict_prefix.json'
DICT_PATH_PREFIX_MISSTROKE='plover/assets/dict_prefix_misstroke.json'
DICT_PATH_SUFFIX='plover/assets/dict_suffix.json'
DICT_PATH_SUFFIX_MISSTROKE='plover/assets/dict_suffix_misstroke.json'

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
    
    def test_no_duplicates_unsorted_file(self):
            
        d = json.load(open(DICT_PATH), object_pairs_hook=read_key_pairs)
        
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

    def test_no_duplicates_categorized_files(self):

        d = json.load(open(DICT_PATH_NUMBER_DECIMAL), object_pairs_hook=read_key_pairs)
        d.update(json.load(open(DICT_PATH_NUMBER_FRACTIONS), object_pairs_hook=read_key_pairs))
        d.update(json.load(open(DICT_PATH_NUMBER_INTEGERS), object_pairs_hook=read_key_pairs))
        d.update(json.load(open(DICT_PATH_NUMBER_MONEY), object_pairs_hook=read_key_pairs))
        d.update(json.load(open(DICT_PATH_NUMBER_PERCENT), object_pairs_hook=read_key_pairs))
        d.update(json.load(open(DICT_PATH_NUMBER_S), object_pairs_hook=read_key_pairs))
        d.update(json.load(open(DICT_PATH_NUMBER_TH), object_pairs_hook=read_key_pairs))
        d.update(json.load(open(DICT_PATH_NUMBER_TIME), object_pairs_hook=read_key_pairs))
        d.update(json.load(open(DICT_PATH_NUMBER_X), object_pairs_hook=read_key_pairs))
        d.update(json.load(open(DICT_PATH_PREFIX), object_pairs_hook=read_key_pairs))
        d.update(json.load(open(DICT_PATH_PREFIX_MISSTROKE), object_pairs_hook=read_key_pairs))
        d.update(json.load(open(DICT_PATH_SUFFIX), object_pairs_hook=read_key_pairs))
        d.update(json.load(open(DICT_PATH_SUFFIX_MISSTROKE), object_pairs_hook=read_key_pairs))

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
