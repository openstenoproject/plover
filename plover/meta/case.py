from plover.formatting import Case, apply_case


def meta_case(ctx, case):
    case = Case(case.lower())
    action = ctx.copy_last_action()
    action.next_case = case
    return action

def meta_retro_case(ctx, case):
    case = Case(case.lower())
    action = ctx.copy_last_action()
    action.prev_attach = True
    last_words = ctx.last_words(count=1)
    if last_words:
        action.prev_replace = last_words[0]
        action.text = apply_case(last_words[0], case)
    else:
        action.text = ''
    return action
