def meta_key_combo(ctx, combo):
    action = ctx.copy_last_action()
    action.combo = combo
    return action
