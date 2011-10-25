# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Repository of stenotype machine descriptions.

Each stenotype machine description must define a Stenotype class that
has start_capture, stop_capture, and add_callback methods.

"""
__all__ = ['geminipr', 'sidewinder', 'txbolt']

supported = {'Microsoft Sidewinder X4' : 'plover.machine.sidewinder',
             'Gemini PR' : 'plover.machine.geminipr',
             'TX Bolt': 'plover.machine.txbolt',}

