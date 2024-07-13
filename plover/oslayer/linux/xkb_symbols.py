"""
Simple loop to go through all keys in a keymap, and find the possible keys to type using modifiers,
then return a list in the format [(base, modifiers)], that can be used to emulate the key presses
This code is a bit messy, and could be improved on a lot, but from my testing, it seems to work with different layouts
"""

from xkbcommon import xkb


# layout can be "no", "us", "gb", "fr" or any other xkb layout
def generate_symbols(layout="us", variant = ""):
    ctx = xkb.Context()
    keymap = ctx.keymap_new_from_names(layout=layout, variant=variant)
    # The keymaps have to be "translated" to a US layout keyboard for evdev
    keymap_us = ctx.keymap_new_from_names(layout="us")

    # Modifier names from xkb, converted to lists of modifiers
    level_mapping = {
        0: [],
        1: ["shift_l"],
        2: ["alt_r"],
        3: ["shift_l", "alt_r"],
    }

    symbols = {}

    for key in iter(keymap):
        try:
            # Levels are different outputs from the same key with modifiers pressed
            levels = keymap.num_levels_for_key(key, 1)
            if levels == 0:  # Key has no output
                continue

            # === Base key symbol ===
            base_key_syms = keymap_us.key_get_syms_by_level(key, 1, 0)
            if len(base_key_syms) == 0:  # There are no symbols for this key
                continue
            base_key = xkb.keysym_to_string(base_key_syms[0])
            if base_key is None:
                continue

            # === Key variations ===
            if levels < 1:  # There are no variations (Check maybe not needed)
                continue
            for level in range(0, levels + 1):  # Ignoring the first (base) one
                level_key_syms = keymap.key_get_syms_by_level(key, 1, level)
                if len(level_key_syms) == 0:
                    continue
                level_key = xkb.keysym_to_string(level_key_syms[0])
                if level_key is None:
                    continue
                modifiers = level_mapping.get(level, "")
                if not level_key in symbols:
                    symbols[level_key] = (base_key, modifiers)
        except xkb.XKBInvalidKeycode:
            # Iter *should* return only valid, but still returns some invalid...
            pass

    return symbols
