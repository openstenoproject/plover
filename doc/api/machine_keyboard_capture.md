# `plover.machine.keyboard_capture` -- Keyboard capture

```{py:module} plover.machine.keyboard_capture

```

This module provides a skeleton for implementing keyboard input to grab steno
keystrokes. This is typically platform-specific, so actual implementations
are contained in platform-specific {mod}`oslayer<plover.oslayer>` modules.

````{class} Capture
Encapsulates logic for capturing keyboard input. An instance of this is
used internally by Plover's built-in keyboard plugin.

Define the {meth}`key_down` and {meth}`key_up` methods below to implement
custom behavior that gets executed when a key is pressed or released.

```{method} start()
Start collecting keyboard input.
```

```{method} cancel()
Stop collecting keyboard input.
```

```{method} suppress([suppressed_keys: List[str] = ()])
Suppresses the specified keys, preventing them from returning any
output through regular typing. This allows us to intercept keyboard
events when using keyboard input.
```

The following methods are available to implementors to hook into the
keyboard capture system:

```{method} key_down(key: str)
Notifies Plover that a key was pressed down.
```

```{method} key_up(key: str)
Notifies Plover that a key was released.
```
````
