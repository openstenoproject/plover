# v4.0.0.dev10 (2021-06-19)

## Features

### Core

- Change behavior when launching Plover and an existing instance is already running: send a `focus` command to the existing instance (to show, raise, and focus the main window). Additionally, a new `plover_send_command` executable/script can be used to send other commands. (#1284)
- Add FreeBSD/OpenBSD support. (#1306)

### Linux

- The oldest Ubuntu LTS release supported by the AppImage is now Ubuntu Bionic (18.04). (#1329)

## Bugfixes

### Core

- Fix 2 corner cases when handling dictionaries:
  - If the class implementation is marked as read-only, then loading from a writable file should still result in a read-only dictionary.
  - Don't allow `clear` on a read-only dictionary. (#1302)
- Don't try to start missing extensions. (#1313)

### User Interface

- Correctly restore a window if it was minimized: fix the `focus` command, and activating a tool window. (#1314)

## API

### Breaking Changes

- The `Engine` constructor now takes an additional parameter: the controller. (#1284)

### New

- Add some new helpers to `plover_build_utils.testing`:
  - `dictionary_test`: torture tests for dictionary implementations.
  - `make_dict`: create a temporary dictionary.
  - `parametrize`: parametrize helper for tracking test data source line numbers. (#1302)


# v4.0.0.dev9 (2021-04-22)

## Features

### Core

- A new `SET_CONFIG` command can be used to change the configuration with a stroke, e.g.:
  ``` json
  "O*EP": "{PLOVER:SET_CONFIG:'translation_frame_opacity':100}",
  "TR*PB": "{PLOVER:SET_CONFIG:'translation_frame_opacity':0}",
  ```
  to change the opacity of the "Add Translation" dialog on the fly. (#989)
- Speed up loading dictionaries. (#1022)
- Be more restrictive with macro names: only accept valid identifier, so for example `==` is not handled like a macro anymore. (#1025)
- Ignore case when processing builtin commands / metas. (#1069)
- Add user friendly names for built-in metas, e.g.: `{:retro_case:cap_first_word}`, `{:retro_currency:$c}`, `{:attach:attach^}`, etc... (#1069)
- Improve orthography rules. (#1092, #1212)
- The configuration is now automatically saved on change, rather than on exit. (#1123)
- Add prefix strokes (syntax `/STROKE`) that will only translate if they are at the beginning of a word. Word endings can be specified with `{:word_end}` or `{$}`. (#1157)
- Add support for conditional formatting (based on the text following a translation): `{=REGEXP/TRANSLATION_IF_FOLLOWING_TEXT_MATCH/TRANSLATION_IF_NOT}` or `{:if_next_matches:REGEXP/TRANSLATION_IF_FOLLOWING_TEXT_MATCH/TRANSLATION_IF_NOT}`. (#1158)

### User Interface

- Add menu entry for opening the configuration directory ("File" =&gt; "Open config folder"). (#981)
- Automatically focus the input field and pre-select the previous input when the lookup window is activated. (#1009)
- Improve the configuration dialog for serial machines: automatically scan available ports and default to the first one. (#1036)
- The "Add translation" stroke lookup now returns entries for all enabled dictionaries and is debounced to improve performance. (#1084)
- Added translation into Spanish. (#1165)
- A new command, `{PLOVER:SUGGESTIONS}`, is available to open the suggestions window with a steno stroke. (#1184)
- Add support for saving dictionaries:
  - save a copy of each selected dictionary
  - merge the selected dictionaries into a new one
  - both operations support converting to another format (#1244)
- Added translation into Dutch. (#1264)
- Added Italian translation. (#1268)

### Linux

- The distribution Python is now built with optimization. (#1068)
- Expand the list of supported key names in key combos to include non-US specific keys (like `ISO_Level3_Shift`). (#1082)
- The default configuration directory on Linux is now `~/.config/plover` (`~/.local/share/plover` is still supported for backward compatibility). (#1123)

### macOS

- The minimum version supported by the macOS bundle is now 10.13 (High Sierra). (#1156)

### Windows

- The distribution is now 64bits. (#1023)

## Bugfixes

### Core

- Fix retrospective insert space macro when the previous translation involved suffix keys. (#995)
- Fix updating a dictionary mapping: ensure reverse lookups data stays consistent. (#1022)
- Fix keymap validation: properly fallback to default keymap when invalid. (#1065)
- Fix lookups by translation: do not ignore lower priority dictionaries when a match is found in a higher priority one. (#1066)
- Fix wordlist support for system plugins: try loading from the system dictionaries root (and not Plover assets directory). (#1116)
- Configuration save operations are now atomic. (#1123)
- Fix forced lowercasing of all engine command arguments. (#1139)
- Fix implicit hyphen handling with numbers only strokes on some theories (e.g. Melani). (#1159)
- Fix unbounded memory use in the lookup functions used by the Suggestions window. (#1188)

### Dictionaries

- Fix a number of invalid entries in the main dictionary. (#1038)
- Tweak orthographic rules so "reduce/{^ability}" result in "reducibility" instead of "reducability". (#1096)

### User Interface

- Fix a possible crash on close when opening a read-only dictionary in the editor. (#897)
- Fix possible crash when changing machine parameters in the configuration dialog. (#1041)
- Fix internationalization of machine types in the configuration dialog. (#1061)
- Fix tools shortcuts. (#1062)
- Fix crashes due to GUI exceptions reaching the event loop. (#1135)
- Fix an exception caused by an incorrect assertion that would prevent enabling and disabling extension plugins if they weren't on the first row. (#1171)
- Fix changes to the list of enabled extension plugins not being saved to the configuration file. (#1230)
- Fix missing translations. (#1248)

### Linux

- Fix output capitalization issue. (#1153)
- Fix a race condition that may freeze Plover while toggling with keyboard input machine. (#1163)

### macOS

- Fix an issue where permissions had to be granted to "env" on macOS Catalina 10.15. (#1152)
- Mac notifications no longer have "Plover" as their title. (#1271)

### Windows

- Fix Unicode characters output. (#991)
- Fix installer's icon. (#1027)

## API

### Breaking Changes

- `StenoDictionaryCollection.casereverse_lookup` now returns a `set` (instead of a `list`). (#1066)
- The API for providing i18n support as been changed: see `doc/i18n.md` for more information. (#1258)

### New

- `plover_build_utils.setup` now provides a new `babel_options` helper for configuring Babel for i18n support. (#1258)


# v4.0.0.dev8+66.g685bd33 (2018-07-02)

## Features

### Dictionaries

- Use `AOE` instead of `E` for prefix "e". (#951)
- Quality of Life changes/additions to the dictionaries. (#959, #960)

### User Interface

- Add tooltips to dictionary status icons. (#962)

## Bugfixes

### Core

- Fix issues when output is set to "Spaces After". (#965)

### macOS

- Fix portable mode. (#932)

### Windows

- Add missing C++ redistributable DLL to the installer. (#957)
- Fix emoji output. (#942)
