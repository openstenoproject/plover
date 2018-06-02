
from unittest.mock import MagicMock, call, patch

import pytest

from plover import system
from plover.machine.keyboard import Keyboard
from plover.machine.keymap import Keymap
from plover.oslayer.keyboardcontrol import KeyboardCapture


def send_input(capture, key_events):
    for evt in key_events.strip().split():
        if evt.startswith('+'):
            capture.key_down(evt[1:])
        elif evt.startswith('-'):
            capture.key_up(evt[1:])
        else:
            capture.key_down(evt)
            capture.key_up(evt)


@pytest.fixture
def capture():
    capture = MagicMock(spec=KeyboardCapture)
    with patch('plover.machine.keyboard.KeyboardCapture', new=lambda: capture):
        yield capture

@pytest.fixture(params=[False])
def machine(request, capture):
    machine = Keyboard({'arpeggiate': request.param})
    keymap = Keymap(Keyboard.KEYS_LAYOUT.split(),
                    system.KEYS + Keyboard.ACTIONS)
    keymap.set_mappings(system.KEYMAPS['Keyboard'])
    machine.set_keymap(keymap)
    return machine

def arpeggiate(func):
    return pytest.mark.parametrize('machine', [True], indirect=True)(func)

@pytest.fixture
def strokes(machine):
    strokes = []
    machine.add_stroke_callback(strokes.append)
    return strokes


def test_lifecycle(capture, machine, strokes):
    # Start machine.
    machine.start_capture()
    assert capture.mock_calls == [
        call.suppress_keyboard(()),
        call.start(),
    ]
    capture.reset_mock()
    machine.set_suppression(True)
    suppressed_keys = dict(machine.keymap.get_bindings())
    del suppressed_keys['space']
    assert strokes == []
    assert capture.mock_calls == [
        call.suppress_keyboard(suppressed_keys.keys()),
    ]
    # Trigger some strokes.
    capture.reset_mock()
    send_input(capture, '+a +h -a -h space w')
    assert strokes == [
        {'S-', '*'},
        {'T-'},
    ]
    assert capture.mock_calls == []
    # Stop machine.
    del strokes[:]
    machine.stop_capture()
    assert strokes == []
    assert capture.mock_calls == [
        call.suppress_keyboard(()),
        call.cancel(),
    ]

def test_unfinished_stroke_1(capture, machine, strokes):
    machine.start_capture()
    send_input(capture, '+a +q -a')
    assert strokes == []

def test_unfinished_stroke_2(capture, machine, strokes):
    machine.start_capture()
    send_input(capture, '+a +r -a +a -r')
    assert strokes == []

@arpeggiate
def test_arpeggiate_1(capture, machine, strokes):
    machine.start_capture()
    send_input(capture, 'a h space w')
    assert strokes == [{'S-', '*'}]

@arpeggiate
def test_arpeggiate_2(capture, machine, strokes):
    machine.start_capture()
    send_input(capture, 'a +h +space -space -h w')
    assert strokes == [{'S-', '*'}]
