
import re

from PyQt5.QtWidgets import QDialog

import plover

from plover.gui_qt.about_dialog_ui import Ui_AboutDialog


class AboutDialog(QDialog, Ui_AboutDialog):

    ROLE = 'about'

    def __init__(self, engine):
        super().__init__()
        self.setupUi(self)
        credits = plover.__credits__
        credits = re.sub(r'<([^>]*)>', r'<a href="\1">\1</a>', credits)
        credits = credits.replace('\n', '<br/>')
        self.text.setHtml(
            '''
            <style>
            h1 {text-align:center;}
            h2 {text-align:center;}
            p {text-align:center;}
            </style>
            <p><img src="%(icon)s"/></p>
            <h1>%(name)s %(version)s</h1>
            <p>%(description)s</p>
            <p><i>Copyright %(copyright)s</i></p>
            <p>License: <a href="%(license_url)s">%(license)s</a></p>
            <p>Project Homepage: <a href='%(url)s'>%(url)s</a></p>
            <h2>Credits:</h2>
            <p>%(credits)s</p>
            ''' % {
                'icon'       : ':/plover.png',
                'name'       : plover.__name__.capitalize(),
                'version'    : plover.__version__,
                'description': plover.__long_description__,
                'copyright'  : plover.__copyright__.replace('(C)', '&copy;'),
                'license'    : plover.__license__,
                'license_url': 'https://www.gnu.org/licenses/gpl-2.0-standalone.html',
                'url'        : plover.__download_url__,
                'credits'    : credits,
            })
