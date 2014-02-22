# by Brent Nesbitt
# Feb 21, 2014

"""Display the avg speed, current speed, and  maximum speed for the session, and stroke/word ratio"""
import wx
import threading
import time
from wx.lib.utils import AdjustRectToScreen
from collections import deque

TITLE = 'Plover: Typing Speed'
ON_TOP_TEXT = "Always on top"
UI_BORDER = 4
MAX_SAMPLES = 300
WORD_LENGTH = 5
CURRENT_SPEED_TEXT = "current"
AVERAGE_SPEED_TEXT = "average"
MAX_SPEED_TEXT = "maximum"
RATIO_TEXT = "strokes per word"

class SpeedReportDialog(wx.Dialog):

    other_instances = []
    history = deque(maxlen=MAX_SAMPLES)
    start_time = time.time()
    total_strokes = 0
    total_characters = 0
    maximum_speed = 0

    def __init__(self, parent, config):
        self.disabled=False
        self.start_time = time.time()
        self.config = config
        on_top = config.get_speed_report_on_top()
        style = wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP
        pos = (config.get_speed_report_x(), config.get_speed_report_y())
        wx.Dialog.__init__(self, parent, title=TITLE, style=style, pos=pos)

        self.c_speed_text = wx.StaticText(self, label=CURRENT_SPEED_TEXT+": 0        ")
        self.a_speed_text = wx.StaticText(self, label=AVERAGE_SPEED_TEXT+": 0        ")
        self.m_speed_text = wx.StaticText(self, label=MAX_SPEED_TEXT+": 0        ")
        self.ratio_text = wx.StaticText(self, label=RATIO_TEXT+":           ")

        sizer = wx.BoxSizer(wx.VERTICAL)
        top_line = wx.BoxSizer(wx.HORIZONTAL)
        #second_line = wx.BoxSizer(wx.HORIZONTAL)
        top_line.Add(self.c_speed_text, flag=wx.RIGHT | wx.BOTTOM, border=UI_BORDER)
        top_line.Add(self.a_speed_text, flag=wx.RIGHT | wx.BOTTOM, border=UI_BORDER)
        top_line.Add(self.m_speed_text, flag=wx.RIGHT | wx.BOTTOM , border=UI_BORDER)
        top_line.Add(self.ratio_text, flag=wx.RIGHT | wx.BOTTOM, border=UI_BORDER)

        sizer.Add(top_line)
        #sizer.Add(second_line)

        #box.Add(sizer, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, border=UI_BORDER)

        self.SetSizer(top_line)
        self.SetAutoLayout(True)
        top_line.Layout()
        top_line.Fit(self)

        self.Show()

        self.close_all()
        self.other_instances.append(self)
        self.SetRect(AdjustRectToScreen(self.GetRect()))

        self.Bind(wx.EVT_MOVE, self.on_move)
        self.run()

    def on_move(self, event):
        pos = self.GetScreenPositionTuple()
        self.config.set_speed_report_x(pos[0])
        self.config.set_speed_report_y(pos[1])
        event.Skip()

    def on_close(self, event):
        self.config.set_show_speed_report(False)
        self.other_instances.remove(self)
        self.disabled=True
        event.Skip()

    def run(self):
        if (not self.disabled):
            threading.Timer(1.0, self.run).start()
            wx.CallAfter(self.update_display)

    def update_display(self):
        # called every second
        # add history item & update display
        if self.total_characters<=0:
            #don't start timing until something is typed.  Reset if all erased.
            self.start_time = time.time()
            self.history.clear()
            self.history.append(HistoryItem(self.start_time, 0, 0))
            return
        total_words = self.total_characters/float(WORD_LENGTH)
        current_time = time.time()
        self.history.append(HistoryItem(current_time, self.total_strokes, total_words))
        total_minutes = (current_time-self.start_time)/60
        average_speed = total_words/total_minutes

        oldest_item = self.history[0]
        words_in_history = (total_words-oldest_item.get_words())
        minutes_in_history = (current_time-oldest_item.get_time())/float(60)
        if (minutes_in_history<=0):
            return
        current_speed =  words_in_history/minutes_in_history

        if (current_speed > self.maximum_speed):
            if (len(self.history) > 10):
                self.maximum_speed = current_speed

        ratio = self.total_strokes/float(total_words)

        self.c_speed_text.SetLabel(CURRENT_SPEED_TEXT+": "+str(round(current_speed)))
        self.a_speed_text.SetLabel(AVERAGE_SPEED_TEXT+": "+str(round(average_speed)))
        self.m_speed_text.SetLabel(MAX_SPEED_TEXT+": "+str(round(self.maximum_speed)))
        self.ratio_text.SetLabel(RATIO_TEXT+": "+str(round(ratio,2)))

        self.Show()

    def handle_on_top(self, event):
        self.config.set_speed_report_on_top(event.IsChecked())
        self.display(self.GetParent(), self.config)

    @staticmethod
    def close_all():
        for instance in SpeedReportDialog.other_instances:
            instance.Close()
        del SpeedReportDialog.other_instances[:]

    @staticmethod
    def display(parent, config):
        # StrokeDisplayDialog shows itself.
        SpeedReportDialog(parent, config)

    @staticmethod
    def stroke_handler(stroke):
        SpeedReportDialog.total_strokes += 1

    @staticmethod
    def output_handler(backspaces, text):
        SpeedReportDialog.total_characters += len(text) - backspaces


class HistoryItem:

    def __init__(self, current_time, strokes, words):
        self.timestamp = current_time
        self.strokes = strokes
        self.words = words

    def get_time(self):
        return self.timestamp

    def get_strokes(self):
        return self.strokes

    def get_words(self):
        return self.words