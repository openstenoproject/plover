# `plover.output` -- Text output handling

```{py:module} plover.output

```

This module provides a skeleton for customizable text output. By default,
Plover only outputs steno translations through keyboard emulation, but through
the output plugin mechanism it can also be made to output through other
means, such as writing to a file or sending it over the network.

````{class} Output

Encapsulates logic for sending keystrokes. Pass an instance of this to
the {class}`StenoEngine<plover.engine.StenoEngine>` when it is initialized.

```{method} send_backspaces(number_of_backspaces: int)
Sends the specified number of backspace keys.
```

```{method} send_string(s: str)
Sends the sequence of keys that would produce the specified string.
```

```{method} send_key_combination(combo_string: str)
Sends the specified key combination. `combo_string` is a string in the
key combo format described in {mod}`plover.key_combo`.
```
````
