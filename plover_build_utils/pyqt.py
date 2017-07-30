import re


def fix_icons(contents):
    # replace ``addPixmap(QtGui.QPixmap(":/settings.svg"),``
    # by ``addFile(":/settings.svg", QtCore.QSize(),``
    contents = re.sub(r'\baddPixmap\(QtGui.QPixmap\(("[^"]*")\),',
                      r'addFile(\1, QtCore.QSize(),', contents)
    return contents

def gettext(contents):
    # replace ``_translate("context", `` by ``_(``
    contents = re.sub(r'_translate\(".*",\s', '_(', contents)
    contents = contents.replace(
        '        _translate = QtCore.QCoreApplication.translate',
        ''
    )
    return contents
