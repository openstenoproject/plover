# Top-Level Design

The Plover application has two main components: the engine, which captures
keystroke data from the hardware and translates it into keystrokes
corresponding to the output text; and the user interface, which provides a way
to configure translation and other parts of the engine.

## Engine

The translation process that occurs in the engine is composed of four major
phases: _capture_, _translation_, _formatting_, and _rendering_. Each phase is
controlled by a separate component; the engine connects all of their
outputs according to the program's configuration.

```{figure-md} engine-flow
![Plover engine flow diagram](_static/engine-flow.png)

A diagram of the components involved in translating steno keystrokes to text
in the Plover engine.
```

### Capture

The first phase is **capturing** user input, in the form of either keystrokes
on a standard keyboard or steno stroke data from a steno writer. The exact
method of communication between Plover and the device depends on the hardware.

Capture is performed by a **machine plugin**. Some are already included with
Plover, but others may require installing third-party plugins. Plover has
support for two primary types of protocols:

- **Keyboard**: captures input from a standard computer keyboard, using the USB
  Human Interface Device (HID) protocol.

  Keyboard capture uses operating system APIs to capture keystrokes. As a
  result, the exact implementations will be specific to each platform, and only
  a handful of platforms are supported at this time.

- **Serial**: captures input from steno writers, both hobbyist and professional,
  using UART over a USB connection. Most professional writers will support this
  protocol, and Plover provides native support for most steno protocols.

See [Keyboard Capture & Output](keyboard-capture-output) for more details on
these protocols, and how to implement capture for your protocol or platform.

Once the keystrokes have been captured, the engine is then responsible for
translating _physical_ keys in keystrokes to _logical_ steno keys based on
the active [system](api/system), then sending them to the translator.

### Translation

The **translator** is the second phase of the engine. It receives captured
steno strokes and looks up translations against the user's dictionaries.

The translator has a _buffer_ of previously entered strokes (100 strokes by
default); this allows for multi-stroke outlines to be translated properly,
and for the latest strokes to be undone when the user presses `*` (or whatever
outline translates to the undo operator).

```{todo}
Complete this section.
```

### Dictionaries

```{todo}
Complete this section.
```

#### Macros

```{todo}
Complete this section.
```

### Formatting

The **formatter** is the third phase of the engine. It receives individual
outline translations from the translator, and converts it into a series of
_actions_. Formatting actions consist of:

- **output instructions**, such as text strings, backspaces, or keyboard
  combinations; and

- **state changes**, such as capitalization, or adding or omitting spaces
  between words.

```{todo}
Complete this section.
```

#### Metas

```{todo}
Complete this section.
```

### Rendering

```{todo}
Complete this section.
```

#### Commands

```{todo}
Complete this section.
```

#### Output

```{todo}
Complete this section.
```

### Hooks

The engine communicates with other components, including the user interface
and some plugins, using _hooks_.

Plugins may connect to a hook by calling {meth}`StenoEngine.hook_connect<plover.engine.StenoEngine.hook_connect>`
and providing a callback function:

```python
class MyExtension:
  def __init__(self, engine: plover.engine.StenoEngine):
    self.engine = engine

  def start(self):
    # Connect to the "stroked" hook
    self.engine.hook_connect("stroked", self._on_stroked)

  def _on_stroked(self, stroke: plover.steno.Stroke):
    ...  # Gets called after each stroke
```

Events that occur within the Plover engine, such as machine disconnections,
stroke inputs, and configuration changes, trigger these hooks, which in turn
call the callback functions.

[Engine Hooks](engine-hooks) provides the full list of available hooks.

## User Interface

```{todo}
Complete this section.
```
