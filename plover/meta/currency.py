def meta_retro_currency(ctx, dict_format):
    action = ctx.copy_last_action()
    last_words = ctx.last_words(count=1)
    if not last_words:
        return action
    currency = last_words[0].replace(',', '')
    for cast, fmt in (
        (int,   '{:,}'   ),
        (float, '{:,.2f}'),
    ):
        try:
            cast_input = cast(currency)
        except ValueError:
            continue
        currency_format = dict_format.replace('c', fmt)
        action.prev_attach = True
        action.prev_replace = last_words[0]
        action.text = currency_format.format(cast_input)
        action.word = None
        break
    return action
