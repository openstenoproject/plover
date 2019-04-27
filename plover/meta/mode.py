from plover.formatting import Case, SPACE


MODE_CAMEL = 'CAMEL'
MODE_CAPS = 'CAPS'
MODE_LOWER = 'LOWER'
MODE_RESET = 'RESET'
MODE_RESET_CASE = 'RESET_CASE'
MODE_RESET_SPACE = 'RESET_SPACE'
MODE_SET_SPACE = 'SET_SPACE:'
MODE_SNAKE = 'SNAKE'
MODE_TITLE = 'TITLE'


def meta_mode(ctx, mode):
    """
    mode should be:
        CAPS, LOWER, TITLE, CAMEL, SNAKE, RESET_SPACE,
            RESET_CASE, SET_SPACE or RESET

        CAPS: UPPERCASE
        LOWER: lowercase
        TITLE: Title Case
        CAMEL: titleCase, no space, initial lowercase
        SNAKE: Underscore_space
        RESET_SPACE: Space resets to ' '
        RESET_CASE: Reset to normal case
        SET_SPACE:xy: Set space to xy
        RESET: Reset to normal case, space resets to ' '
    """
    action = ctx.copy_last_action()
    if mode == MODE_CAPS:
        action.case = Case.UPPER
    elif mode == MODE_TITLE:
        action.case = Case.TITLE
    elif mode == MODE_LOWER:
        action.case = Case.LOWER
    elif mode == MODE_SNAKE:
        action.space_char = '_'
    elif mode == MODE_CAMEL:
        action.case = Case.TITLE
        action.space_char = ''
        action.next_case = Case.LOWER_FIRST_CHAR
    elif mode == MODE_RESET:
        action.space_char = SPACE
        action.case = None
    elif mode == MODE_RESET_SPACE:
        action.space_char = SPACE
    elif mode == MODE_RESET_CASE:
        action.case = None
    elif mode.startswith(MODE_SET_SPACE):
        action.space_char = mode[len(MODE_SET_SPACE):]
    else:
        raise ValueError('%r is not a valid mode' % mode)
    return action
