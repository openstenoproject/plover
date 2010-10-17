# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

import glob
from serial import Serial
from serial import SerialException
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
TIMEOUT_VALUE_ERROR_STR = 'Timeout must be a numeric value'
TIMEOUT_VALUE_ERROR_TITLE = 'Value Error'
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
        self.serial = serial
        wx.Dialog.__init__(self, parent, id, title, pos, size, style, name)
        self.SetTitle(DIALOG_TITLE)

        # Create components.
        self.combo_box_port = wx.ComboBox(self,
                                          choices=enumerate_ports(),
                                          style=wx.CB_DROPDOWN)
        self.choice_baudrate = wx.Choice(self,
                                         choices=map(str, Serial.BAUDRATES))
        self.choice_databits = wx.Choice(self,
                                         choices=map(str, Serial.BYTESIZES))
        self.choice_stopbits = wx.Choice(self,
                                         choices=map(str, Serial.STOPBITS))
        self.choice_parity = wx.Choice(self,
                                       choices=map(str, Serial.PARITIES))
        self.checkbox_timeout = wx.CheckBox(self, label=USE_TIMEOUT_STR)
        self.text_ctrl_timeout = wx.TextCtrl(self, value='')
        self.checkbox_rtscts = wx.CheckBox(self, label=RTS_CTS_STR)
        self.checkbox_xonxoff = wx.CheckBox(self, label=XON_XOFF_STR)
        button_ok = wx.Button(self, label=OK_STR)
        button_cancel = wx.Button(self, label=CANCEL_STR)
        button_ok.SetDefault()

        # Bind events.
        self.Bind(wx.EVT_BUTTON, self.on_ok, button_ok)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, button_cancel)
        self.Bind(wx.EVT_CHECKBOX,
                  self.on_timeout_select,
                  self.checkbox_timeout)

        # Layout components.
        global_sizer = wx.BoxSizer(wx.VERTICAL)

        static_box = wx.StaticBox(self, label=CONNECTION_STR)
        outline_sizer = wx.StaticBoxSizer(static_box, wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=PORT_STR),
                    proportion=1,
                    flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                    border=LABEL_BORDER)
        sizer.Add(self.combo_box_port)
        outline_sizer.Add(sizer, flag=wx.EXPAND)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=BAUDRATE_STR),
                  flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL,
                  border=LABEL_BORDER)
        sizer.Add(self.choice_baudrate, flag=wx.ALIGN_RIGHT)
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
        sizer.Add(self.choice_databits, proportion=3, flag=wx.ALIGN_RIGHT)
        outline_sizer.Add(sizer, flag=wx.EXPAND)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=STOP_BITS_STR),
                  proportion=5,
                  flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL,
                  border=LABEL_BORDER)
        sizer.Add(self.choice_stopbits, proportion=3, flag=wx.ALIGN_RIGHT)
        outline_sizer.Add(sizer, flag=wx.EXPAND)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=PARITY_STR),
                  proportion=5,
                  flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                  border=LABEL_BORDER)
        sizer.Add(self.choice_parity, proportion=3, flag=wx.ALIGN_RIGHT)
        outline_sizer.Add(sizer, flag=wx.EXPAND)
        global_sizer.Add(outline_sizer,
                         flag=wx.EXPAND | wx.ALL, border=GLOBAL_BORDER)

        static_box = wx.StaticBox(self, label=TIMEOUT_STR)
        outline_sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)
        outline_sizer.Add(self.checkbox_timeout,
                          flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL,
                          border=LABEL_BORDER)
        outline_sizer.Add(self.text_ctrl_timeout)
        outline_sizer.Add(wx.StaticText(self, label=SECONDS_STR),
                          flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL,
                          border=LABEL_BORDER)
        global_sizer.Add(outline_sizer, flag=wx.ALL, border=GLOBAL_BORDER)

        wx.StaticBox(self, label=FLOW_CONTROL_STR)
        outline_sizer = wx.StaticBoxSizer(static_box, wx.HORIZONTAL)
        outline_sizer.Add(self.checkbox_rtscts,
                          flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL,
                          border=LABEL_BORDER)
        outline_sizer.Add(self.checkbox_xonxoff,
                          flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL,
                          border=LABEL_BORDER)
        outline_sizer.Add((10,10), proportion=1, flag=wx.EXPAND)
        global_sizer.Add(outline_sizer,
                         flag=wx.EXPAND | wx.ALL,
                         border=GLOBAL_BORDER)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(button_ok)
        sizer.Add(button_cancel)
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
        """Updates the GUI to reflect the current data model."""
        if self.serial.portstr is not None:
            self.combo_box_port.SetValue(str(self.serial.portstr))
        else:
            self.combo_box_port.SetSelection(0)
        self.choice_baudrate.SetStringSelection(str(self.serial.baudrate))
        self.choice_databits.SetStringSelection(str(self.serial.bytesize))
        self.choice_stopbits.SetStringSelection(str(self.serial.stopbits))
        self.choice_parity.SetStringSelection(str(self.serial.parity))
        if self.serial.timeout is None:
            self.checkbox_timeout.SetValue(False)
            self.text_ctrl_timeout.Enable(False)
        else:
            self.checkbox_timeout.SetValue(True)
            self.text_ctrl_timeout.Enable(True)
            self.text_ctrl_timeout.SetValue(str(self.serial.timeout))
        self.checkbox_rtscts.SetValue(self.serial.rtscts)
        self.checkbox_xonxoff.SetValue(self.serial.xonxoff)

    def on_ok(self, events):
        success = True
        self.serial.port = self.combo_box_port.GetValue()
        self.serial.baudrate = int(self.choice_baudrate.GetStringSelection())
        self.serial.bytesize = int(self.choice_databits.GetStringSelection())
        self.serial.stopbits = int(self.choice_stopbits.GetStringSelection())
        self.serial.parity = self.choice_parity.GetStringSelection()
        self.serial.rtscts = self.checkbox_rtscts.GetValue()
        self.serial.xonxoff = self.checkbox_xonxoff.GetValue()
        if self.checkbox_timeout.GetValue():
            try:
                self.serial.timeout = float(self.text_ctrl_timeout.GetValue())
            except ValueError:
                dlg = wx.MessageDialog(self,
                                       TIMEOUT_VALUE_ERROR_STR,
                                       TIMEOUT_VALUE_ERROR_TITLE,
                                       wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                success = False
        else:
            self.serial.timeout = None
        if success:
            self.EndModal(wx.ID_OK)

    def on_cancel(self, events):
        self.EndModal(wx.ID_CANCEL)

    def on_timeout_select(self, events):
        if self.checkbox_timeout.GetValue():
            self.text_ctrl_timeout.Enable(True)
        else:
            self.text_ctrl_timeout.Enable(False)


class TestApp(wx.App):
    """A test application that brings up a SerialConfigDialog.

    Serial port information is printed both before and after the
    dialog is dismissed.
    """
    def OnInit(self):
        ser = Serial()
        print 'Before:', ser
        dialog_serial_cfg = SerialConfigDialog(ser, None)
        self.SetTopWindow(dialog_serial_cfg)
        result = dialog_serial_cfg.ShowModal()
        print 'After:', ser
        print 'Result:', result
        self.ExitMainLoop()
        return True

if __name__ == "__main__":
    app = TestApp(0)
    app.MainLoop()
