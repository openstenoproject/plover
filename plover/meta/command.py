def meta_command(ctx, command):
    action = ctx.copy_last_action()
    action.command = command
    return action
