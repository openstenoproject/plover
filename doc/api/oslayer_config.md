# `plover.oslayer.config` -- Platform-specific configuration

This module provides platform-specific information like paths to configuration
files and asset directories.

```{py:module} plover.oslayer.config

```

```{data} PLATFORM
:type: str

The platform Plover is running on; one of `win`, `mac`, `bsd` or
`linux`.
```

```{data} PLUGINS_PLATFORM
:type: str

Same as {data}`PLATFORM`.
```

```{data} PROGRAM_DIR
:type: str

The directory Plover is running from. In most cases, this will be the
directory the Plover executable itself is in, but when running from an app
bundle on macOS, this is the directory `Plover.app` is in.
```

```{data} CONFIG_BASENAME
:type: str

The name of Plover's configuration file. By default this is `plover.cfg`.
```

```{data} CONFIG_DIR
:type: str

The directory containing Plover's configuration.

If the main config file is in the same directory as the program itself,
then Plover is running in *portable mode*, in which case this is equivalent
to the program directory {data}`PROGRAM_DIR`.

Otherwise, the location of this directory depends on the platform:

  * Windows: `%USERPROFILE%\AppData\Local\plover`
  * macOS: `~/Library/Application Support/plover`
  * Linux: `~/.config/plover`
```

```{data} CONFIG_FILE
:type: str

The full path name of the Plover configuration file.
```

```{data} ASSETS_DIR
:type: str

The directory containing Plover's assets, such as icons and dictionaries.
```
