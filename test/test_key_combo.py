
import inspect
import itertools

import pytest

from plover.key_combo import KeyCombo


def generate_combo_tests(test_id, *params, key_name_to_key_code=None):
    yield ('id', test_id)
    if key_name_to_key_code is not None:
        yield ('key_name_to_key_code', key_name_to_key_code)
    for iterables in params:
        iterables = [
            i if isinstance(i, (tuple, list)) else (i,)
            for i in iterables
        ]
        if len(iterables) < 2:
            iterables.append(('',))
        if len(iterables) < 3:
            iterables.append((False,))
        if len(iterables) < 4:
            iterables.append(('',))
        for combo_string, parse_result, bool_result, reset_result in itertools.product(*iterables):
            yield (
                ('parse', combo_string, parse_result),
                ('bool', bool_result),
                ('reset', reset_result),
            )

KEY_COMBO_TESTS = tuple(itertools.chain(
    (
        # id TEST_IDENTIFIER
        # key_name_to_key_code KEY_NAME_TO_KEY_CODE_FUNCTION
        # parse COMBO_STRING KEY_EVENTS
        # bool HAS_PRESSED
        # reset KEY_EVENTS

        ('key_name_to_key_code', lambda k: k),

        # Initial state.
        ('id', 'initial_state'),
        (
            ('bool', False),
            ('reset', ''),
        ),

        # Reset after holding a key.
        ('id', 'reset'),
        (
            ('parse', '+a b', '+a +b -b'),
            ('bool', True),
            ('reset', '-a'),
            ('bool', False),
            ('reset', ''),
        ),
    ),

    # No-op.
    generate_combo_tests(
        'no-op',
        (('', '   '), '', False, ''),
    ),

    # Syntax error:
    generate_combo_tests(
        'syntax_error',
        ((
            # - invalid character
            'Return,',
            'Return&',
            'Ret. urn <',
            'exclam ! foo',
            'shift[a]',
            # - unbalanced `)`
            ') arg',
            'arg )',
            'arg())',
            'arg(x) )',
            # - unbalanced `(`
            'test(',
            '( grr',
            'foo ( bar',
            'foo (bar ( ',
            'foo ((',
            # - [-+]key() is not valid
            '+foo ()',
            '+foo()',
        ), SyntaxError, False, ''),
    ),

    # Pressing an already pressed key.
    generate_combo_tests(
        'already_pressed',
        ((
            'foo(foo)',
            'Foo(foO)',
            'foo(fOo(arg))',
            'foo(bar(Foo))',
            'foo(bar(foo(x)))',
            '+foo +foo',
            'foo(+foo)',
            '+foo bar(foo)',
            '+foo bar(+foo)',
        ), ValueError, False, ''),
    ),

    # Trying to release a key not pressed.
    generate_combo_tests(
        'already_released',
        (('-foo', 'foo(-bar)'), ValueError, False, ''),
    ),

    # Stacking.
    generate_combo_tests(
        'stacking',
        # 1 is not a valid identifier, but still a valid key name.
        (('1', '+1 -1'), '+1 -1'),
        (('Shift_l', 'SHIFT_L', '+shift_l -SHIFT_l'), '+shift_l -shift_l'),
        # Case does not matter.
        (('a', ' A ', ' +A -a  '), '+a -a'),
        (('a(b c)', 'a ( b c   )', 'a(+b-b+c-c)'), '+a +b -b +c -c -a'),
        (('a(bc)', ' a(  Bc )', '+A+BC-BC-A'), '+a +bc -bc -a'),
        (('a(bc(d)e f(g) h())i j', '+a +bc d -bc e +f g -f h -a i j'),
         '+a +bc +d -d -bc +e -e +f +g -g -f +h -h -a +i -i +j -j'),
        (('foo () bar ( foo a b c (d))', 'fOo () Bar ( FOO a B c (D))',
          '+foo -foo +bar +foo -foo +a -a +b -b +c +d -d -c -bar'),
         '+foo -foo +bar +foo -foo +a -a +b -b +c +d -d -c -bar'),
    ),

    # Held keys.
    generate_combo_tests(
        'held_keys',
        ('+a', '+a', True, '-a'),
        (('+alt tab', '+alt +tab -tab'), '+alt +tab -tab', True, '-alt'),
    ),

    # Split combo.
    (
        ('id', 'split_combo'),
        (
            ('parse', '+alt tab', '+alt +tab -tab'),
            ('bool', True),
            ('parse', 'tab', '+tab -tab'),
            ('bool', True),
            ('reset', '-alt'),
            ('bool', False),
        ),
    ),

    # Invalid key name.
    generate_combo_tests(
        'invalid_key',
        (('1 (c) 2 bad 3 (a b c)', '1 +c 2 +bad 3',), ValueError),
        key_name_to_key_code={c: c for c in '123abc'}.get,
    ),

    # Same key code, multiple key names.
    generate_combo_tests(
        'aliasing',
        (('1 exclam', '+1 -exclam +exclam -1'), '+10 -10 +10 -10'),
        (('1 ( exclam )', 'exclam(1)', '+1 +exclam', 'exclam(-1)'), ValueError),
        key_name_to_key_code={'1': '10', 'exclam': '10'}.get,
    ),

))

def parametrize(tests):
    key_name_to_key_code = None
    test_id = None
    args = []
    ids = []
    for t in tests:
        if t[0] == 'key_name_to_key_code':
            key_name_to_key_code = t[1]
        elif t[0] == 'id':
            test_id = t[1]
        else:
            assert key_name_to_key_code is not None
            assert test_id is not None
            args.append((key_name_to_key_code, t))
            ids.append(test_id)
    return pytest.mark.parametrize(
        ('key_name_to_key_code', 'instructions'),
        args, ids=ids
    )

@parametrize(KEY_COMBO_TESTS)
def test_key_combo(key_name_to_key_code, instructions):
    def repr_expected(result):
        assert isinstance(result, str)
        return [s.strip() for s in result.split()]
    def repr_key_events(events):
        assert isinstance(events, list)
        return ['%s%s' % ('+' if pressed else '-', key)
                for key, pressed in events]
    kc = KeyCombo(key_name_to_key_code)
    for action, *args in instructions:
        if action == 'parse':
            combo_string, key_events = args
            if inspect.isclass(key_events):
                with pytest.raises(key_events):
                    kc.parse(combo_string)
            else:
                assert repr_key_events(kc.parse(combo_string)) == repr_expected(key_events)
        elif action == 'bool':
            has_pressed = args[0]
            assert bool(kc) == has_pressed
        elif action == 'reset':
            key_events = args[0]
            assert repr_key_events(kc.reset()) == repr_expected(key_events)
        else:
            raise ValueError(args[0])
