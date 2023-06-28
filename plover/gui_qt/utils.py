from PyQt6.QtCore import QSettings
from PyQt6.QtGui import (
    QAction,
    QGuiApplication,
    QIcon,
    QKeySequence,
    QPixmap
)
from PyQt6.QtWidgets import (
    QMainWindow,
    QToolBar,
    QToolButton,
    QWidget,
)
import importlib.resources

from plover import _


def ActionCopyViewSelectionToClipboard(view):
    def copy_selection_to_clipboard():
        indexes = view.selectedIndexes()
        data = view.model().mimeData(indexes)
        QGuiApplication.clipboard().setMimeData(data)
    action = QAction(_('Copy selection to clipboard'))
    action.setShortcut(QKeySequence(QKeySequence.StandardKey.Copy))
    action.triggered.connect(copy_selection_to_clipboard)
    return action


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


def Icon(resource):
    icon = QIcon()
    package = "plover.gui_qt.resources"

    if type(resource) is tuple:
        package = resource[0]
        resource = resource[1]

    if type(resource) is str:
        if resource.startswith(":/"):
            resource = resource[2:]

    with importlib.resources.path(package, resource) as f_path:
        icon.addPixmap(QPixmap(str(f_path)))

    return icon


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
            sub_menu = action.menu()
            if sub_menu is None:
                continue
            actions_dict.update(find_menu_actions(sub_menu))
            name = sub_menu.objectName()
        assert name
        assert name not in actions_dict
        actions_dict[name] = action
    return actions_dict
