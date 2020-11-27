Building Plover from Source
===========================

Building Plover from source currently requires Python 3.6 installed with
``pip`` support.

.. note::
    If you are building on macOS 11 Big Sur, please note that Python 3.6 does
    not work on this platform (see `bpo-41100`_ for more information); you can
    still follow the build steps below but using Python **3.7** instead.

.. _`bpo-41100`: https://bugs.python.org/issue41100

First, clone the Plover Git repository:

::

    git clone https://github.com/openstenoproject/plover.git
    cd plover

Then, install the required dependencies via ``pip``:

::

    python3 -m pip install -r requirements.txt

.. note::
    On Linux, some dependencies can't be installed with ``pip``; you will have
    to use your system's package manager to install ``python-hidapi`` and
    ``dbus-python``.

.. note::
    On macOS 11 Big Sur, the Qt-based interface may freeze or not open at all.
    Upgrading to PyQt 5.15.2 fixes this issue:

    ::

        python3 -m pip install --upgrade PyQt5

    See `this Stack Overflow post <https://stackoverflow.com/a/64856281>`_
    for more information.

In addition, to install the standard plugins, as well as Plover itself:

::

    python3 -m pip install --user -e . -r requirements_plugins.txt

Once all the packages are installed, you can run the following commands:

  * ``./launch.sh`` (Linux, macOS) or ``./launch.bat`` (Windows) to run Plover
    directly from source
  * ``./test.sh`` (Linux, macOS) or ``./test.bat`` (Windows) to run the test suite
  * ``./setup.py bdist_win`` to create a standalone distribution for Windows
  * ``./setup.py bdist_app`` to create an application bundle for macOS
  * ``./setup.py bdist_dmg`` to create a disk image for macOS

.. note::
    On macOS, Plover requires `Assistive Devices permissions`_ to capture
    keyboard inputs and use the keyboard as a steno machine. When running from
    source, the terminal application (e.g. ``Terminal.app`` or ``iTerm2.app``)
    must be granted Assistive Devices permissions.

    If you are running from an application bundle (both in development and for
    releases), every new build will require re-granting the permissions.

.. _`Assistive Devices permissions`: https://support.apple.com/guide/mac-help/allow-accessibility-apps-to-access-your-mac-mh43185/mac
