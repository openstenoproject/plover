
import re


_SPLIT_RX = re.compile(ur'(\s+|(?:\w+(?:\s*\()?)|.)')

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

        elif re.match(ur'\w', token):

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
