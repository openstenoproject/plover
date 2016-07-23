# -*- coding: utf-8 -*-
# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"Launch the plover application."

# Python 2/3 compatibility.
from __future__ import print_function

import os
import sys
import traceback
import argparse

WXVER = '3.0'
if not hasattr(sys, 'frozen'):
    import wxversion
    wxversion.ensureMinimal(WXVER)

if sys.platform.startswith('darwin'):
    import appnope
import wx

import plover.gui.main
import plover.oslayer.processlock
from plover.oslayer.config import CONFIG_DIR, ASSETS_DIR
from plover.config import CONFIG_FILE, Config
from plover import log
from plover import __name__ as __software_name__
from plover import __version__

def show_error(title, message):
    """Report error to the user.

    This shows a graphical error and prints the same to the terminal.
    """
    print(message)
    app = wx.App()
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

    # Create a default configuration file if one doesn't already exist.
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'wb') as f:
            f.close()


def main():
    """Launch plover."""
    description = "Run the plover stenotype engine. This is a graphical application."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--version', action='version', version='%s %s'
                        % (__software_name__.capitalize(), __version__))
    parser.add_argument('-l', '--log-level', choices=['debug', 'info', 'warning', 'error'],
                        default=None, help='set log level')
    args = parser.parse_args(args=sys.argv[1:])
    if args.log_level is not None:
        log.set_level(args.log_level.upper())
    try:
        # Ensure only one instance of Plover is running at a time.
        with plover.oslayer.processlock.PloverLock():
            if sys.platform.startswith('darwin'):
                appnope.nope()
            init_config_dir()
            # This must be done after calling init_config_dir, so
            # Plover's configuration directory actually exists.
            log.setup_logfile()
            log.info('Plover %s', __version__)
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
