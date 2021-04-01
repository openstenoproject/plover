def meta_word_end(ctx, meta):
    action = ctx.copy_last_action()
    action.word_is_finished = True
    return action
