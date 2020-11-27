``plover.steno`` -- Steno data model
====================================

This module deals with the fundamental concept in stenography: the `stroke`.
A stroke is a combination of keys all pressed at once; an `outline` is a series
of strokes performed in succession.

Many Plover actions deal with steno strokes, and this will be especially useful
to authors of system and dictionary plugins.

Steno Notation
--------------

Steno notation refers to the way steno strokes are written textually, such as
on the paper tape or in dictionaries. Each stroke is written as a concatenation
of several keys, sometimes with a hyphen.

Steno notation is also sometimes referred to as *RTF/CRE* (Rich Text Format
with Court Reporting Extensions) *notation*, named after the dictionary format
that popularized it.

Each steno system has a `steno order`, or a canonical ordering of all the keys
on the layout. For most systems, this is the ordering of the keys from left to
right, starting with the left bank, then the thumb keys, then the right bank,
but others may use a different order. Well-formed steno notation **must** have
all keys in steno order.

The full list of keys and rules for expressing strokes in steno notation are
defined for each steno system. See :doc:`system` for more information.

Keys
^^^^

Combinations of keys can be expressed by concatenating the letters representing
them; for example, ``S-``, ``-E`` and ``-T`` together can be written ``SET``,
and ``K-`` and ``W-`` together can be written ``KW-``. All but one hyphen is
removed to separate the left and right bank keys, but the hyphen may be
omitted completely if a stroke includes certain keys, such as the ``-E`` in
``SET``, or the ``*`` in ``R*R``.

Strokes are often written with a hyphen, because without one it may not be
fully clear which side each key is on. For example, the ``P`` in ``KPT`` may
refer to *either* left-hand ``P-`` *or* right-hand ``-P``; writing ``KP-T`` or
``K-PT`` respectively is unambiguous.

Some strokes may still be resolvable when not completely well-formed, i.e.
the hyphen is in the wrong place or doesn't exist when it should, or the keys
aren't fully in steno order, but it's not guaranteed to work.

Numbers
^^^^^^^

When a part of a stroke represents a number we don't write the number key;
instead, we replace the letter keys with the corresponding numbers.

For example, to express the stroke represented by pressing the ``S-`` and
``T-`` keys together with the number bar (``#``) in steno notation, we write
``12-``, since ``S-`` represents the number ``1-`` and ``T-`` represents ``2-``.

If a stroke consists *only* of a number key, or none of the other pressed keys
represent numbers, we still write the number key. For example, ``#`` and ``#-R``
are both valid steno notation, since ``-R`` does not represent a number, but
``#P-`` is not (write ``3-`` instead).

Multiple Strokes
^^^^^^^^^^^^^^^^

We use the stroke delimiter, ``/``, to separate successive strokes in a single
outline. For example, to write the 3-stroke outline for `New York Times`, we
write:

.. code-block:: none

    TPHU/KWRORBG/TAOEUPLS

Note that ``TPHU``, ``KWRORBG`` and ``TAOEUPLS`` are all separate strokes, but
the ``/`` indicates that they are written in sequence.

.. py:module:: plover.steno

.. data:: STROKE_DELIMITER

    The character used to separate successive strokes.
    This is equivalent to ``/``.

.. class:: Stroke(steno_keys)

    .. attribute:: steno_keys

    .. attribute:: rtfcre

    .. attribute:: is_correction

.. function:: normalize_stroke(stroke)

.. function:: normalize_steno(strokes_string)

.. function:: sort_steno_keys(steno_keys)

.. function:: sort_steno_strokes(strokes_list)
