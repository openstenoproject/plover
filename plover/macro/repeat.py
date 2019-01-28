
from plover.steno import Stroke


def last_stroke(translator, stroke, cmdline):
    assert not cmdline
    # Repeat last stroke
    translations = translator.get_state().translations
    if not translations:
        return
    stroke = Stroke(translations[-1].strokes[-1].steno_keys)
    translator.translate_stroke(stroke)
