import os
import sys
import locale
import gettext

import pkg_resources

from plover.oslayer.config import CONFIG_DIR


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

def get_locale_dir(package, resource_dir):
    for locale_dir in [
        os.path.join(CONFIG_DIR, 'messages'),
        pkg_resources.resource_filename(package, resource_dir),
    ]:
        if gettext.find(package, locale_dir):
            break
    return locale_dir


class Translator:

    def __init__(self, package, resource_dir='messages', lang=None):
        self.package = package
        self.resource_dir = resource_dir
        if lang is None:
            lang = get_language()
        self.lang = lang

    @property
    def lang(self):
        return self._lang

    @lang.setter
    def lang(self, lang):
        self._lang = lang
        localedir = get_locale_dir(self.package, self.resource_dir)
        self._translation = gettext.translation(self.package, localedir=localedir,
                                                languages=[lang], fallback=True)
        self.gettext = self._translation.gettext
        self.ngettext = self._translation.ngettext

    def __call__(self, message):
        return self.gettext(message)

    def _(self, message):
        return message
