Copyright (c) 2010 Joshua Harlan Lifton.
See LICENSE.txt for details.

Plover: Open Source Stenography Software

Stenography expertise, original concept, feature design, and testing
by Mirabai Knight. Code and technical design by Joshua Harlan Lifton.

Supported stenotype machines:
 * Microsoft SideWinder X4 keyboard
 * Gemini PR stenography machine

Contact the authors if you would like Plover to support your stenotype
machine.


WARNING

Plover is not mature software. Once running, it will interpret all
keystrokes according to the stenography dictionary you provide. Be
careful what you type. When using the Sidewinder or any other normal
keyboard with Plover, your normal keyboard shortcuts may not work. Use
the mouse or stop the Plover program if you are unsure of what will
result from typing.


INSTALLATION

These installation notes are for Debian-like Linux systems. From the
directory in which this README file is located, run the following
commands:

sudo aptitude install python-xlib python-serial python-wxgtk2.8
sudo python setup.py install


RUNNING PLOVER

After installation is complete as above, the Plover application will
be available in the Applications->Universal Access menu. Starting the
application will cause a red 'P' icon to appear in the desktop's
taskbar. At this point, Plover is inactive. To activate Plover, click
the red 'P' icon. The icon will turn green to indicate that Plover is
active and ready to translate stenography keystrokes into English
text. Clicking the green icon will cause it to turn red, which means
Plover is again in the inactive state. Right clicking on the 'P' icon
will cause a menu to appear. From the menu, Plover can be quit,
configured, and toggled between active and inactive.
