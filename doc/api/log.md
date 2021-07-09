# `plover.log` -- Logging

```{py:module} plover.log
```

This module provides logging functionality, with an API based on that of the
built-in [`logging`](https://docs.python.org/3/library/logging.html) module.

````{class} Logger
Initializes a logger with a handler that outputs to the console. A {class}`Logger`
may also log to a file, and may also log strokes and translations if enabled.

```{method} set_level(level: int)
Sets the minimum log level to emit messages to the print and file
handlers.
```

```{method} setup_logfile()
Sets up a log handler that saves logs to a file in the configuration
directory, rotating log files as needed.
```

```{method} setup_platform_handler()
Sets up a platform-specific GUI notification handler. This sets up a
a DBus handler on Linux, a Notification Center handler on macOS, and a
[Plyer](https://github.com/kivy/plyer) handler on Windows. Platform-specific handlers are expected to
emit log messages of at least `WARNING` severity.

If a handler has already been set up, this does nothing.
```

```{method} has_platform_handler()
Returns whether a platform handler has been set up.
```

```{method} set_stroke_filename([filename: str = None])
Sets the name of the file to save stroke and translation logs to, and
sets up stroke and translation handling.
```

```{method} enable_stroke_logging(enable: bool)
If `enable` is `True`, enable logging strokes; otherwise, disable it.
```

```{method} enable_translation_logging(enable: bool)
If `enable` is `True`, enable logging translations; otherwise,
disable it.
```

```{method} log_stroke(stroke: plover.steno.Stroke)
Logs `stroke` to the stroke log file. Does nothing if the stroke
logging handler is not set up, or stroke logging is disabled.
```

```{method} log_translation(undo, do, prev)
```

Aside from the methods above, the typical
[`logging.Logger`](https://docs.python.org/3/library/logging.html#logging.Logger) methods can
be used, such as `info` and `add_handler`.
````

In addition to the {class}`Logger` class above, the following module-level
functions are also available for convenience:

```{data} __logger
:type: Logger

The global Plover logger instance. You should typically not have to
access this directly; most use cases can be handled by the functions below.
```

```{function} debug(msg, *args, **kwargs)
Logs at a `DEBUG` log level by calling `__logger.debug`.
```

```{function} info(msg, *args, **kwargs)
Logs at an `INFO` log level by calling `__logger.info`.
```

```{function} warning(msg, *args, **kwargs)
Logs at a `WARNING` log level by calling `__logger.warning`.
```

```{function} error(msg, *args, **kwargs)
Logs at an `ERROR` log level by calling `__logger.error`.
```

```{function} stroke(stroke)
Logs `stroke` by calling `__logger.log_stroke`.
```

```{function} translation(undo, do, prev)
Logs the translation by calling `__logger.log_translation`.
```

```{function} set_level(level)
Sets the minimum log level for `__logger`.
```

```{function} add_handler(handler)
Adds a log handler to `__logger`.
```

```{function} remove_handler(handler)
Removes a log handler from `__logger`.
```

```{function} setup_logfile()
Sets up file logging for `__logger`.
```

```{function} setup_platform_handler()
Calls `__logger.setup_platform_handler`.
```

```{function} has_platform_handler()
Calls `__logger.has_platform_handler`.
```

```{function} set_stroke_filename([filename=None])
Sets the filename to log strokes to for `__logger`.
```

```{function} enable_stroke_logging(enable)
Enable or disable stroke logging for `__logger`.
```

```{function} enable_translation_logging(enable)
Enable or disable translation logging for `__logger`.
```
