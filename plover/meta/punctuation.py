from plover.formatting import Case


def meta_comma(ctx, text):
    action = ctx.new_action()
    action.text = text
    action.prev_attach = True
    return action

def meta_stop(ctx, text):
    action = ctx.new_action()
    action.prev_attach = True
    action.text = text
    action.next_case = Case.CAP_FIRST_WORD
    return action
