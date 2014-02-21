# by Brent Nesbitt
# Feb 21, 2014

"""Display the avg speed, current speed, and  maximum speed for the session, and stroke/word ratio"""
import wx
import time
from collections import deque

TITLE = 'Plover: Stroke Display'
ON_TOP_TEXT = "Always on top"
UI_BORDER = 4
MAX_SAMPLES = 300
WORD_LENGTH = 5

class SpeedReportDialog(wx.Dialog):

    history = deque(maxlen=MAX_SAMPLES)
    start_time = time.time()
    total_strokes = 0
    total_characters = 0
    maximum_speed = 0

    def __init__(self, parent, config):
        self.start_time = time.time()
        self.config = config
        on_top = config.get_speed_report_on_top()
        style = wx.DEFAULT_DIALOG_STYLE
        if on_top:
            style |= wx.STAY_ON_TOP
        pos = (config.get_speed_report_x(), config.get_speed_report_y())
        wx.Dialog.__init__(self, parent, title=TITLE, style=style, pos=pos)

        self.on_top = wx.CheckBox(self, label=ON_TOP_TEXT)
        self.on_top.SetValue(config.get_stroke_display_on_top())
        self.on_top.Bind(wx.EVT_CHECKBOX, self.handle_on_top)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.choice, proportion=1)

    def update(self):
        # called every second
        # add history item & update display
        total_words = self.total_characters/WORD_LENGTH
        current_time = time.time()
        self.history.append(HistoryItem(current_time, self.total_strokes, total_words))
        total_minutes = (current_time-self.start_time)/60
        average_speed = total_words/total_minutes

        oldest_item = self.history[0]
        words_in_history = (total_words-oldest_item.get_words())
        minutes_in_history = (current_time-oldest_item.get_time())/60
        current_speed =  words_in_history/minutes_in_history

        if (current_speed > self.maximum_speed):
            if (len(self.history) > 10):
                self.maximum_speed = current_speed

        #TODO: Update Display

    @staticmethod
    def display(parent, config):
        # StrokeDisplayDialog shows itself.
        SpeedReportDialog(parent, config)

    @classmethod
    def stroke_handler(cls, stroke):
        cls.total_strokes+=1

    @classmethod
    def output_handler(cls, text):
        cls.total_characters+=text.length()


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