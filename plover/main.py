# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"Launch the plover application."

import os
import shutil
import sys
import traceback

WXVER = '3.0'
if not hasattr(sys, 'frozen'):
    import wxversion
    wxversion.ensureMinimal(WXVER)

import wx
import json
import glob

from collections import OrderedDict

import plover.gui.main
import plover.oslayer.processlock
from plover.oslayer.config import CONFIG_DIR, ASSETS_DIR
from plover.config import CONFIG_FILE, DEFAULT_DICTIONARIES, Config

def show_error(title, message):
    """Report error to the user.

    This shows a graphical error and prints the same to the terminal.
    """
    print message
    app = wx.PySimpleApp()
    alert_dialog = wx.MessageDialog(None,
                                    message,
                                    title,
                                    wx.OK | wx.ICON_INFORMATION)
    alert_dialog.ShowModal()
    alert_dialog.Destroy()

def init_config_dir():
    """Creates plover's config dir.

    This usually only does anything the first time plover is launched.
    """
    # Create the configuration directory if needed.
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

    # Copy the default dictionary to the configuration directory.
    def copy_dictionary_to_config(name):
        source_path = os.path.join(ASSETS_DIR, name)
        out_path = os.path.join(CONFIG_DIR, name)
        if not os.path.exists(out_path):
            unsorted_dict = json.load(open(source_path, 'rb'))
            ordered = OrderedDict(sorted(unsorted_dict.iteritems(),
                                         key=lambda x: x[1]))
            outfile = open(out_path, 'wb')
            json.dump(ordered, outfile, indent=0, separators=(',', ': '))

    for dictionary in DEFAULT_DICTIONARIES:
        copy_dictionary_to_config(dictionary)

    # Create a default configuration file if one doesn't already
    # exist.
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'wb') as f:
            f.close()


def main():
    """Launch plover."""
    try:
        # Ensure only one instance of Plover is running at a time.
        with plover.oslayer.processlock.PloverLock():
            init_config_dir()
            config = Config()
            config.target_file = CONFIG_FILE
            gui = plover.gui.main.PloverGUI(config)
            gui.MainLoop()
            with open(config.target_file, 'wb') as f:
                config.save(f)
    except plover.oslayer.processlock.LockNotAcquiredException:
        show_error('Error', 'Another instance of Plover is already running.')
    except:
        show_error('Unexpected error', traceback.format_exc())
    os._exit(1)

if __name__ == '__main__':
    main()
