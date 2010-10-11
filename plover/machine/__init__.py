# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Repository of stenotype machine descriptions.

Each stenotype machine description must define a Stenotype class that
has start_capture, stop_capture, and add_callback methods.

"""
__all__ = ['geminipr', 'geminitx', 'sidewinder']
