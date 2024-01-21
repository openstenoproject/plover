from AppKit import NSLocale


def get_system_language():
    lang_list = NSLocale.preferredLanguages()
    return lang_list[0] if lang_list else None
