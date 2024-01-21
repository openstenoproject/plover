# `plover.translation` -- Translation

```{py:module} plover.translation
```

% TODO: complete the remainder of this module

```{eval-rst}
.. function:: escape_translation(translation)

.. function:: unescape_translation(translation)

.. class:: Macro(name, stroke, cmdline)

    .. attribute:: name
    .. attribute:: stroke
    .. attribute:: cmdline

.. function:: _mapping_to_macro(mapping, stroke)

.. class:: Translation(outline, translation)

    .. attribute:: strokes
    .. attribute:: rtfcre
    .. attribute:: english
    .. attribute:: replaced
    .. attribute:: formatting
    .. attribute:: is_retrospective_command
    .. method:: has_undo()

.. class:: Translator()

    .. method:: translate(stroke)
    .. method:: set_dictionary(d)
    .. method:: get_dictionary()
    .. method:: add_listener(callback)
    .. method:: remove_listener(callback)
    .. method:: set_min_undo_length(n)
    .. method:: flush([extra_translations=None])
    .. method:: get_state()
    .. method:: set_state(state)
    .. method:: clear_state()
    .. method:: translate_stroke(stroke)
    .. method:: translate_macro(macro)
    .. method:: translate_translation(t)
    .. method:: untranslate_translation(t)
    .. method:: lookup(strokes[, suffixes=()])

.. class:: _State()

    .. method:: prev([count=None])
    .. method:: restrict_size(n)
```
