
from qtpy.QtCore import QSettings, Qt
from qtpy.QtWidgets import (
    QFileDialog,
    QFontDialog,
    QMainWindow,
    QMenu,
    QToolBar,
    QToolButton,
    QWidget,
)
from qtpy import API as QT_API


def ToolButton(action):
    button = QToolButton()
    button.setDefaultAction(action)
    return button


def ToolBar(*action_list):
    toolbar = QToolBar()
    for action in action_list:
        if action is None:
            toolbar.addSeparator()
        else:
            toolbar.addWidget(ToolButton(action))
    return toolbar


class WindowState(QWidget):

    ROLE = None

    def _save_state(self, settings):
        pass

    def save_state(self):
        assert self.ROLE
        settings = QSettings()
        settings.beginGroup(self.ROLE)
        settings.setValue('geometry', self.saveGeometry())
        if isinstance(self, QMainWindow):
            settings.setValue('state', self.saveState())
        self._save_state(settings)
        settings.endGroup()

    def _restore_state(self, settings):
        pass

    def restore_state(self):
        assert self.ROLE
        settings = QSettings()
        settings.beginGroup(self.ROLE)
        geometry = settings.value('geometry')
        if geometry is not None:
            self.restoreGeometry(geometry)
        if isinstance(self, QMainWindow):
            state = settings.value('state')
            if state is not None:
                self.restoreState(state)
        self._restore_state(settings)
        settings.endGroup()


def find_menu_actions(menu):
    '''Recursively find and return a menu actions.'''
    actions_dict = {}
    for action in menu.actions():
        name = action.objectName()
        if not name:
            continue
        assert name not in actions_dict
        actions_dict[name] = (action, None)
    for child in menu.children():
        if not isinstance(child, QMenu):
            continue
        name = child.objectName()
        if not name:
            continue
        assert name not in actions_dict
        actions_dict[name] = (child.menuAction(), child)
        actions_dict.update(find_menu_actions(child))
    return actions_dict


if QT_API.startswith('pyside'):

    def select_font(*args, **kwargs):
        ok, font = QFontDialog.getFont(*args, **kwargs)
        return font, ok

    def obj_exec(obj, *args, **kwargs):
        return obj.exec_(*args, **kwargs)

else:

    def select_font(*args, **kwargs):
        return QFontDialog.getFont(*args, **kwargs)

    def obj_exec(obj, *args, **kwargs):
        return obj.exec(*args, **kwargs)


if QT_API == 'pyqt6':

    BOOL_TO_CHECKED = {
        True: Qt.CheckState.Checked.value,
        False: Qt.CheckState.Unchecked.value,
    }

elif QT_API == 'pyside6':

    BOOL_TO_CHECKED = {
        True: int(Qt.CheckState.Checked),
        False: int(Qt.CheckState.Unchecked),
    }

else:

    BOOL_TO_CHECKED = {
        True: Qt.CheckState.Checked,
        False: Qt.CheckState.Unchecked,
    }

CHECKED_TO_BOOL = {v: k for k, v in BOOL_TO_CHECKED.items()}


if QT_API == 'pyside6':

    def select_open_filenames(*args, directory=None, **kwargs):
        return QFileDialog.getOpenFileNames(*args, dir=directory, **kwargs)

    def select_save_filename(*args, directory=None, **kwargs):
        return QFileDialog.getSaveFileName(*args, dir=directory, **kwargs)

else:

    def select_open_filenames(*args, **kwargs):
        return QFileDialog.getOpenFileNames(*args, **kwargs)

    def select_save_filename(*args, **kwargs):
        return QFileDialog.getSaveFileName(*args, **kwargs)
