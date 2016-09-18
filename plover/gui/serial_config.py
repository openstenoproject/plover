# coding: utf-8
# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.


"""A graphical user interface for configuring a serial port."""

from serial import Serial
from serial.tools.list_ports import comports
import string
import wx
import wx.animate
from wx.lib.utils import AdjustRectToScreen
from threading import Thread

from plover.config import SPINNER_FILE

DIALOG_TITLE = 'Serial Port Configuration'
USE_TIMEOUT_STR = 'Use Timeout'
RTS_CTS_STR = 'RTS/CTS'
XON_XOFF_STR = 'Xon/Xoff'
OK_STR = 'OK'
SCAN_STR = "Scan"
LOADING_STR = u"Scanning ports…"
CANCEL_STR = 'Cancel'
CONNECTION_STR = 'Connection'
PORT_STR = 'Port'
BAUDRATE_STR = 'Baudrate'
DATA_FORMAT_STR = 'Data Format'
DATA_BITS_STR = 'Data Bits'
STOP_BITS_STR = 'Stop Bits'
PARITY_STR = 'Parity'
TIMEOUT_STR = 'Timeout'
SECONDS_STR = 'seconds'
FLOW_CONTROL_STR = 'Flow Control'
LABEL_BORDER = 4
GLOBAL_BORDER = 4


def enumerate_ports():
    """Enumerates available ports"""
    return sorted(x[0] for x in comports())

class SerialConfigDialog(wx.Dialog):
    """Serial port configuration dialog."""

    def __init__(self, serial, parent, config):
        """Create a configuration GUI for the given serial port.

        Arguments:

        serial -- An object containing all the current serial options. This 
        object will be modified when pressing the OK button. The object will not 
        be changed if the cancel button is pressed.

        parent -- See wx.Dialog.
        
        config -- The config object that holds plover's settings.

        """
        self.config = config
        pos = (config.get_serial_config_frame_x(), 
               config.get_serial_config_frame_y())
        wx.Dialog.__init__(self, parent, title=DIALOG_TITLE, pos=pos)

        self.serial = serial

        # Create and layout components. Components must be created after the 
        # static box that contains them or they will be unresponsive on OSX.

        global_sizer = wx.BoxSizer(wx.VERTICAL)

        static_box = wx.StaticBox(self, label=CONNECTION_STR)
        outline_sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=PORT_STR),
                    proportion=1,
                    flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                    border=LABEL_BORDER)
        self.port_combo_box = wx.ComboBox(self,
                                          choices=[],
                                          style=wx.CB_DROPDOWN)
        sizer.Add(self.port_combo_box, flag=wx.ALIGN_CENTER_VERTICAL)
        self.scan_button = wx.Button(self, label=SCAN_STR)
        sizer.Add(self.scan_button, flag=wx.ALIGN_CENTER_VERTICAL)
        self.loading_text = wx.StaticText(self, label=LOADING_STR)
        sizer.Add(self.loading_text,
                  flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                  border=LABEL_BORDER)
        self.loading_text.Hide()
        self.gif = wx.animate.GIFAnimationCtrl(self, -1, SPINNER_FILE)
        self.gif.GetPlayer().UseBackgroundColour(True)
        # Need to call this so the size of the control is not
        # messed up (100x100 instead of 16x16) on Linux...
        self.gif.InvalidateBestSize()
        self.gif.Hide()
        sizer.Add(self.gif, flag=wx.ALIGN_CENTER_VERTICAL)
        outline_sizer.Add(sizer, flag=wx.EXPAND)
        self.port_sizer = sizer

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=BAUDRATE_STR),
                  flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                  border=LABEL_BORDER)
        self.baudrate_choice = wx.Choice(self,
                                         choices=map(str, Serial.BAUDRATES))
        sizer.Add(self.baudrate_choice, flag=wx.ALIGN_RIGHT)
        outline_sizer.Add(sizer, flag=wx.EXPAND)
        global_sizer.Add(outline_sizer,
                         flag=wx.EXPAND | wx.ALL, border=GLOBAL_BORDER)

        static_box = wx.StaticBox(self, label=DATA_FORMAT_STR)
        outline_sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=DATA_BITS_STR),
                  proportion=5,
                  flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                  border=LABEL_BORDER)
        self.databits_choice = wx.Choice(self,
                                         choices=map(str, Serial.BYTESIZES))
        sizer.Add(self.databits_choice, proportion=3, flag=wx.ALIGN_RIGHT)
        outline_sizer.Add(sizer, flag=wx.EXPAND)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=STOP_BITS_STR),
                  proportion=5,
                  flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                  border=LABEL_BORDER)
        self.stopbits_choice = wx.Choice(self,
                                         choices=map(str, Serial.STOPBITS))
        sizer.Add(self.stopbits_choice, proportion=3, flag=wx.ALIGN_RIGHT)
        outline_sizer.Add(sizer, flag=wx.EXPAND)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=PARITY_STR),
                  proportion=5,
                  flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                  border=LABEL_BORDER)
        self.parity_choice = wx.Choice(self,
                                       choices=map(str, Serial.PARITIES))
        sizer.Add(self.parity_choice, proportion=3, flag=wx.ALIGN_RIGHT)
        outline_sizer.Add(sizer, flag=wx.EXPAND)
        global_sizer.Add(outline_sizer,
                         flag=wx.EXPAND | wx.ALL, border=GLOBAL_BORDER)

        static_box = wx.StaticBox(self, label=TIMEOUT_STR)
        outline_sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)
        self.timeout_checkbox = wx.CheckBox(self, label=USE_TIMEOUT_STR)
        outline_sizer.Add(self.timeout_checkbox,
                          flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                          border=LABEL_BORDER)
        self.timeout_text_ctrl = wx.TextCtrl(self,
                                             value='',
                                             validator=FloatValidator())
        outline_sizer.Add(self.timeout_text_ctrl)
        outline_sizer.Add(wx.StaticText(self, label=SECONDS_STR),
                          flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                          border=LABEL_BORDER)
        global_sizer.Add(outline_sizer, flag=wx.ALL, border=GLOBAL_BORDER)

        static_box = wx.StaticBox(self, label=FLOW_CONTROL_STR)
        outline_sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)
        self.rtscts_checkbox = wx.CheckBox(self, label=RTS_CTS_STR)
        outline_sizer.Add(self.rtscts_checkbox,
                          flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                          border=LABEL_BORDER)
        self.xonxoff_checkbox = wx.CheckBox(self, label=XON_XOFF_STR)
        outline_sizer.Add(self.xonxoff_checkbox,
                          flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                          border=LABEL_BORDER)
        outline_sizer.Add((10, 10), proportion=1, flag=wx.EXPAND)
        global_sizer.Add(outline_sizer,
                         flag=wx.EXPAND | wx.ALL,
                         border=GLOBAL_BORDER)

        self.ok_button = wx.Button(self, label=OK_STR)
        cancel_button = wx.Button(self, label=CANCEL_STR)
        self.ok_button.SetDefault()
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.ok_button)
        sizer.Add(cancel_button)
        global_sizer.Add(sizer,
                         flag=wx.ALL | wx.ALIGN_RIGHT,
                         border=GLOBAL_BORDER)

        # Bind events.
        self.Bind(wx.EVT_BUTTON, self._on_ok, self.ok_button)
        self.Bind(wx.EVT_BUTTON, self._on_cancel, cancel_button)
        self.Bind(wx.EVT_CHECKBOX,
                  self._on_timeout_select,
                  self.timeout_checkbox)
        self.Bind(wx.EVT_BUTTON, self._on_scan, self.scan_button)

        self.SetAutoLayout(True)
        self.SetSizer(global_sizer)
        global_sizer.Fit(self)
        global_sizer.SetSizeHints(self)
        self.Layout()
        self.SetRect(AdjustRectToScreen(self.GetRect()))
        
        self.Bind(wx.EVT_MOVE, self.on_move)
        self.Bind(wx.EVT_CLOSE, self._on_cancel)
        
        self._update()
        self.scan_pending = False
        self.closed = False
        
        if serial.port and serial.port != 'None':
            self.port_combo_box.SetValue(serial.port)
        else:
            self._on_scan()

    def _update(self):
        # Updates the GUI to reflect the current data model.
        if self.serial.port is not None:
            self.port_combo_box.SetValue(str(self.serial.port))
        elif self.port_combo_box.GetCount() > 0:
            self.port_combo_box.SetSelection(0)
        self.baudrate_choice.SetStringSelection(str(self.serial.baudrate))
        self.databits_choice.SetStringSelection(str(self.serial.bytesize))
        self.stopbits_choice.SetStringSelection(str(self.serial.stopbits))
        self.parity_choice.SetStringSelection(str(self.serial.parity))
        if self.serial.timeout is None:
            self.timeout_text_ctrl.SetValue('')
            self.timeout_checkbox.SetValue(False)
            self.timeout_text_ctrl.Enable(False)
        else:
            self.timeout_text_ctrl.SetValue(str(self.serial.timeout))
            self.timeout_checkbox.SetValue(True)
            self.timeout_text_ctrl.Enable(True)
        self.rtscts_checkbox.SetValue(self.serial.rtscts)
        self.xonxoff_checkbox.SetValue(self.serial.xonxoff)

    def _on_ok(self, event):
        # Transfer the configuration values to the serial config object.
        sb = lambda s: int(float(s)) if float(s).is_integer() else float(s)
        self.serial.port = self.port_combo_box.GetValue()
        self.serial.baudrate = int(self.baudrate_choice.GetStringSelection())
        self.serial.bytesize = int(self.databits_choice.GetStringSelection())
        self.serial.stopbits = sb(self.stopbits_choice.GetStringSelection())
        self.serial.parity = self.parity_choice.GetStringSelection()
        self.serial.rtscts = self.rtscts_checkbox.GetValue()
        self.serial.xonxoff = self.xonxoff_checkbox.GetValue()
        if self.timeout_checkbox.GetValue():
            value = self.timeout_text_ctrl.GetValue()
            try:
                self.serial.timeout = float(value)
            except ValueError:
                self.serial.timeout = None
        else:
            self.serial.timeout = None
        self.EndModal(wx.ID_OK)
        self._destroy()
        
    def _on_cancel(self, event):
        # Dismiss the dialog without making any changes.
        self.EndModal(wx.ID_CANCEL)
        self._destroy()

    def _on_timeout_select(self, event):
        # Dis/allow user input to timeout text control.
        if self.timeout_checkbox.GetValue():
            self.timeout_text_ctrl.Enable(True)
        else:
            self.timeout_text_ctrl.Enable(False)
            
    def _on_scan(self, event=None):
        self.scan_button.Hide()
        self.port_combo_box.Hide()
        self.gif.Show()
        self.gif.Play()
        self.loading_text.Show()
        self.ok_button.Disable()
        self.port_sizer.Layout()
        t = Thread(target=self._do_scan)
        t.daemon = True
        self.scan_pending = True
        t.start()

    def _do_scan(self):
        ports = enumerate_ports()
        wx.CallAfter(self._scan_done, ports)

    def _scan_done(self, ports):
        if self.closed:
            self.Destroy()
            return
        self.scan_pending = False
        self.gif.Hide()
        self.gif.Stop()
        self.loading_text.Hide()
        self.scan_button.Show()
        self.port_combo_box.Show()
        self.port_combo_box.Clear()
        self.port_combo_box.AppendItems(ports)
        if self.port_combo_box.GetCount() > 0:
            self.port_combo_box.Select(0)
        self.ok_button.Enable()
        self.port_sizer.Layout()

    def _destroy(self):
        if self.scan_pending:
            self.closed = True
        else:
            self.Destroy()
            
    def on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_serial_config_frame_x(pos[0]) 
        self.config.set_serial_config_frame_y(pos[1])
        event.Skip()

class FloatValidator(wx.PyValidator):
    """Validates that a string can be converted to a float."""

    def __init__(self):
        """Create the validator."""
        wx.PyValidator.__init__(self)
        self.Bind(wx.EVT_CHAR, self._on_char)

    def Clone(self):
        """Return a copy of this validator."""
        return FloatValidator()

    def Validate(self, window):
        """Return True if the window's value is a float, False otherwise.

        Argument:

        window -- The parent of the control being validated.

        """
        value = self.GetWindow().GetValue()
        try:
            float(value)
            return True
        except:
            return False

    def TransferToWindow(self):
        """Trivial implementation."""
        return True

    def TransferFromWindow(self):
        """Trivial implementation."""
        return True

    def _on_char(self, event):
        # Filter text input to ensure value is always a valid float.
        key = event.GetKeyCode()
        char = chr(key)
        current_value = self.GetWindow().GetValue()
        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return
        if ((char in string.digits) or
            (char == '.' and char not in current_value)):
            event.Skip()
            return
        if not wx.Validator_IsSilent():
            wx.Bell()
        return


class TestApp(wx.App):
    """A test application that brings up a SerialConfigDialog.

    Serial port information is printed both before and after the
    dialog is dismissed.
    """
    def OnInit(self):
        class SerialPort(object):
            def __init__(self):
                self.__dict__.update({
                    'port': None,
                    'baudrate': 9600,
                    'bytesize': 8,
                    'parity': 'N',
                    'stopbits': 1,
                    'timeout': 2.0,
                    'xonxoff': False,
                    'rtscts': False,
                })
        class SerialConfig(object):
            def get_serial_config_frame_x(self):
                return 200
            def get_serial_config_frame_y(self):
                return 100
        ser = SerialPort()
        cfg = SerialConfig()
        print 'Before:', ser.__dict__
        serial_config_dialog = SerialConfigDialog(ser, None, cfg)
        self.SetTopWindow(serial_config_dialog)
        result = serial_config_dialog.ShowModal()
        print 'After:', ser.__dict__
        print 'Result:', result
        return True

if __name__ == "__main__":
    app = TestApp(0)
    app.MainLoop()
