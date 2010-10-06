# Copyright (c) 2010 Joshua Harlan Lifton.
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
        if k == "A-" or k == "O-":
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
            if hyphenFound == True:
                k = k[1:] 
            elif hyphenFound == False:
                k = k[1:] 
                out.append("-")
                hyphenFound = True 

        out.append(k)
    return ''.join(out) 
