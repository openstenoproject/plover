# Translation Language

In addition to translating normal text, Plover supports some special
formatting operators as well as commands to control the steno engine behavior.
This page describes all of these operators and how they are represented in
translations.

Most formatting operators and commands are surrounded by curly brackets `{}`,
so when writing literal curly brackets they must be escaped: `\{\}`.

## Spacing & Affixes

By default, defining a translation with just a word will output that word
with spaces on either side. The space is inserted either before or after the
translated word, depending on your configuration. The operators in this section
control when spaces are entered.

### Attach

The _attach_ operator removes spaces on either end of a word to allow prefixes
and suffixes to be attached to the adjoining word.

::::{plover:operator} {^}; {:attach}
Attaches a word to a preceding or succeeding word.

:::{plover:operator} {^}[suffix]; {:attach}[suffix]
Attaches the suffix to the previous word.

_Example_: `is` + `{^}n't` = `isn't`
:::

:::{plover:operator} {^[suffix]}; {:attach:^[suffix]}
An orthographically-aware attachment, which changes the spelling of the
suffix when needed to follow English orthography rules.
Where `red` + `{^}ish` with a raw attachment would produce `redish`,
`red` + `{^ish}` with the ortho-aware attachment would return the expected
`reddish`.
:::

:::{plover:operator} [prefix]{^}; {[prefix]^}; [prefix]{:attach}; {:attach:[prefix]^}
Attaches the prefix to the next word.

_Example_: `re{^}` + `port` = `report`
:::

:::{plover:operator} {^}[infix]{^}; {^[infix]^}; {:attach:[infix]}
Attaches the infix to the words on either side.

_Example_: `day` + `{^}-to-{^}` + `day` = `day-to-day`
:::
::::

:::{note}
If the text you are trying to attach is some kind of punctuation, prefer to use
the raw attachment versions, e.g. `:{^}` rather than `{:^}`, or `{^}\}` instead
of `{^\}}`.
:::

While attachment is meant primarily for prefixes and suffixes, this can be
extended to other operations involving spacing:

:::{plover:operator} {^^}; {:attach:}
Removes the space, so that the next word written is attached to the previous
one. Especially useful for compound words that aren't explicitly defined.

_Default outline_: `TK-LS` ("**D**e**L**ete **S**pace")
:::

:::{plover:operator} {^ ^}; {:attach: }
Forces a space to be added even when writing the next stroke would result in
an attachment. For example, whereas `break` + `fast` would result in
`breakfast`, a space can be added in between: `break` + `{^ ^}` + `fast`.

_Default outline_: `S-P` ("**SP**ace")
:::

### Glue

The _glue_ operator acts like the attach operator above, but only attaches to
neighboring glue translations. This is commonly used in numbers and
fingerspelling.

Translations containing only digits are implicitly glued, allowing you to
output multiple number outlines to make a larger number.

:::{plover:operator} {&[text]}; {:glue:[text]}
Glues the text.
:::

### Retroactive Spacing

The operators below add or remove spaces between your last stroke and the one
before that.

:::{plover:operator} {*?}; =retro_insert_space; =retrospective_insert_space
Adds a space between the last two strokes. For example, if your dictionary
contained `PER` for 'perfect', `SWAEUGS` for 'situation' and `PER/SWAEUGS` for
'persuasion', you can force Plover to output 'perfect situation' by writing
`{*?}`.

The name `=retrospective_insert_space` is _deprecated_; prefer `=retro_insert_space` instead.

_Suggested outline_: `AFPS` ("**A**dd **SP**a**C**e")
:::

:::{plover:operator} {*!}; =retro_delete_space; =retrospective_delete_space
Delete the space between the last two strokes. For example, if you wrote
'basket ball', you could force them together into 'basketball' by writing `{*!}`.

The name `=retrospective_delete_space` is _deprecated_; prefer `=retro_delete_space` instead.

_Suggested outline_: `TK-FPS` ("**D**elete **SP**a**C**e")
:::

### Whitespace

Instead of using the [keyboard shortcuts mechanism](key-combo) to press Enter
`{#return}` and Tab `{#tab}`, neither of which are undoable, escape sequences
can be used in definitions.

:::{plover:operator} \n
Sends a newline character. Equivalent of pressing Enter, but undoable.
:::

:::{plover:operator} \t
Sends a tab character. Equivalent of pressing Tab, but undoable.
:::

### Spacing Modes

In addition to outputting the space character between words, Plover can also
output other characters, or none at all.

:::{plover:operator} {mode:set_space:[char]}
Set the space character to `char`, which may be a string of multiple characters.
To remove spaces altogether, set this to an empty string: `{mode:set_space:}`.
:::

:::{plover:operator} {mode:reset_space}
Reset the space character.
:::

## Casing and Capitalization

::::{plover:operator} {-|}; {:case:cap_first_word}
Capitalizes the first letter of the next word.

_Default outline_: `KPA` ("cap")

:::{plover:operator} {^}{-|}
Deletes a space and capitalizes the next word, enabling writing in CamelCase.

_Default outline_: `KPA*`
:::
::::

:::{plover:operator} {*-|}; {:retro_case:cap_first_word}
Capitalizes the first letter of the previous word. This is useful in case you
realize that a word should be capitalized after you've written it. For example,
`cat` + `{*-|}{^ville}` = `Catville`.

_Suggested outline_: `KA*PD` ("capped")
:::

:::{plover:operator} {>}; {:case:lower_first_char}
Forces the next letter to be lowercase, for example `{>}Plover` = `plover`.

_Suggested outline_: `HRO*ER` ("lower")
:::

:::{plover:operator} {*>}; {:retro_case:lower_first_char}
Rewrites the previous word to start with a lowercase letter, for example
`Plover{*>}` = `plover`.

_Suggested outline_: `HRO*ERD` ("lowered")
:::

:::{plover:operator} {<}; {:case:upper_first_word}
Outputs the next word in all capital letters, for example `{<}cat` = `CAT`.

_Suggested outline_: `KPA*L` ("cap all")
:::

:::{plover:operator} {*<}; {:retro_case:upper_first_word}
Rewrites the previous word in all capital letters, for example `cat{*<}` = `CAT`.

_Suggested outline_: `*UPD`
:::

### Carrying Capitalization

In English, we have punctuation that doesn't get capitalized, but instead the
next letter gets the capitalization. For example, if you end a sentence in
quotes, the next sentence still starts with a capital letter:
`"You can't eat that!" The baby ate on.`

In order to support this, there is a special syntax that will "pass on" or
"carry" the capitalized state. You might find this useful with quotes,
parentheses, and words like `'til` or `'cause`.

:::{plover:operator} {~|[text]}; {^~|[text]}; {~|[text]^}; {^~|[text]^}
Carries the capitalization from before the `text` over to after it.
For example, an opening quotation mark can be implemented as `{~|"^}`.
:::

### Casing Modes

In addition to altering casing for individual words, you can use operators to
set a long-running casing mode, such as writing in all-caps or in title case:

:::{plover:operator} {mode:caps}
SETS OUTPUT TO ALL CAPS.
:::

:::{plover:operator} {mode:title}
Sets Output To Title Case.
:::

:::{plover:operator} {mode:lower}
sets output to lower case.
:::

:::{plover:operator} {mode:camel}
SetsOutputToCamelCase.
:::

:::{plover:operator} {mode:snake}
Sets_output_to_snake_case.
:::

:::{plover:operator} {mode:reset_case}
Resets output to the normal casing mode.
:::

## Punctuation

The main punctuation symbols (`.`, `,`, `:`, `;`, `?`, `!`) can be written in
brackets to provide automatic spacing and capitalization where necessary:

:::{plover:operator} {.}; {:stop:.}
Inserts a full stop or period, with a space after but not before, and
capitalizing the first word after. Short for `{^}.{-|}`.

_Default outline_: `TP-PL`, `-FPLT`
:::

:::{plover:operator} {,}; {:comma:,}
Inserts a comma, with a space after but not before. Short for `{^},`.

_Default outline_: `KW-BG`, `-RBGS`
:::

:::{plover:operator} {?}; {:stop:?}
Inserts a question mark, with a space after but not before,
and capitalizing the first word after. Short for `{^}?{-|}`.

_Default outline_: `KW-PL`, `STPH`
:::

:::{plover:operator} {!}; {:stop:!}
Inserts an exclamation mark, with a space after but not before,
and capitalizing the first word after. Short for `{^}!{-|}`.

_Default outline_: `TP-BG`, `STKPWHR-FPLT`
:::

:::{plover:operator} {:}; {:comma::}
Inserts a colon, with a space after but not before. Short for `{^}:`.

_Default outline_: `STPH-FPLT`
:::

:::{plover:operator} {;}; {:comma:;}
Inserts a semicolon, with a space after but not before. Short for `{^};`.

_Default outline_: `STPH*FPLT`
:::

## Currency

Plover has an operator to format the last written number as a currency amount.
The amount is written with either no decimal places or two, and commas are
added every 3 digits.

:::{plover:operator} {*([prefix]c[suffix])}; {:retro_currency:[prefix]c[suffix]}
Retroactively converts the previously written number into a currency amount.
The number takes the place of the `c` in the format specification.

For example, `{*($c)}` is the standard way of formatting dollars in English;
the symbol can also be placed after the `c`, such as when writing Japanese yen:
`{*(c円)}`.
:::

## Lookahead Translation

Plover also supports conditional translations depending on the following text.

:::{plover:operator} {=[regex]/[match_text]/[no_match_text]}; {:if_next_matches:[regex]/[match_text]/[no_match_text]}
Translates to `match_text` if the text after this translation matches `regex`,
or `no_match_text` otherwise. `regex` is a pattern following Python's regular
expression syntax.

For example, `{=[AEIOUaeiou]/an/a}` outputs `an` if the next word starts with
a vowel, or `a` otherwise.
:::

(key-combo)=

## Keyboard Shortcuts

Plover allows sending arbitrary keyboard shortcuts, for when text output is
not sufficient. This is useful for things like application commands.

:::{plover:operator} {#[combo]}; {:key_combo:[combo]}
Sends the keystroke defined by `combo`, which is a key combination string.
Key combination strings are case-insensitive.
:::

Key combination strings are defined as sequences of key names separated by
spaces, occasionally with modifiers, for example `{#control(z shift(z))}`
presses Ctrl-Z then Ctrl-Shift-Z.

:::{warning}
Keyboard shortcuts are not undoable. When inputting symbols or letters, prefer
to use other means such as entering raw symbols or fingerspelling. For example,
`\n` should be used over `{#return}`.
:::

### Key Names

:::{describe} a, b, c, ...
Press the individual letter keys.
:::

:::{describe} 0, 1, 2, ...
Press the individual number keys.
:::

:::{describe} udiaeresis, eacute, ...
Press accented letter keys on international layouts.
:::

All possible keys are defined in the [Plover codebase](https://github.com/openstenoproject/plover/blob/main/plover/key_combo.py#L21).

:::{note}
When specifying a key by the name of a symbol that would normally be produced
by adding the Shift modifier on your keyboard, the Shift key will **not** be
added. For example, `{#plus}` sends `=` on a US layout; to send `+`, you should
specify `{#shift(plus)}` (or, more correctly, `{#shift(equal)}`).
:::

### Modifier Keys

To specify modifier keys, surround the key sequence with parentheses and
precede it with the modifier key name. These can be nested.

:::{plover:combo} Shift_L([combo]); Shift_R([combo]); shift([combo])
Shift key modifier.
:::

:::{plover:combo} Control_L([combo]); Control_R([combo]); control([combo])
Ctrl key modifier.
:::

:::{plover:combo} Alt_L([combo]); Alt_R([combo]); alt([combo]); option([combo])
Alt key modifier, or Option on macOS.
:::

:::{plover:combo} Super_L([combo]); Super_R([combo]); super([combo]); windows([combo]); command([combo])
Super key modifier, or Command on macOS and the Windows key on Windows.
:::

## Other Formatting Actions

:::{plover:operator} =undo
Undoes the last stroke.

_Default outline_: `*`
:::

:::{plover:operator} {*+}; =repeat_last_stroke
Sends the last stroke entered. For example, `KAT{*+}{*+}` translates to
`cat cat cat`. Especially useful for repeated keys, such as navigating around
a document.

_Suggested outline_: `#`
:::

:::{plover:operator} {*}; =retro_toggle_asterisk; =retrospective_toggle_asterisk
Toggles the asterisk key on the last stroke entered. For example, `KAT{*}` will
translate as if you wrote `KA*T`, and `KA*T{*}` will translate as if you wrote `KAT`.

The name `=retrospective_toggle_asterisk` is _deprecated_; prefer `=retro_toggle_asterisk` instead.

_Suggested outline_: `#*`
:::

:::{plover:operator} {}
Cancels the formatting of the next word.

Using `{}` in front of a arrow key commands, as in `{}{#Left}`, is useful if
the arrow key commands are used to move cursor to edit text. Canceling
formatting actions for cursor movement prevents Plover from, for instance,
capitalizing words in middle of a sentence if cursor is moved back when the
last stroke, such as `{.}`, includes an action to capitalize next word.
:::

:::{plover:operator} {#}
Does nothing. This is a null or cancelled outline, which doesn't affect
formatting, doesn't output anything, and cannot be undone with the asterisk key.
It effectively does nothing but show up in logs.
:::

## Word Boundaries

It's possible to select a different translation for an outline depending on
whether the previous word was finished.

Given the dictionary:

```json
{
  "S": "word",
  "/S": "{prefix^}"
}
```

with an initial stroke `S`, the translation `"/S": "{prefix^}"` is chosen;
unless the previous word is not finished (for example if the previous
translation is `{con^}`), then the translation `"S": "word"` is chosen.

:::{plover:operator} {$}; {:word_end}
Explicitly marks a translation as finished.
:::

## Control Commands

The following commands control Plover's behavior. Some of them are already
defined in the base `commands.json` dictionary; the provided outlines are listed
below.

Commands are case-insensitive, so `{plover:toggle}`, `{PLOVER:TOGGLE}`, and
even `{Plover:ToGGlE}` all resolve to the same command.

:::{plover:command} suspend
Stops Plover's output. If you are using a keyboard, you will be able to type
normally again; any other machine will not output anything.

_Default outline_: PHRO\*F ("**PL**over **OFF**")
:::

:::{plover:command} resume
Enables Plover's output. This command can be executed while the engine is
disabled, so it can be written on a keyboard to turn steno mode on as well.

_Default outline_: `PHRO*PB` ("**PL**over **ON**")
:::

:::{plover:command} toggle
Toggles between steno output being enabled and disabled.

_Default outline_: `PHROLG` ("**PL**over t**OGGL**e")
:::

:::{plover:command} add_translation
Opens a translation window where you can enter a stroke and translation text to create a new dictionary entry.

_Default outline_: `TKUPT` ("**D**ictionary **UP**da**T**e")
:::

:::{plover:command} lookup
Opens a search dialog that you can write a translation into to get a list of
outlines in your dictionaries.

_Suggested outline_: `PHR*UP` ("**PL**over look**UP**") or `PHRAOBG` ("**PL**over **LOOK**up")
:::

:::{plover:command} suggestions
Opens and focuses Plover's suggestions window which will suggest alternative
outlines for your most recent outputs.

_Suggested outline_: `PHROGS` ("**PL**over sugges**TION**")
:::

:::{plover:command} configure
Opens and focuses Plover's configuration window.

_Suggested outline_: `PHROFG` ("**PL**over con**F**i**G**")
:::

:::{plover:command} focus
Opens and focuses the main Plover window.

_Suggested outline_: `PHROFBGS` ("**PL**over **F**o**C**u**S**")
:::

:::{plover:command} quit
Quits Plover.

_Suggested outline_: `PHROBGT` ("**PL**over **Q**ui**T**")
:::

::::{plover:command} set_config:arg
Sets Plover configuration options. `arg` is a comma-separated list of
[config key-value pairs](config-keys), for example:

```
"start_attached": True, "start_capitalized": True
```

The quotes and colons are mandatory, and the values must be valid Python
expressions.

This command also reloads all changed dictionaries. Run this command without
arguments to _just_ reload dictionaries without changing any config options.
::::

## Plugins

Plugins may provide some commands, metas, or macros. Consult each plugin's
documentation to find out what type of operator they add, and what arguments
they take, if any.

:::{plover:command} command; command:arg
Run the command named `command`, with the argument if specified. Note that
the `plover` prefix is mandatory; even if it is not a built-in Plover command,
the operator name in the translation syntax still starts with `plover:`.
:::

:::{plover:operator} {:[meta]}; {:[meta]:[arg]}
Run the meta named `meta`, with the argument if specified.
:::

:::{plover:operator} =[macro]; =[macro]:[arg]
Run the macro named `macro`, with the argument if specified.
:::
