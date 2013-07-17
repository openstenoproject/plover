# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""A gui display of recent strokes."""

import wx
from collections import deque

class StrokeHistory(object):
    def __init__(self, gui_parent):
        self.gui_parent = gui_parent
        self.buffer = deque(maxlen=100)
        
    def stroke_handler(self, stroke):
        self.buffer.append(stroke)
        
