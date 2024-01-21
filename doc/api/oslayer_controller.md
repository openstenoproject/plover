# `plover.oslayer.controller` -- Process management

This module provides a global process lock to ensure that there is only
one instance of Plover running, and forwards any commands received externally
(i.e. from sources other than Plover) to that existing instance.

```{py:module} plover.oslayer.controller
```

````{class} Controller
Creates a handle in the operating system that guarantees there is only one
Plover instance running. On Windows, this takes the form of a named pipe,
e.g. `\\.\pipe\plover`; on Unix platforms it is a Unix domain socket,
e.g. `/tmp/plover_socket`. This handle is destroyed when Plover exits.

If the handle already exists, this tries to send the `focus` command to
the existing instance to surface the main window.

An instance of this class can be used as a context manager:

```
with Controller() as ctrl:
  # Now this is the only Plover instance running
  pass
```

```{attribute} is_owner
:type: bool

`True` if the current process is the only one running.
```

```{method} force_cleanup()
Delete the handle, if possible. This should only be used if the
previous Plover instance did not exit cleanly and the handle still
exists on the system.
```

```{method} send_command(command: str)
Sends `command` to the running Plover instance to be executed.
```
````
