# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Repository of stenography dictionary types.

Each dictionary submodule must define a STROKE_DELIMITER constant and
a toRTFCRE function that takes a sequence as input and returns a
string.

"""

supported = {'Eclipse' : 'plover.dictionary.eclipse',
             'DCAT' : 'plover.dictionary.dcat',}
