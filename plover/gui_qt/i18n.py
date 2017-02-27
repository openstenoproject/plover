import os
import sys
import locale
import gettext

# Python 2/3 compatibility.
from six import PY2

import pkg_resources

from plover import log


# Mark some strings for localization.
def _unused():
    # Machines.
    _('Keyboard')
    # States.
    _('stopped')
    _('initializing')
    _('connected')
    _('disconnected')


def get_language():
    env_vars = ['LANGUAGE']
    if sys.platform.startswith('linux'):
        env_vars.extend(('LC_ALL', 'LC_MESSAGES', 'LANG'))
    for var in env_vars:
        lang = os.environ.get(var)
        if lang is not None:
            return lang
    if sys.platform.startswith('linux'):
        lang, enc = locale.getdefaultlocale()
    elif sys.platform.startswith('darwin'):
        from AppKit import NSLocale
        lang_list = NSLocale.preferredLanguages()
        lang = lang_list[0] if lang_list else None
    elif sys.platform.startswith('win'):
        from ctypes import windll
        lang = locale.windows_locale[windll.kernel32.GetUserDefaultUILanguage()]
    if lang is None:
        lang = 'en'
    return lang

def install_gettext():
    lang = get_language()
    log.info('setting language to: %s', lang)
    os.environ['LANGUAGE'] = lang
    locale_dir = pkg_resources.resource_filename('plover', 'gui_qt/messages')
    if PY2:
        # unicode=True
        args = [True]
    else:
        args = []
    gettext.install('plover', locale_dir, *args)

def get_gettext(package='plover', resource_dir='gui_qt/messages'):
    locale_dir = pkg_resources.resource_filename(package, resource_dir)
    if PY2:
        # unicode=True
        args = [True]
    else:
        args = []
    translation = gettext.translation(package, locale_dir, fallback=True)
    return translation.ugettext if PY2 else translation.gettext
