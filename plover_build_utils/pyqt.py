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
    contents = re.sub(r'\n', (
        '\n'
        '_ = __import__(__package__.split(".", 1)[0])._\n'
    ), contents, 1)
    contents = re.sub(
        r'\n\s+_translate = QtCore\.QCoreApplication\.translate\n',
        '\n',
        contents
    )
    def repl(m):
        gd = m.groupdict()
        comment = '{ws}# i18n: Widget: “{widget}”'.format(**gd)
        field = gd['field']
        if field:
            field = ' '.join(
                word.lower()
                for word in re.split(r'([A-Z][a-z_0-9]+)', field)
                if word
            )
            comment += ", {field}".format(field=field)
        comment += '.'
        gd['pre2'] = gd['pre2'] or ''
        return '{comment}\n{ws}{pre1}{pre2}_('.format(comment=comment, **gd)
    contents = re.sub((r'(?P<ws> *)(?P<pre1>.*?)(?P<pre2>\.set(?P<field>\w+)\()?'
                       r'\b_translate\("(?P<widget>.*)",\s'), repl, contents)
    assert re.search(r'\b_translate\(', contents) is None
    return contents

def no_autoconnection(contents):
    # remove calls to ``QtCore.QMetaObject.connectSlotsByName``
    contents = re.sub(
        r'\n\s+QtCore\.QMetaObject\.connectSlotsByName\(\w+\)\n',
        '\n',
        contents
    )
    return contents
