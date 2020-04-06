def meta_glue(ctx, text):
    action = ctx.new_action()
    action.glue = True
    action.text = text
    if ctx.last_action.glue:
        action.prev_attach = True
    return action
