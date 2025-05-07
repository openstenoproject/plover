# Hardware Communication

This page covers the details of communication protocols Plover uses to capture
keyboard or steno writer input.

## Keyboard Capture & Output

Three implementations of keyboard capture and output are currently available:

- The **Windows** implementation installs low-level event hooks to listen for
  key presses, and the Win32 API's [`SendInput`](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput) to generate keystrokes.

- The **macOS** implementation uses Quartz's Event Services API: [event taps](https://developer.apple.com/documentation/coregraphics/1454426-cgeventtapcreate)
  to listen for key presses, and [keyboard events](https://developer.apple.com/documentation/coregraphics/1456564-cgeventcreatekeyboardevent)
  to generate keystrokes.

- For **Linux** and **BSD**, there are two implementations. If the display server is `x11`, an implementation based on Xlib's `xinput` is used to
  listen for key presses, and `xtest.fake_input` to generate keystrokes. For all other display servers, for example `wayland`, an implementation based
  on `evdev` is used to listen for key presses, and `uinput` to generate keystrokes. The `uinput` implementation needs to know the keyboard layout of the
  system, which can be configured in the Plover `Output` configuration tap.

Before implementing new keyboard capture and output mechanisms for a new
platform, make sure to set up the [platform layer](platform_layer) for your
platform.

### Capture

New keyboard capture methods can be implemented as a subclass of
{class}`Capture<plover.machine.keyboard_capture.Capture>`; your implementation
should translate platform-specific events into calls to
{meth}`key_down<plover.machine.keyboard_capture.Capture.key_down>` and {meth}`key_up<plover.machine.keyboard_capture.Capture.key_up>`.

```python
class MyKeyboardCapture(Capture):
  def start(self):
    self._thread = threading.Thread(target=self._run)
    self._thread.start()

  def _run(self):
    while True:
      key, pressed = ... # wait for key event

      if pressed:
        self.key_down(key)
      else:
        self.key_up(key)
```

Plover's engine handles translating these calls into steno strokes, as well as
handling keymaps and arpeggiation.

### Output

New keyboard emulation methods can be implemented as a subclass of
{class}`Output<plover.output.Output>`. It _must_ implement all of the methods
specified, by translating them to platform-specific input calls.

```python
class MyKeyboardEmulation(Output):
  def send_backspaces(self, num):
    ...

  def send_string(self, s):
    ...

  def send_key_combination(self, combo):
    ...
```

## Serial Protocols

Plover supports communicating with hobbyist, student, and professional steno
writers through a serial interface. The most common protocols are Gemini PR
for hobbyist writers and Stentura for Stenograph writers, but custom protocols
may be implemented.

The {class}`SerialStenotypeBase<plover.machine.base.SerialStenotypeBase>` class
handles all of the connection establishment and configuration; when
implementing a new serial interface, you only need to define your key layout
and implement a way to parse each packet.

```python
class MySerialMachine(SerialStenotypeBase):
  KEYS_LAYOUT = """
    ...
  """

  def run(self):
    ...
```

## USB-based Protocols

### Stenograph USB
```
Packet format:
--------------
Name:     Size:       Value Range:
----------------------------------
Sync          2 bytes "SG"
Sequence #    4 bytes 0 - 0xFFFFFFFF (will wrap from 0xFFFFFFFF to 0x00000000)
Packet ID     2 bytes As Defined (used as packet type)
Data Length   4 bytes 0 - size (limited in most writers to 65536 bytes)
Parameter 1   4 bytes As Defined
Parameter 2   4 bytes As Defined
Parameter 3   4 bytes As Defined
Parameter 4   4 bytes As Defined
Parameter 5   4 bytes As Defined

Command 0x13 Read Bytes
-----------------------

Request (from PC)
Description   Packet ID   Data Length       Param 1       Param 2     Param 3     Param 4     Param 5
------------------------------------------------------------------------------------------------------
Read Bytes   0x0013       00000000          File Offset   Byte Count  00000000    00000000    00000000

-Parameter 1 contains the file offset from which the writer should start returning bytes (or stroke number * 8 since there are 8 bytes returned per stroke (see details of Response))
-Parameter 2 contains the maximum number of bytes the Host wants the writer to send in response to this request
-The writer will respond to this packet with a successful Read Bytes packet or an Error packet.

Response (from writer)
Description   Packet ID   Data Length       Param 1       Param 2     Param 3     Param 4     Param 5
------------------------------------------------------------------------------------------------------
Read Bytes    0x0013      Number of Bytes   File Offset   00000000    00000000    00000000    00000000

-Parameter 1 contains the file offset from which the writer is returning bytes
-For real-time the data is four bytes of steno and 4 bytes of timestamp - 8 bytes per stroke - repeating for the number of strokes returned.
The format of the eight bytes will be:
-Byte 0: 11^#STKP
-Byte 1: 11WHRAO*
-Byte 2: 11EUFRPB
-Byte 3: 11LGTSDZ
-Bytes 4-7: 'timestamp'
-The steno is in the (very) old SmartWriter format where the top two bits of each of the four bytes are set to 1 and the bottom 6 bits as set according to the keys pressed.
-If the Data Length is zero that indicates there are no more bytes available (real-time).
-If the file has been closed (on the writer) an Error packet (error: FileClosed) will be sent in response to Read Bytes.

Description   Packet ID   Data Length       Param 1       Param 2     Param 3     Param 4     Param 5
------------------------------------------------------------------------------------------------------
Open File     0x0012      Number of Bytes   Disk ID

- Parameter 1 is the disk ID that the file you wish to open is on (disk A for all intents and purposes)
- Data is the filename, probably 'REALTIME.000'
```

## Other Protocols

```{todo}
Complete this section.
```
