# `plover.oslayer.log` -- User-facing notifications

This module provides a log handler for displaying critical notifications in the
system GUI.

```{py:module} plover.oslayer.log

```

```{class} NotificationHandler
A `logging.StreamHandler` that emits system notifications.

* On Windows, uses [Plyer](https://pypi.org/project/plyer/).
* On macOS, uses [`NSUserNotificationCenter`](https://developer.apple.com/documentation/foundation/nsusernotificationcenter).
* On Linux and BSD, uses DBus.

By default, this emits only notifications of level `WARNING` or higher.
```
