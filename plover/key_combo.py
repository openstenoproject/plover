# -*- coding: utf-8 -*-

from collections import OrderedDict
import re


# Mapping of "standard" keynames (derived from X11 keysym names) to Unicode.
KEYNAME_TO_CHAR = {
    # Generated using:
    #
    # from Xlib import XK
    # from plover.oslayer.xkeyboardcontrol import keysym_to_string
    # for kn, ks in sorted({
    #     name[3:].lower(): getattr(XK, name)
    #     for name in sorted(dir(XK))
    #     if name.startswith('XK_')
    # }.items()):
    #     us = keysym_to_string(ks)
    #     if us == kn or not us:
    #         continue
    # print '    %-20r: %8r, # %s' % (kn, us, us)
    'aacute'            :  '\xe1', # á
    'acircumflex'       :  '\xe2', # â
    'acute'             :  '\xb4', # ´
    'adiaeresis'        :  '\xe4', # ä
    'ae'                :  '\xe6', # æ
    'agrave'            :  '\xe0', # à
    'ampersand'         :     '&', # &
    'apostrophe'        :     "'", # '
    'aring'             :  '\xe5', # å
    'asciicircum'       :     '^', # ^
    'asciitilde'        :     '~', # ~
    'asterisk'          :     '*', # *
    'at'                :     '@', # @
    'atilde'            :  '\xe3', # ã
    'backslash'         :    '\\', # \
    'bar'               :     '|', # |
    'braceleft'         :     '{', # {
    'braceright'        :     '}', # }
    'bracketleft'       :     '[', # [
    'bracketright'      :     ']', # ]
    'brokenbar'         :  '\xa6', # ¦
    'ccedilla'          :  '\xe7', # ç
    'cedilla'           :  '\xb8', # ¸
    'cent'              :  '\xa2', # ¢
    'clear'             :  '\x0b', # 
    'colon'             :     ':', # :
    'comma'             :     ',', # ,
    'copyright'         :  '\xa9', # ©
    'currency'          :  '\xa4', # ¤
    'degree'            :  '\xb0', # °
    'diaeresis'         :  '\xa8', # ¨
    'division'          :  '\xf7', # ÷
    'dollar'            :     '$', # $
    'eacute'            :  '\xe9', # é
    'ecircumflex'       :  '\xea', # ê
    'ediaeresis'        :  '\xeb', # ë
    'egrave'            :  '\xe8', # è
    'equal'             :     '=', # =
    'eth'               :  '\xf0', # ð
    'exclam'            :     '!', # !
    'exclamdown'        :  '\xa1', # ¡
    'grave'             :     '`', # `
    'greater'           :     '>', # >
    'guillemotleft'     :  '\xab', # «
    'guillemotright'    :  '\xbb', # »
    'hyphen'            :  '\xad', # ­
    'iacute'            :  '\xed', # í
    'icircumflex'       :  '\xee', # î
    'idiaeresis'        :  '\xef', # ï
    'igrave'            :  '\xec', # ì
    'less'              :     '<', # <
    'macron'            :  '\xaf', # ¯
    'masculine'         :  '\xba', # º
    'minus'             :     '-', # -
    'mu'                :  '\xb5', # µ
    'multiply'          :  '\xd7', # ×
    'nobreakspace'      :  '\xa0', #  
    'notsign'           :  '\xac', # ¬
    'ntilde'            :  '\xf1', # ñ
    'numbersign'        :     '#', # #
    'oacute'            :  '\xf3', # ó
    'ocircumflex'       :  '\xf4', # ô
    'odiaeresis'        :  '\xf6', # ö
    'ograve'            :  '\xf2', # ò
    'onehalf'           :  '\xbd', # ½
    'onequarter'        :  '\xbc', # ¼
    'onesuperior'       :  '\xb9', # ¹
    'ooblique'          :  '\xd8', # Ø
    'ordfeminine'       :  '\xaa', # ª
    'oslash'            :  '\xf8', # ø
    'otilde'            :  '\xf5', # õ
    'paragraph'         :  '\xb6', # ¶
    'parenleft'         :     '(', # (
    'parenright'        :     ')', # )
    'percent'           :     '%', # %
    'period'            :     '.', # .
    'periodcentered'    :  '\xb7', # ·
    'plus'              :     '+', # +
    'plusminus'         :  '\xb1', # ±
    'question'          :     '?', # ?
    'questiondown'      :  '\xbf', # ¿
    'quotedbl'          :     '"', # "
    'quoteleft'         :     '`', # `
    'quoteright'        :     "'", # '
    'registered'        :  '\xae', # ®
    'return'            :    '\r', # 
    'section'           :  '\xa7', # §
    'semicolon'         :     ';', # ;
    'slash'             :     '/', # /
    'space'             :     ' ', #  
    'ssharp'            :  '\xdf', # ß
    'sterling'          :  '\xa3', # £
    'tab'               :    '\t', # 	
    'thorn'             :  '\xfe', # þ
    'threequarters'     :  '\xbe', # ¾
    'threesuperior'     :  '\xb3', # ³
    'twosuperior'       :  '\xb2', # ²
    'uacute'            :  '\xfa', # ú
    'ucircumflex'       :  '\xfb', # û
    'udiaeresis'        :  '\xfc', # ü
    'ugrave'            :  '\xf9', # ù
    'underscore'        :     '_', # _
    'yacute'            :  '\xfd', # ý
    'ydiaeresis'        :  '\xff', # ÿ
    'yen'               :  '\xa5', # ¥
}
for char in (
    '0123456789'
    'abcdefghijklmnopqrstuvwxyz'
):
    KEYNAME_TO_CHAR[char] = char
CHAR_TO_KEYNAME = {
    char: name
    for name, char in KEYNAME_TO_CHAR.items()
}


_SPLIT_RX = re.compile(r'(\s+|[-+]\w+|\w+(?:\s*\()?|.)')


class KeyCombo(object):

    def __init__(self, key_name_to_key_code=None):
        self._down_keys = OrderedDict()
        if key_name_to_key_code is None:
            key_name_to_key_code = lambda key_name: key_name
        self._key_name_to_key_code = key_name_to_key_code

    def __bool__(self):
        return bool(self._down_keys)

    def reset(self):
        key_events = [
            (key_code, False)
            for key_code in self._down_keys
        ]
        self._down_keys = OrderedDict()
        key_events.reverse()
        return key_events

    def parse(self, combo_string):

        down_keys = OrderedDict(self._down_keys)
        key_events = []
        key_stack = []
        token = None
        count = 0

        def _raise_error(exception, details):
            msg = '%s in "%s"' % (
                details,
                combo_string[:count] +
                '[' + token + ']' +
                combo_string[count+len(token):],
            )
            raise exception(msg)

        for token in _SPLIT_RX.split(combo_string):
            if not token:
                continue

            if token[0].isspace():
                pass

            elif re.match(r'[-+]?\w', token):

                add_to_stack = False
                if token.startswith('+'):
                    key_name = token[1:].lower()
                    press, release = True, False
                elif token.startswith('-'):
                    key_name = token[1:].lower()
                    press, release = False, True
                elif token.endswith('('):
                    key_name = token[:-1].rstrip().lower()
                    press, release = True, False
                    add_to_stack = True
                else:
                    key_name = token.lower()
                    press, release = True, True

                key_code = self._key_name_to_key_code(key_name)
                if key_code is None:
                    _raise_error(ValueError, 'unknown key')

                if press:
                    if key_code in down_keys:
                        _raise_error(ValueError, 'key "%s" already pressed' % key_name)
                    key_events.append((key_code, True))
                    down_keys[key_code] = True

                if release:
                    if key_code not in down_keys:
                        _raise_error(ValueError, 'key "%s" already released' % key_name)
                    key_events.append((key_code, False))
                    del down_keys[key_code]

                if add_to_stack:
                    key_stack.append(key_code)

            elif token == ')':
                if not key_stack:
                    _raise_error(SyntaxError, 'unbalanced ")"')
                key_code = key_stack.pop()
                if key_code not in down_keys:
                    _raise_error(ValueError, 'key "%s" already released' % key_name)
                key_events.append((key_code, False))
                del down_keys[key_code]

            else:
                _raise_error(SyntaxError, 'invalid character "%s"' % token)

            count += len(token)

        if key_stack:
            _raise_error(SyntaxError, 'unbalanced "("')

        self._down_keys = down_keys

        return key_events


def add_modifiers_aliases(dictionary):
    ''' Add aliases for common modifiers to a dictionary of key name to key code.

    - add `mod` for `mod_l` aliases for `alt`, `control`, `shift` and `super`
    - add `command` and `windows` aliases for `super`
    - add `option` alias for `alt`
    '''
    for name, extra_aliases in (
        ('control', ''               ),
        ('shift'  , ''               ),
        ('super'  , 'command windows'),
        ('alt'    , 'option'         ,)
    ):
        code = dictionary[name + '_l']
        dictionary[name] = code
        for alias in extra_aliases.split():
            dictionary[alias] = code
