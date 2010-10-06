# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Constants and functions for the DCAT stenography dictionary format."""

STROKE_DELIMITER = '/'

def toRTFCRE(stenoKeys):
    """Convert stenokeys to an RTF/CRE string in DCAT format.

    Argument:

    stenoKeys -- A sequence of steno keys.

    """
    out = []
    hyphenFound = False
    for k in stenoKeys:

        if len(out) == 0 and k == '*':
            out.append(k)

        elif k =="*" and out[-1] == "-": 
            out.pop()
            out.append(k)
            out.append("-")

        if k == "A-":
            k = k[:-1]
            out.append(k)
            out.append("-")
            hyphenFound = True

        elif len(out) > 0 and k =="O-" and out[-1] == "-": 
            out.pop()
            k = k[:-1]
            out.append(k)
            out.append("-")
            hyphenFound = True

        elif k == "O-":
            if hyphenFound == True:
                k = k[:-1]
                out.append(k)
            elif hyphenFound == False:
                k = k[:-1]
                out.append(k)
                out.append("-")
                hyphenFound = True

        elif k == "-E":
            if hyphenFound == True:
                k = k[1:] 
                out.append(k)
            elif hyphenFound == False: 
                k = k[1:]
                out.append("-")
                hyphenFound = True
                out.append(k)

        elif k == "-U":
            if hyphenFound == True:
                k = k[1:] 
                out.append(k)
            elif hyphenFound == False: 
                k = k[1:]
                out.append("-")
                hyphenFound = True
                out.append(k) 

        elif k.startswith("-"):
            if hyphenFound == True:
                k = k[1:] 
                out.append(k)
            elif hyphenFound == False:
                k = k[1:] 
                out.append("-")
                hyphenFound = True 
                out.append(k)

        elif k.endswith("-"):
            k = k[:-1]
            out.append(k)

        elif k == "*" and len(out) > 0 and out[-1] != '-':
            out.append(k)

    if len(out) > 0 and out[-1] == "-":
        out.pop()

    return ''.join(out) 
    
