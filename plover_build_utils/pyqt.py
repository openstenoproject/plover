import re


def fix_icons(contents):
    # replace ``addPixmap(QtGui.QPixmap(":/settings.svg"),``
    # by ``addFile(":/settings.svg", QtCore.QSize(),``
    contents = re.sub(
        r'\baddPixmap\(QtGui\.QPixmap\(("[^"]*")\),',
        r'addFile(\1, QtCore.QSize(),',
        contents
    )
    return contents

def gettext(contents):
    # replace ``_translate("context", `` by ``_(``
    contents = re.sub(r'_translate\(".*",\s', '_(', contents)
    contents = re.sub(
        r'\n\s+_translate = QtCore\.QCoreApplication\.translate\n',
        '\n',
        contents
    )
    return contents

def no_autoconnection(contents):
    # remove calls to ``QtCore.QMetaObject.connectSlotsByName``
    contents = re.sub(
        r'\n\s+QtCore\.QMetaObject\.connectSlotsByName\(\w+\)\n',
        '\n',
        contents
    )
    return contents
