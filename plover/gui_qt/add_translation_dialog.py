from plover.gui_qt.add_translation_dialog_ui import _, Ui_AddTranslationDialog
from plover.gui_qt.tool import Tool


class AddTranslationDialog(Tool, Ui_AddTranslationDialog):

    # i18n: Widget: “AddTranslationDialog”, tooltip.
    __doc__ = _('Add a new translation to the dictionary.')

    TITLE = _('Add Translation')
    ICON = ':/translation_add.svg'
    ROLE = 'add_translation'
    SHORTCUT = 'Ctrl+N'

    def __init__(self, engine, dictionary_path=None):
        super().__init__(engine)
        self.setupUi(self)
        self.add_translation.select_dictionary(dictionary_path)
        engine.signal_connect('config_changed', self.on_config_changed)
        self.on_config_changed(engine.config)
        self.installEventFilter(self)
        self.restore_state()
        self.finished.connect(self.save_state)

    def on_config_changed(self, config_update):
        if 'translation_frame_opacity' in config_update:
            opacity = config_update.get('translation_frame_opacity')
            if opacity is None:
                return
            assert 0 <= opacity <= 100
            self.setWindowOpacity(opacity / 100.0)

    def accept(self):
        self.add_translation.save_entry()
        super().accept()

    def reject(self):
        self.add_translation.reject()
        super().reject()
