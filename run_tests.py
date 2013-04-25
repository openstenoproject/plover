# Copyright (c) 2012 Hesky Fisher
# See LICENSE.txt for details.

import os.path
import unittest

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover(os.path.dirname(__file__))
    unittest.TextTestRunner().run(suite)
