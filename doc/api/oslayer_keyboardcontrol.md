# `plover.oslayer.keyboardcontrol` -- Keyboard input and output

This module handles platform-specific operations relating to the keyboard,
both for capturing keyboard input (using the keyboard to write steno) and
keyboard emulation (writing the output from steno translation).

```{py:module} plover.oslayer.keyboardcontrol

```

```{class} KeyboardCapture
A subclass of {class}`plover.machine.keyboard_capture.Capture` encapsulating logic
for capturing keyboard input. An instance of this is used internally by Plover’s
built-in keyboard plugin.
```

```{class} KeyboardEmulation
A subclass of {class}`plover.output.Output` encapsulating logic
for sending keystrokes. Pass an instance of this when initializing the
{class}`StenoEngine<plover.engine.StenoEngine>`.
```
