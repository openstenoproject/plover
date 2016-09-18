
from plover.key_combo import parse_key_combo

from . import TestCase


class KeyComboParserTest(TestCase):

    def test_noop(self):
        for combo_string in ('', '   '):
            self.assertEqual(parse_key_combo(combo_string), [])

    def test_syntax_error(self):
        for combo_string in (
            # Invalid character.
            'Return,',
            'Return&',
            'Ret. urn <',
            'exclam ! foo',
            'shift[a]',
            # Unbalanced )
            ') arg',
            'arg )',
            'arg())',
            'arg(x) )',
            # Unbalanced (
            'test(',
            '( grr',
            'foo ( bar',
            'foo (bar ( ',
            'foo ((',
        ):
            msg = 'parse_key_combo(%r): SyntaxError not raised' % (
                combo_string,
            )
            with self.assertRaisesWithMessage(SyntaxError, msg):
                parse_key_combo(combo_string)

    def test_already_pressed(self):
        for combo_string in (
            # Pressing an already pressed key.
            'foo(foo)',
            'Foo(foO)',
            'foo(fOo(arg))',
            'foo(bar(Foo))',
            'foo(bar(foo(x)))',
        ):
            msg = 'parse_key_combo(%r): ValueError not raised' % (
                combo_string,
            )
            with self.assertRaisesWithMessage(ValueError, msg):
                parse_key_combo(combo_string)

    def test_stacking(self):
        for combo_string_variants, expected in (
            # + press, - release
            # 1 is not a valid identifier, but still a valid key name.
            (('1',)                    , '+1 -1'                                                  ),
            (('Shift_l', 'SHIFT_L')    , '+shift_l -shift_l'                                      ),
            # Case does not matter.
            (('a', ' A ')              , '+a -a'                                                  ),
            (('a(b c)', 'a ( b c   )') , '+a +b -b +c -c -a'                                      ),
            (('a(bc)', ' a(  Bc )')    , '+a +bc -bc -a'                                          ),
            (('a(bc(d)e f(g) h())i j',), '+a +bc +d -d -bc +e -e +f +g -g -f +h -h -a +i -i +j -j'),
            (('foo () bar ( foo a b c (d))',
              'fOo () Bar ( FOO a B c (D))'),
             '+foo -foo +bar +foo -foo +a -a +b -b +c +d -d -c -bar'),
        ):
            expected = [s.strip() for s in expected.split()]
            for combo_string in combo_string_variants:
                result = ['%s%s' % ('+' if pressed else '-', key)
                          for key, pressed in parse_key_combo(combo_string)]
                msg = (
                    'parse_key_combo(%r):\n'
                    ' result  : %r\n'
                    ' expected: %r\n'
                    % (combo_string, result, expected)
                )
                self.assertEqual(result, expected, msg=msg)

    def test_bad_keyname(self):
        name2code = { c: c for c in '123abc' }
        combo_string = '1 (c) 2 bad 3 (a b c)'
        msg = 'parse_key_combo(%r): ValueError not raised' % (
            combo_string,
        )
        with self.assertRaisesWithMessage(ValueError, msg):
            parse_key_combo(combo_string, key_name_to_key_code=name2code.get)

    def test_aliasing(self):
        name2code = {
            '1'     : 10,
            'exclam': 10,
        }
        self.assertListEqual(list(parse_key_combo('1 exclam', key_name_to_key_code=name2code.get)),
                             [(10, True), (10, False),
                              (10, True), (10, False)])

        for combo_string in (
            '1 ( exclam )',
            'exclam(1)',
        ):
            msg = 'parse_key_combo(%r): ValueError not raised' % (
                combo_string,
            )
            with self.assertRaisesWithMessage(ValueError, msg):
                # Yielding the first key event should
                # only happen after full validation.
                parse_key_combo(combo_string, key_name_to_key_code=name2code.get)
