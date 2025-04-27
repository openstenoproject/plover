# `plover.oslayer` -- Platform layer

```{py:module} plover.oslayer

```

This is an umbrella package for platform-specific functionality:

```{toctree}
:maxdepth: 1

oslayer_config
oslayer_controller
oslayer_i18n
oslayer_keyboardcontrol
oslayer_log
oslayer_wmctrl
```

````{data} PLATFORM_PACKAGE
:type: Dict[str, str]

A mapping from platforms to platform layer packages.

The keys are platform names, the same as in {data}`PLATFORM<plover.oslayer.config.PLATFORM>`,
and the values are names of subpackages within `plover.oslayer`. For example,
logic specific to macOS systems (for which {data}`PLATFORM<plover.oslayer.config.PLATFORM>` is `mac`)
can be found in `plover.oslayer.osx`, and this is defined as follows:

```python
PLATFORM_PACKAGE = {
  "mac": "osx",
}
```

By adding a platform definition to this mapping, the platform layer logic can
be imported automatically without using the platform name, for example
`plover.oslayer.osx.wmctrl` is imported as `plover.oslayer.wmctrl`, and the
same for every other platform.
````
