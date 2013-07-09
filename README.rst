Copyright (c) 2010-2011 Joshua Harlan Lifton.
See LICENSE.txt for details.

Plover: Open Source Stenography Software
========================================

Stenography expertise, original concept, feature design, and testing
by Mirabai Knight. Code and technical design by Joshua Harlan
Lifton. Additional code contributions by Hesky Fisher.

Supported stenotype protocols:
 * QWERTY keyboards with n-key rollover (e.g. Microsoft SideWinder X4)
 * Gemini PR (a.k.a. Gemini Enhanced)
 * TX Bolt (a.k.a. Gemini TX)
 * Stentura
 * Treal

Contact the authors if you would like Plover to support your stenotype
machine.


Warning
-------

Plover is not mature software. Once running, it will interpret all
keystrokes according to the stenography dictionary you provide. Be
careful what you type. When using the Sidewinder or any other normal
keyboard with Plover, your normal keyboard shortcuts may not work. Use
the mouse or stop the Plover program if you are unsure of what will
result from typing.


Installation
------------

Windows:
Plover is available for Windows as a compiled executable. The latest 
version is here: https://github.com/plover/plover/releases/2.4.0/2662/plover.exe 
There is no installer, just run the binary 

Mac:
Plover is available for Mac OSX as an app. Download the dmg from:
https://github.com/plover/plover/releases/2.4.0/2663/Plover.dmg
Open the dmg and drag plover to the applications folder to install.
Before running the application you will also need to 
Open System Preferences, Open "Universal Access" and check the box next 
to "Enable access for assistive devices" If you do not do this, Plover 
will not work.

Linux (debian/ubuntu):
There is no package yet so an installation requires installing all dependencies. First, you must have python 2.7. Then
run the following commands::

    cd
    sudo apt-get install python-xlib python-serial python-wxgtk2.8 wmctrl python-dev python-pip
    sudo pip install -U appdirs simplejson
    wget https://github.com/plover/plover/archive/2.4.0.tar.gz
    tar -zxf 2.4.0.tar.gz
    cd plover-2.4.0
    sudo python setup.py install

Once this is done then you should be able to run plover from the applications menu or from the command line with::

    /usr/local/bin/plover
    
If you run into any trouble please seek help on the plover aviary: http://stenoknight.com/plover/aviary/phpBB3/
or the plover mailing list: https://groups.google.com/forum/#!forum/ploversteno

Running Plover
--------------

Windows:
Run the downloaded executable.

Mac:
Run plover from applications.

Linux:
Run plover from the application list or the command line as shown above.

All OS:
Starting the application will bring up a small window with a red
'P' icon. At this point, Plover is inactive. To activate Plover, click
the red 'P' icon, or type on the steno machine the strokes
corresponding to the PLOVER:TOGGLE or PLOVER:RESUME commands as
defined in the dictionary. The icon will turn green to indicate that
Plover is active and ready to translate stenography keystrokes into
English text. Clicking the green icon or sending the PLOVER:SUSPEND or
PLOVER:TOGGLE commands will cause the icon to turn red, which means
Plover is again in the inactive state.
