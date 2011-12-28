# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Constants and functions for the Eclipse stenography dictionary format."""

STROKE_DELIMITER = '/'

def toRTFCRE(stenoKeys):
    """Convert stenokeys to an RTF/CRE string in Eclipse format.

    Argument:

    stenoKeys -- A sequence of steno keys.

    """
    out = []
    hyphenFound = False
    for k in stenoKeys:
        if k == "A-" or k == "O-" or k == "5-" or k == "0-":
            k = k[:-1]
            hyphenFound = True
            
        elif k == "-E" or k == "-U":
            k = k[1:]
            hyphenFound = True
                
        elif k[0] == "*":
            hyphenFound = True
            
        elif k.endswith("-"):
            k = k[:-1]
                
        elif k.startswith("-"):
            if hyphenFound:
                k = k[1:] 
            else:
                k = k[1:] 
                out.append("-")
                hyphenFound = True 

        out.append(k)
    return ''.join(out) 
