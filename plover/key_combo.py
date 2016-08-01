# -*- coding: utf-8 -*-

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
    'aacute'            :  u'\xe1', # á
    'acircumflex'       :  u'\xe2', # â
    'acute'             :  u'\xb4', # ´
    'adiaeresis'        :  u'\xe4', # ä
    'ae'                :  u'\xe6', # æ
    'agrave'            :  u'\xe0', # à
    'ampersand'         :     u'&', # &
    'apostrophe'        :     u"'", # '
    'aring'             :  u'\xe5', # å
    'asciicircum'       :     u'^', # ^
    'asciitilde'        :     u'~', # ~
    'asterisk'          :     u'*', # *
    'at'                :     u'@', # @
    'atilde'            :  u'\xe3', # ã
    'backslash'         :    u'\\', # \
    'bar'               :     u'|', # |
    'braceleft'         :     u'{', # {
    'braceright'        :     u'}', # }
    'bracketleft'       :     u'[', # [
    'bracketright'      :     u']', # ]
    'brokenbar'         :  u'\xa6', # ¦
    'ccedilla'          :  u'\xe7', # ç
    'cedilla'           :  u'\xb8', # ¸
    'cent'              :  u'\xa2', # ¢
    'clear'             :   '\x0b', # 
    'colon'             :     u':', # :
    'comma'             :     u',', # ,
    'copyright'         :  u'\xa9', # ©
    'currency'          :  u'\xa4', # ¤
    'degree'            :  u'\xb0', # °
    'diaeresis'         :  u'\xa8', # ¨
    'division'          :  u'\xf7', # ÷
    'dollar'            :     u'$', # $
    'eacute'            :  u'\xe9', # é
    'ecircumflex'       :  u'\xea', # ê
    'ediaeresis'        :  u'\xeb', # ë
    'egrave'            :  u'\xe8', # è
    'equal'             :     u'=', # =
    'eth'               :  u'\xf0', # ð
    'exclam'            :     u'!', # !
    'exclamdown'        :  u'\xa1', # ¡
    'grave'             :     u'`', # `
    'greater'           :     u'>', # >
    'guillemotleft'     :  u'\xab', # «
    'guillemotright'    :  u'\xbb', # »
    'hyphen'            :  u'\xad', # ­
    'iacute'            :  u'\xed', # í
    'icircumflex'       :  u'\xee', # î
    'idiaeresis'        :  u'\xef', # ï
    'igrave'            :  u'\xec', # ì
    'less'              :     u'<', # <
    'macron'            :  u'\xaf', # ¯
    'masculine'         :  u'\xba', # º
    'minus'             :     u'-', # -
    'mu'                :  u'\xb5', # µ
    'multiply'          :  u'\xd7', # ×
    'nobreakspace'      :  u'\xa0', #  
    'notsign'           :  u'\xac', # ¬
    'ntilde'            :  u'\xf1', # ñ
    'numbersign'        :     u'#', # #
    'oacute'            :  u'\xf3', # ó
    'ocircumflex'       :  u'\xf4', # ô
    'odiaeresis'        :  u'\xf6', # ö
    'ograve'            :  u'\xf2', # ò
    'onehalf'           :  u'\xbd', # ½
    'onequarter'        :  u'\xbc', # ¼
    'onesuperior'       :  u'\xb9', # ¹
    'ooblique'          :  u'\xd8', # Ø
    'ordfeminine'       :  u'\xaa', # ª
    'oslash'            :  u'\xf8', # ø
    'otilde'            :  u'\xf5', # õ
    'paragraph'         :  u'\xb6', # ¶
    'parenleft'         :     u'(', # (
    'parenright'        :     u')', # )
    'percent'           :     u'%', # %
    'period'            :     u'.', # .
    'periodcentered'    :  u'\xb7', # ·
    'plus'              :     u'+', # +
    'plusminus'         :  u'\xb1', # ±
    'question'          :     u'?', # ?
    'questiondown'      :  u'\xbf', # ¿
    'quotedbl'          :     u'"', # "
    'quoteleft'         :     u'`', # `
    'quoteright'        :     u"'", # '
    'registered'        :  u'\xae', # ®
    'return'            :     '\r', # 
    'section'           :  u'\xa7', # §
    'semicolon'         :     u';', # ;
    'slash'             :     u'/', # /
    'space'             :     u' ', #  
    'ssharp'            :  u'\xdf', # ß
    'sterling'          :  u'\xa3', # £
    'tab'               :     '\t', # 	
    'thorn'             :  u'\xfe', # þ
    'threequarters'     :  u'\xbe', # ¾
    'threesuperior'     :  u'\xb3', # ³
    'twosuperior'       :  u'\xb2', # ²
    'uacute'            :  u'\xfa', # ú
    'ucircumflex'       :  u'\xfb', # û
    'udiaeresis'        :  u'\xfc', # ü
    'ugrave'            :  u'\xf9', # ù
    'underscore'        :     u'_', # _
    'yacute'            :  u'\xfd', # ý
    'ydiaeresis'        :  u'\xff', # ÿ
    'yen'               :  u'\xa5', # ¥
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


_SPLIT_RX = re.compile(r'(\s+|(?:\w+(?:\s*\()?)|.)')

def parse_key_combo(combo_string, key_name_to_key_code=None):

    if key_name_to_key_code is None:
        key_name_to_key_code = lambda key_name: key_name

    key_events = []
    down_keys = []
    token = None
    count = 0

    def _raise_error(exception, details):
        msg = u'%s in "%s"' % (
            details,
            combo_string[:count] +
            u'[' + token + u']' +
            combo_string[count+len(token):],
        )
        raise exception(msg)

    for token in _SPLIT_RX.split(combo_string):
        if not token:
            continue

        if token.isspace():
            pass

        elif re.match(r'\w', token):

            if token.endswith(u'('):
                key_name = token[:-1].rstrip().lower()
                release = False
            else:
                key_name = token.lower()
                release = True

            key_code = key_name_to_key_code(key_name)
            if key_code is None:
                _raise_error(ValueError, 'unknown key')
            elif key_code in down_keys:
                _raise_error(ValueError, u'key "%s" already pressed' % key_name)

            key_events.append((key_code, True))

            if release:
                key_events.append((key_code, False))
            else:
                down_keys.append(key_code)

        elif token == u')':
            if not down_keys:
                _raise_error(SyntaxError, u'unbalanced ")"')
            key_code = down_keys.pop()
            key_events.append((key_code, False))

        else:
            _raise_error(SyntaxError, u'invalid character "%s"' % token)

        count += len(token)

    if down_keys:
        _raise_error(SyntaxError, u'unbalanced "("')

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
