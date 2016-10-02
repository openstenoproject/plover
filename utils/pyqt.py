import re


def fix_icons(ui_file_path):
    with open(ui_file_path, 'r') as fin:
        content = fin.read()
    # replace ``addPixmap(QtGui.QPixmap(":/settings.svg"),``
    # by ``addFile(":/settings.svg", QtCore.QSize(),``
    content = re.sub(r'\baddPixmap\(QtGui.QPixmap\(("[^"]*")\),',
                     r'addFile(\1, QtCore.QSize(),', content)
    with open(ui_file_path, 'w') as fout:
        fout.write(content)
