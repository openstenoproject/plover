v4.0.0.dev9 (2020-10-17)
========================
Features
--------

Core
~~~~

- A new ``SET_CONFIG`` command can be used to change the configuration with a stroke, e.g.::

          "O*EP": "{PLOVER:SET_CONFIG:'translation_frame_opacity':100}",
          "TR*PB": "{PLOVER:SET_CONFIG:'translation_frame_opacity':0}",

  to change the opacity of the "Add Translation" dialog on the fly. (#989)
- Speed up loading dictionaries. (#1022)
- Be more restrictive with macro names: only accept valid identifier, so for example ``==`` is not handled like a macro anymore. (#1025)
- Ignore case when processing builtin commands / metas. (#1069)
- Add user friendly names for built-in metas, e.g.: ``{:retro_case:cap_first_word}``, ``{:retro_currency:$c}``, ``{:attach:attach^}``, etc... (#1069)
- The configuration is now automatically saved on change, rather than on exit. (#1123)


User Interface
~~~~~~~~~~~~~~

- Add menu entry for opening the configuration directory ("File" => "Open config folder"). (#981)
- Automatically focus the input field and pre-select the previous input when the lookup window is activated. (#1009)
- Improve the configuration dialog for serial machines: automatically scan available ports and default to the first one. (#1036)
- The "Add translation" stroke lookup now returns entries for all enabled dictionaries and is debounced to improve performance. (#1084)


Linux
~~~~~

- The distribution Python is now built with optimization. (#1068)
- Expand the list of supported key names in key combos to include non-US specific keys (like ``ISO_Level3_Shift``). (#1082)
- The default configuration directory on Linux is now ``~/.config/plover`` (``~/.local/share/plover`` is still supported for backward compatibility). (#1123)


Windows
~~~~~~~

- The distribution is now 64bits. (#1023)


Bugfixes
--------

Core
~~~~

- Fix retrospective insert space macro when the previous translation involved suffix keys. (#995)
- Fix updating a dictionary mapping: ensure reverse lookups data stays consistent. (#1022)
- Fix keymap validation: properly fallback to default keymap when invalid. (#1065)
- Fix lookups by translation: do not ignore lower priority dictionaries when a match is found in a higher priority one. (#1066)
- Fix wordlist support for system plugins: try loading from the system dictionaries root (and not Plover assets directory). (#1116)
- Configuration save operations are now atomic. (#1123)
- Fix forced lowercasing of all engine command arguments. (#1139)


Dictionaries
~~~~~~~~~~~~

- Fix a number of invalid entries in the main dictionary. (#1038)
- Tweak orthographic rules so "reduce/{^ability}" result in "reducibility" instead of "reducability". (#1096)


User Interface
~~~~~~~~~~~~~~

- Fix a possible crash on close when opening a read-only dictionary in the editor. (#897)
- Fix possible crash when changing machine parameters in the configuration dialog. (#1041)
- Fix internationalization of machine types in the configuration dialog. (#1061)
- Fix tools shortcuts. (#1062)
- Fix crashes due to GUI exceptions reaching the event loop. (#1135)


macOS
~~~~~

- Fix an issue where permissions had to be granted to "env" on macOS Catalina 10.15. (#1152)


Windows
~~~~~~~

- Fix Unicode characters output. (#991)
- Fix installer's icon. (#1027)


API
---

Breaking Changes
~~~~~~~~~~~~~~~~

- ``StenoDictionaryCollection.casereverse_lookup`` now returns a ``set`` (instead of a ``list``). (#1066)


v4.0.0.dev8+66.g685bd33 (2018-07-02)
====================================


Features
--------

Dictionaries
~~~~~~~~~~~~

- Use ``AOE`` instead of ``E`` for prefix "e". (#951)
- Quality of Life changes/additions to the dictionaries. (#959, #960)


User Interface
~~~~~~~~~~~~~~

- Add tooltips to dictionary status icons. (#962)


Bugfixes
--------

Core
~~~~

- Fix issues when output is set to "Spaces After". (#965)


macOS
~~~~~

- Fix portable mode. (#932)


Windows
~~~~~~~

- Add missing C++ redistributable DLL to the installer. (#957)
- Fix emoji output. (#942)
