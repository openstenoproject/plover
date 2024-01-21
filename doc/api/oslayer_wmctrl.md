# `plover.oslayer.wmctrl` -- Window management

This module provides wrappers for platform-specific window management functions.

```{py:module} plover.oslayer.wmctrl
```

```{function} GetForegroundWindow()
Return the process ID (PID) of the program that currently has the
frontmost window on the screen.
```

```{function} SetForegroundWindow(pid)
Allow the program with the specified PID to display the frontmost window.
```
