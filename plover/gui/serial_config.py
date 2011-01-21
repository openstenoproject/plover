# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""A graphical user interface for configuring a serial port."""

import glob
from serial import Serial
from serial import SerialException
import string
import wx

DIALOG_TITLE = 'Serial Port Configuration'
USE_TIMEOUT_STR = 'Use Timeout'
RTS_CTS_STR = 'RTS/CTS'
XON_XOFF_STR = 'Xon/Xoff'
OK_STR = 'OK'
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
    """Enumerates common available ports on *nix systems."""
    base = '/dev/tty'
    candidates = []
    for port in glob.glob(base + '*'):
        if port == base:
            continue
        try:
            ser = Serial(port=port)
            del ser
            candidates.append(port)
        except SerialException:
            continue
    candidates.sort()
    return candidates

class SerialConfigDialog(wx.Dialog):
    """Serial port configuration dialog."""
    
    def __init__(self,
                 serial,
                 parent,
                 id=wx.ID_ANY,
                 title='', 
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize, 
                 style=wx.DEFAULT_DIALOG_STYLE,
                 name=wx.DialogNameStr):
        """Create a configuration GUI for the given serial port.

        Arguments:

        serial -- A serial.Serial object or an object with the same
        constructor parameters. This object determines the initial
        values of the configuration interface. This is also the object
        to which the configuration values are written when pressing
        the OK button. The object is not changed if the Cancel button
        is pressed.

        parent -- See wx.Dialog.

        id -- See wx.Dialog.

        title -- See wx.Dialog.

        pos -- See wx.Dialog.

        size -- See wx.Dialog.

        style -- See wx.Dialog.

        name -- See wx.Dialog.

        """
        self.serial = serial
        wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)
        self.SetTitle(DIALOG_TITLE)

        # Create components.
        self.port_combo_box = wx.ComboBox(self,
                                          choices=enumerate_ports(),
                                          style=wx.CB_DROPDOWN)
        self.baudrate_choice = wx.Choice(self,
                                         choices=map(str, Serial.BAUDRATES))
        self.databits_choice = wx.Choice(self,
                                         choices=map(str, Serial.BYTESIZES))
        self.stopbits_choice = wx.Choice(self,
                                         choices=map(str, Serial.STOPBITS))
        self.parity_choice = wx.Choice(self,
                                       choices=map(str, Serial.PARITIES))
        self.timeout_checkbox = wx.CheckBox(self, label=USE_TIMEOUT_STR)
        self.timeout_text_ctrl = wx.TextCtrl(self,
                                             value='',
                                             validator=FloatValidator())
        self.rtscts_checkbox = wx.CheckBox(self, label=RTS_CTS_STR)
        self.xonxoff_checkbox = wx.CheckBox(self, label=XON_XOFF_STR)
        ok_button = wx.Button(self, label=OK_STR)
        cancel_button = wx.Button(self, label=CANCEL_STR)
        ok_button.SetDefault()

        # Bind events.
        self.Bind(wx.EVT_BUTTON, self._on_ok, ok_button)
        self.Bind(wx.EVT_BUTTON, self._on_cancel, cancel_button)
        self.Bind(wx.EVT_CHECKBOX,
                  self._on_timeout_select,
                  self.timeout_checkbox)

        # Layout components.
        global_sizer = wx.BoxSizer(wx.VERTICAL)

        static_box = wx.StaticBox(self, label=CONNECTION_STR)
        outline_sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=PORT_STR),
                    proportion=1,
                    flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                    border=LABEL_BORDER)
        sizer.Add(self.port_combo_box)
        outline_sizer.Add(sizer, flag=wx.EXPAND)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=BAUDRATE_STR),
                  flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL,
                  border=LABEL_BORDER)
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
        sizer.Add(self.databits_choice, proportion=3, flag=wx.ALIGN_RIGHT)
        outline_sizer.Add(sizer, flag=wx.EXPAND)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=STOP_BITS_STR),
                  proportion=5,
                  flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL,
                  border=LABEL_BORDER)
        sizer.Add(self.stopbits_choice, proportion=3, flag=wx.ALIGN_RIGHT)
        outline_sizer.Add(sizer, flag=wx.EXPAND)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=PARITY_STR),
                  proportion=5,
                  flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                  border=LABEL_BORDER)
        sizer.Add(self.parity_choice, proportion=3, flag=wx.ALIGN_RIGHT)
        outline_sizer.Add(sizer, flag=wx.EXPAND)
        global_sizer.Add(outline_sizer,
                         flag=wx.EXPAND | wx.ALL, border=GLOBAL_BORDER)

        static_box = wx.StaticBox(self, label=TIMEOUT_STR)
        outline_sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)
        outline_sizer.Add(self.timeout_checkbox,
                          flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL,
                          border=LABEL_BORDER)
        outline_sizer.Add(self.timeout_text_ctrl)
        outline_sizer.Add(wx.StaticText(self, label=SECONDS_STR),
                          flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL,
                          border=LABEL_BORDER)
        global_sizer.Add(outline_sizer, flag=wx.ALL, border=GLOBAL_BORDER)

        static_box = wx.StaticBox(self, label=FLOW_CONTROL_STR)
        outline_sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)
        outline_sizer.Add(self.rtscts_checkbox,
                          flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL,
                          border=LABEL_BORDER)
        outline_sizer.Add(self.xonxoff_checkbox,
                          flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL,
                          border=LABEL_BORDER)
        outline_sizer.Add((10,10), proportion=1, flag=wx.EXPAND)
        global_sizer.Add(outline_sizer,
                         flag=wx.EXPAND | wx.ALL,
                         border=GLOBAL_BORDER)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(ok_button)
        sizer.Add(cancel_button)
        global_sizer.Add(sizer,
                         flag=wx.ALL | wx.ALIGN_RIGHT,
                         border=GLOBAL_BORDER)

        self.SetAutoLayout(True)
        self.SetSizer(global_sizer)
        global_sizer.Fit(self)
        global_sizer.SetSizeHints(self)
        self.Layout()
        self._update()
        
    def _update(self):
        # Updates the GUI to reflect the current data model.
        if self.serial.port is not None:
            self.port_combo_box.SetValue(str(self.serial.port))
        else:
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

    def _on_ok(self, events):
        # Transfer the configuration values to the serial port object.
        self.serial.port = self.port_combo_box.GetValue()
        self.serial.baudrate = int(self.baudrate_choice.GetStringSelection())
        self.serial.bytesize = int(self.databits_choice.GetStringSelection())
        self.serial.stopbits = int(self.stopbits_choice.GetStringSelection())
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

    def _on_cancel(self, events):
        # Dismiss the dialog without making any changes.
        self.EndModal(wx.ID_CANCEL)

    def _on_timeout_select(self, events):
        # Dis/allow user input to timeout text control.
        if self.timeout_checkbox.GetValue():
            self.timeout_text_ctrl.Enable(True)
        else:
            self.timeout_text_ctrl.Enable(False)


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
        ser = Serial()
        print 'Before:', ser
        serial_config_dialog = SerialConfigDialog(ser, None)
        self.SetTopWindow(serial_config_dialog)
        result = serial_config_dialog.ShowModal()
        print 'After:', ser
        print 'Result:', result
        self.ExitMainLoop()
        return True

if __name__ == "__main__":
    app = TestApp(0)
    app.MainLoop()
