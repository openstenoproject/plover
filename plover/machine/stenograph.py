# -*- coding: utf-8 -*-
# Copyright (c) 2016 Ted Morin & Keith McCready
# See LICENSE.txt for details.

"Thread-based monitoring of the stenograph machine."

import sys
from time import sleep
from plover import log
from plover.machine.base import ThreadedStenotypeBase

# ^ is the "stenomark"
STENO_KEY_CHART = (('^', '#', 'S-', 'T-', 'K-', 'P-'),
                   ('W-', 'H-', 'R-', 'A-', 'O-', '*'),
                   ('-E', '-U', '-F', '-R', '-P', '-B'),
                   ('-L', '-G', '-T', '-S', '-D', '-Z'),
                  )

VENDOR_ID = 0x112b
MAX_OFFSET = 0xFFFFFFFF
HEADER_BYTES = 32
PACKET_ERROR = 0x06
OPEN_FILE = 0x12
READ_BYTES = 0x13

if sys.platform.startswith('win32'):
    from ctypes import *
    from ctypes.wintypes import DWORD, HANDLE, WORD, BYTE
    import uuid

    class GUID(Structure):
        _fields_ = [("Data1", DWORD),
                    ("Data2", WORD),
                    ("Data3", WORD),
                    ("Data4", BYTE * 8)]


    class SP_DEVICE_INTERFACE_DATA(Structure):
      _fields_ = [('cbSize',DWORD),
      ('InterfaceClassGuid', BYTE * 16),
      ('Flags', DWORD),
      ('Reserved', POINTER(c_ulonglong))]

    class USB_Packet(Structure):
        _fields_ = [
            # Hack to pack structure correctly (without importing 'struct')
            ("SyncSeqType", c_ubyte * 8),
            ("uiDataLen", DWORD),
            ("uiFileOffset", DWORD),
            ("uiByteCount", DWORD),
            ("uiParam3", DWORD),
            ("uiParam4", DWORD),
            ("uiParam5", DWORD),
            ("data", c_ubyte * 1024)
        ]  # limiting data to 1024 bytes (should only ask for 512 at a time)

    # Class GUID / UUID for Stenograph USB Writer
    USB_WRITER_GUID = uuid.UUID('{c5682e20-8059-604a-b761-77c4de9d5dbf}')

    # For Windows we directly call Windows API functions
    SetupDiGetClassDevs = windll.setupapi.SetupDiGetClassDevsA
    SetupDiEnumDeviceInterfaces = windll.setupapi.SetupDiEnumDeviceInterfaces
    SetupDiGetInterfaceDeviceDetail = (
        windll.setupapi.SetupDiGetDeviceInterfaceDetailA)
    CreateFile = windll.kernel32.CreateFileA
    ReadFile = windll.kernel32.ReadFile
    WriteFile = windll.kernel32.WriteFile
    CloseHandle = windll.kernel32.CloseHandle
    GetLastError = windll.kernel32.GetLastError

    # USB Writer 'defines'
    INVALID_HANDLE_VALUE = -1
    ERROR_INSUFFICIENT_BUFFER = 122
    USB_NO_RESPONSE = -9
    RT_FILE_ENDED_ON_WRITER = -8

    class WindowsStenographMachine(object):
        def __init__(self):
            # Allocate memory for sending and receiving USB data
            self._host_packet = USB_Packet()
            self._writer_packet = USB_Packet()

            self._sequence_number = 0
            self._connected = False
            self._usb_device = HANDLE(0)

        @staticmethod
        def _open_device_instance(device_info, guid):
            dev_interface_data = SP_DEVICE_INTERFACE_DATA()
            dev_interface_data.cbSize=sizeof(dev_interface_data)

            status = SetupDiEnumDeviceInterfaces(
                device_info, None, guid.bytes, 0, byref(dev_interface_data))
            if status == 0:
                return INVALID_HANDLE_VALUE

            request_length = DWORD(0)
            # Call with None to see how big a buffer we need for detail data.
            SetupDiGetInterfaceDeviceDetail(
                device_info,
                byref(dev_interface_data),
                None,
                0,
                pointer(request_length),
                None
            )
            error = GetLastError()
            if error != ERROR_INSUFFICIENT_BUFFER:
                return INVALID_HANDLE_VALUE

            characters = request_length.value

            class PSP_INTERFACE_DEVICE_DETAIL_DATA(Structure):
                _fields_ = [('cbSize', DWORD),
                            ('DevicePath', c_char * characters)]
            dev_detail_data = PSP_INTERFACE_DEVICE_DETAIL_DATA()
            dev_detail_data.cbSize = 5  # DWORD + 4 byte pointer

            # Now put the actual detail data into the buffer
            status = SetupDiGetInterfaceDeviceDetail(
                device_info, byref(dev_interface_data), byref(dev_detail_data),
                characters, pointer(request_length), None
            )
            if not status:
                return INVALID_HANDLE_VALUE
            return CreateFile(
                dev_detail_data.DevicePath,
                0xC0000000, 0x3, 0, 0x3, 0x80, 0
            )

        @staticmethod
        def _open_device_by_class_interface_and_instance(classguid):
            device_info = SetupDiGetClassDevs(classguid.bytes, 0, 0, 0x12)
            if device_info == INVALID_HANDLE_VALUE:
                return INVALID_HANDLE_VALUE

            usb_device = WindowsStenographMachine._open_device_instance(
                device_info, classguid)
            return usb_device

        def _usb_open_realtime(self):
            self._host_packet.SyncSeqType[0] = ord('S')
            self._host_packet.SyncSeqType[1] = ord('G')
            self._host_packet.SyncSeqType[2] = self._sequence_number % 255
            self._host_packet.SyncSeqType[6] = OPEN_FILE
            self._host_packet.uiFileOffset = ord('A')
            self._host_packet.data = 'REALTIME.000'.encode('ascii')
            if self._usb_device == INVALID_HANDLE_VALUE:
                return 0
            bytes_written = DWORD(0)

            WriteFile(
                self._usb_device,
                byref(self._host_packet),
                32 + self._host_packet.uiDataLen + len(self._host_packet.data),
                byref(bytes_written),
                None
            )
            return bytes_written.value

        def _usb_write_packet(self):
            self._host_packet.SyncSeqType[0] = ord('S')
            self._host_packet.SyncSeqType[1] = ord('G')
            self._host_packet.SyncSeqType[2] = self._sequence_number % 255
            self._host_packet.SyncSeqType[6] = READ_BYTES
            if self._usb_device == INVALID_HANDLE_VALUE:
                return 0
            bytes_written = DWORD(0)

            WriteFile(
                self._usb_device,
                byref(self._host_packet),
                32 + self._host_packet.uiDataLen,
                byref(bytes_written),
                None
            )
            return bytes_written.value

        def _usb_read_packet(self):
          assert self._usb_device != INVALID_HANDLE_VALUE, 'device not open'

          bytes_read = DWORD(0)
          # Always read this maximum amount.
          # The header will tell me how much to pay attention to.
          ReadFile(
              self._usb_device,
              byref(self._writer_packet),
              32 + 1024,
              byref(bytes_read),
              None
          )
          if bytes_read.value == 0:
            return 0
          if bytes_read.value < 32:  # returned without a full packet
            return 0
          return 32 + self._writer_packet.uiDataLen

        def _read_steno(self, file_offset):
            self._host_packet.SyncSeqType[6] = READ_BYTES
            self._host_packet.uiDataLen = 0
            self._host_packet.uiParam3 = 0
            self._host_packet.uiParam4 = 0
            self._host_packet.uiParam5 = 0
            self._host_packet.uiFileOffset = file_offset
            self._host_packet.uiByteCount = 512
            if self._usb_write_packet() == 0:
                return USB_NO_RESPONSE

            # listen for response
            amount_read = self._usb_read_packet()

            if amount_read > 0:
                amount_read -= HEADER_BYTES
            else:
                # No bytes means we've probably disconnected.
                return USB_NO_RESPONSE

            # If the sequence number is not the same it is junk
            if (self._writer_packet.SyncSeqType[2] ==
                    self._host_packet.SyncSeqType[2]):
                self._sequence_number += 1

                if self._writer_packet.SyncSeqType[6] == READ_BYTES:
                    return self._writer_packet.uiDataLen
                else:
                    # Could check the error code for more specific errors here
                    if self._writer_packet.SyncSeqType[6] == PACKET_ERROR:
                        return RT_FILE_ENDED_ON_WRITER
            else:
                self._usb_read_packet() # toss out any junk
                return USB_NO_RESPONSE

        def disconnect(self):
            CloseHandle(self._usb_device)
            self._usb_device = INVALID_HANDLE_VALUE

        def connect(self):
            # If already connected, disconnect first.
            if self._usb_device != INVALID_HANDLE_VALUE:
                self.disconnect()
            self._usb_device = (
                self._open_device_by_class_interface_and_instance(
                    USB_WRITER_GUID))
            if self._usb_device == INVALID_HANDLE_VALUE:
                return False
            self._usb_open_realtime()
            return True

        def read(self, file_offset):
            result = self._read_steno(file_offset)
            if result > 0:  # Got one or more steno strokes
                return self._writer_packet.data[:result]
            elif not result:
                return []
            elif result == RT_FILE_ENDED_ON_WRITER:
                raise EOFError(
                    'No open file on writer, open file and reconnect')
            elif result == USB_NO_RESPONSE:
                # Prompt a reconnect
                raise IOError('No response from Stenograph device')
    StenographMachine = WindowsStenographMachine
else:
    from usb import core, util

    class LibUSBStenographMachine(object):
        def __init__(self):
            self._usb_device = None
            self._endpoint_in = None
            self._endpoint_out = None
            self._sequence_number = 0
            self._packet = bytearray(
                [0x53, 0x47,  # SG → sync (static)
                 0, 0, 0, 0,  # Sequence number
                 READ_BYTES, 0,  # Action (static)
                 0, 0, 0, 0,  # Data length
                 0, 0, 0, 0,  # File offset
                 0, 0x02, 0, 0,  # Requested byte count (static 512)
                 0, 0, 0, 0,  # Parameter 3
                 0, 0, 0, 0,  # Parameter 4
                 0, 0, 0, 0,  # Parameter 5
                 ]
            )
            self._connected = False

        def connect(self):
            # Disconnect device if it's already connected.
            if self._connected:
                self.disconnect()

            # Find the device by the vendor ID.
            self._usb_device = core.find(idVendor=VENDOR_ID)
            if not self._usb_device:  # Device not found
                return self._connected

            # Copy the default configuration.
            self._usb_device.set_configuration()
            config = self._usb_device.get_active_configuration()
            interface = config[(0, 0)]

            # Get the write endpoint.
            self._endpoint_out = util.find_descriptor(
                interface,
                custom_match=lambda e:
                    util.endpoint_direction(e.bEndpointAddress) ==
                    util.ENDPOINT_OUT)
            assert self._endpoint_out is not None, 'cannot find write endpoint'

            # Get the read endpoint.
            self._endpoint_in = util.find_descriptor(
                interface,
                custom_match=lambda e:
                    util.endpoint_direction(e.bEndpointAddress) ==
                    util.ENDPOINT_IN)
            assert self._endpoint_in is not None, 'cannot find read endpoint'

            self._connected = True
            return self._connected

        def disconnect(self):
            self._connected = False
            util.dispose_resources(self._usb_device)
            self._usb_device = None
            self._endpoint_in = None
            self._endpoint_out = None

        def read(self, file_offset):
            assert self._connected, 'cannot read from machine if not connected'
            self._sequence_number = (self._sequence_number + 1) % MAX_OFFSET
            for i in range(4):
                self._packet[2 + i] = self._sequence_number >> 8 * i & 255
            for i in range(4):
                self._packet[12 + i] = file_offset >> 8 * i & 255
            try:
                self._endpoint_out.write(self._packet)
                response = self._endpoint_in.read(1024, 3000)
            except core.USBError:
                raise IOError('Machine read or write failed')
            else:
                if response and len(response) >= HEADER_BYTES:
                    writer_action = response[6]
                    if writer_action == PACKET_ERROR:
                        raise EOFError(
                            'No open file on writer, open file and reconnect')
                    elif writer_action == READ_BYTES:
                        return response[HEADER_BYTES:]
                return response
    StenographMachine = LibUSBStenographMachine


class Stenograph(ThreadedStenotypeBase):

    KEYS_LAYOUT = '''
        #  #  #  #  #  #  #  #  #  #
        S- T- P- H- * -F -P -L -T -D
        S- K- W- R- * -R -B -G -S -Z
              A- O-   -E -U
        ^
    '''
    KEYMAP_MACHINE_TYPE = 'Stentura'

    def __init__(self, params):
        super(Stenograph, self).__init__()
        self._machine = StenographMachine()

        # State variables used while reading steno from machine
        """
        Stenograph writers have "files" which are indexed from 0.
        Each line is a stroke. When the machine is connected, we
        don't know what stroke the stenographer is on. We can't
        assume zero because there may already be content from before.
        Strategy is to read up the indexes until we reach zero. Then,
        we consider ourselves "realtime" and further data should be
        interpreted.
        """
        self._realtime = False
        """
        There is a bug in the stenograph firmware. After the steno
        "file" is closed on the machine, we receive a flag to tell us.
        However, straight after we start receiving 0 length responses,
        which are the same format as what we'd usually use to tell whether
        the machine is in realtime or not. If the stenographer opens a file
        that has previous content in it, we will then blurt out all that
        content.

        The strategy here is to take note of the first response that is exactly
        8 bytes -- a single stroke -- before beginning output. Combined with the
        0 length stroke check, hopefully we will not accidentally read back and
        blurt an entire steno file."""
        self._read_exactly_8 = False
        self._file_offset = 0

    def _on_stroke(self, keys):
        steno_keys = self.keymap.keys_to_actions(keys)
        if steno_keys:
            self._notify(steno_keys)

    def start_capture(self):
        self.finished.clear()
        self._initializing()
        """Begin listening for output from the stenotype machine."""
        if not self._connect_machine():
            log.warning('Stenograph machine is not connected')
            self._error()
        else:
            self._ready()
            self.start()

    def _connect_machine(self):
        connected = False
        try:
            connected = self._machine.connect()
        except ValueError:
            log.warning('Stenograph: libusb must be installed.')
            self._error()
        except AssertionError as e:
            log.warning('Error connecting: %s', str(e))
            self._error()
        finally:
            return connected

    def _reconnect(self):
        self._initializing()
        connected = False
        while not self.finished.isSet() and not connected:
            sleep(0.25)
            connected = self._connect_machine()
        return connected

    def _reset_state(self):
        self._realtime = False
        self._read_exactly_8 = False
        self._file_offset = 0

    def run(self):
        self._reset_state()
        while not self.finished.isSet():
            try:
                response = self._machine.read(self._file_offset)
            except IOError as e:
                log.warning(u'Stenograph machine disconnected, reconnecting…')
                log.debug('Stenograph exception: %s', str(e))
                self._reset_state()
                if self._reconnect():
                    log.warning('Stenograph reconnected.')
                    self._ready()
            except EOFError:
                # File ended -- will resume normal operation after new file
                self._reset_state()
            else:
                if response is None:
                    continue
                if not self._read_exactly_8 and len(response) == 8:
                    self._read_exactly_8 = True
                content = len(response) > 0
                self._file_offset += len(response)
                if not self._realtime and not content:
                    self._realtime = True
                elif self._realtime and content and self._read_exactly_8:
                    chords = Stenograph.process_steno_packet(response)
                    for keys in chords:
                        if keys:
                            self._on_stroke(keys)
        self._machine.disconnect()

    def stop_capture(self):
        """Stop listening for output from the stenotype machine."""
        super(Stenograph, self).stop_capture()
        self._machine = None
        self._stopped()

    @staticmethod
    def process_steno_packet(steno):
        # Expecting 8 byte chords.
        # Bytes 0-3 are steno, 4-7 are timestamp.
        chords = []
        for chord_index in range(len(steno) // 8):
            keys = []
            chord = steno[chord_index * 8: chord_index * 8 + 4]
            for byte_number, byte in enumerate(chord):
                if byte is None:
                    continue
                byte_keys = STENO_KEY_CHART[byte_number]
                for i in range(6):
                    if (byte >> i) & 1:
                        key = byte_keys[-i + 5]
                        if key:
                            keys.append(key)
            if keys:
                chords.append(keys)
        return chords
