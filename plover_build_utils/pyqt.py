from collections import defaultdict
from inspect import isclass
import re


def _qt_scoped_enums_replacements():
    from PyQt5 import QtCore, QtGui, QtWidgets
    enumtype = QtCore.Qt.DropAction.__class__
    scoped_enums = defaultdict(list)
    for mod in (QtCore, QtGui, QtWidgets):
        for attr in dir(mod):
            if not attr.startswith('Q'):
                continue
            obj = getattr(mod, attr)
            if not isclass(obj):
                continue
            scope = (mod.__name__.split('.', 1)[1], attr)
            scope_obj = obj
            for attr in dir(scope_obj):
                obj = getattr(scope_obj, attr, None)
                if obj is None:
                    continue
                if not isinstance(obj.__class__, enumtype):
                    continue
                enum = '.'.join(scope + (obj.__class__.__name__,))
                scoped_enums[enum].append(attr)
    scoped_enums_replacements = {}
    for scope, attr_list in scoped_enums.items():
        *scope, enum = scope.split('.')
        for attr in attr_list:
            for namespace in (scope, scope[1:]):
                pattern = '.'.join(namespace + [attr])
                replacement = '.'.join(namespace + [enum, attr])
                assert pattern not in scoped_enums_replacements
                scoped_enums_replacements[pattern] = replacement
    return scoped_enums_replacements


def fix_icons(contents):
    # replace ``addPixmap(QtGui.QPixmap(":/settings.svg"),``
    # by ``addFile(":/settings.svg", QtCore.QSize(),``
    contents = re.sub(
        r'\baddPixmap\(QtGui\.QPixmap\(("[^"]*")\),',
        r'addFile(\1, QtCore.QSize(),',
        contents
    )
    return contents

def fix_resources(contents):
    # remove ``from . import resources_rc``,
    # and replace ``addFile(":/prefix/font_selector.svg",``
    # by ``addFile(":/prefix/font_selector.svg",``
    contents = contents.replace('\nfrom . import resources_rc\n', '')
    contents = re.sub(
        r'\baddFile\(":/([^/]+)/([^"]+)",',
        r'addFile("\1:\2",',
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
        return '{comment}\n{ws}{pre1}{pre2}_({str})'.format(comment=comment, **gd)
    contents = re.sub((r'(?P<ws> *)(?P<pre1>.*?)(?P<pre2>\.set(?P<field>\w+)\()?'
                       r'\bQCoreApplication\.translate\("(?P<widget>[^"]+)", (?P<str>.+), None\)'), repl, contents)
    contents = re.sub((r'(?P<ws> *)(?P<pre1>.*?)(?P<pre2>\.set(?P<field>\w+)\()?'
                       r'\b_translate\("(?P<widget>[^"]+)", (?P<str>.+)\)'), repl, contents)
    assert re.search(r'\b(QCoreApplication\.|_)translate\(', contents) is None
    return contents

def no_autoconnection(contents):
    # remove calls to ``QtCore.QMetaObject.connectSlotsByName``
    contents = re.sub(
        r'\n\s+(:?QtCore\.)?QMetaObject\.connectSlotsByName\(\w+\)\n',
        '\n',
        contents
    )
    return contents

def use_qtpy(contents):
    # replace ``from PyQt5 import QtCore, QtGui, QtWidgets``
    # by ``from qtpy import QtCore, QtGui, QtWidgets`
    lines = contents.split('\n')
    for n, l in enumerate(lines):
        if re.search(r'\bimport\b', l) is None:
            continue
        lines[n] = re.sub(r'\b(PyQt5|PySide2)\b', 'qtpy', l)
    return '\n'.join(lines)

def use_scoped_enums(contents):
    # replace ``QtWidgets.QSizePolicy.MinimumExpanding``
    # by ``QtWidgets.QSizePolicy.Policy.MinimumExpanding``
    scoped_enums_replacements = getattr(use_scoped_enums, 'scoped_enums_replacements', None)
    if scoped_enums_replacements is None:
        scoped_enums_replacements = _qt_scoped_enums_replacements()
        use_scoped_enums.scoped_enums_replacements = scoped_enums_replacements
    def replace(m):
        match = m.group(0)
        return scoped_enums_replacements.get(match, match)
    return re.sub(r'\b((?:Qt\w+\.)?Q\w+)\.(\w+)\b', replace, contents)
