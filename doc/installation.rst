.. _installation:

Installation
============

There are several versions of Plover available for download. Most of the time,
you'll want the `latest stable version`_. However, this is fairly old, so most
folks on the `Plover Discord`_ recommend v4.0.0 -- see the
`latest weekly release`_. If you are adventurous and want access to the latest
and greatest features and developments, check out the `weekly releases`_.

.. _`latest stable version`: https://github.com/openstenoproject/plover/releases/tag/v3.1.1
.. _`latest weekly release`: https://github.com/openstenoproject/plover/releases
.. _`weekly releases`: https://github.com/openstenoproject/plover/releases
.. _`Plover Discord`: https://discord.gg/0lQde43a6dGmAMp2

If you are a developer and want to build from source, see :doc:`from_source`
for instructions for your operating system.

Check the :doc:`troubleshooting` if you run into any issues building or
running Plover.

.. note::
    The pre-built Plover distribution will **not work** on macOS 11 Big Sur due
    to an issue with Python 3.6; you will have to
    :doc:`build Plover from source<from_source>`
    against Python 3.7 or later.

Windows
-------

  1.  Download the ``.exe`` file from the release page.
        - You can place the file anywhere on your computer. You will run it from
          the same location every time.
  2.  Open the file to launch Plover.

macOS
-----

You can install Plover using `Homebrew Cask`_ if you have it installed:

::

    brew cask install plover

.. _`Homebrew Cask`: https://caskroom.github.io/

Otherwise:

  1.  Download the ``.dmg`` file from the release page.
  2.  Open the ``.dmg`` file.
  3.  In the mounted disk, drag the ``Plover.app`` to your Applications folder.
  4.  Open System Preferences > Security & Privacy > Privacy > Accessibility.
  5.  Click the "+" Button, and go to your applications and select
      ``Plover.app``.

If you use a keyboard instead of a steno machine, Plover needs
`Assistive Devices permissions`_.

.. _`Assistive Devices permissions`: https://support.apple.com/guide/mac-help/allow-accessibility-apps-to-access-your-mac-mh43185/mac

Plover is set up! You can run Plover like you would any other application.

.. note::
    Other "keyboard helper"-type applications (e.g. Karabiner Elements and text
    expanders) may interfere with Plover.

Linux
-----

Arch Linux
^^^^^^^^^^

Two AUR packages are provided:

  * |aur.plover|_ for the latest stable release
  * |aur.plover-git|_ for the current master

.. |aur.plover| replace:: ``plover``
.. |aur.plover-git| replace:: ``plover-git``
.. _aur.plover: https://aur.archlinux.org/packages/plover/
.. _aur.plover-git: https://aur.archlinux.org/packages/plover-git/

You may need to add yourself to the group ``uucp`` (owner of ``/dev/ttyACM*``,
which is usually where your keyboard will show up).

These AUR packages do not come with the `Plover plugins manager`_. This needs
to be installed separately via ``pip install plover-plugins-manager``.

.. _`Plover plugins manager`: https://pypi.org/project/plover-plugins-manager/

Gentoo
^^^^^^

Currently, only a `git ebuild`_ for the master branch is provided.

.. _`git ebuild`: https://framagit.org/3/ebuilds

Ubuntu
^^^^^^

Stable releases can be installed from a dedicated PPA, see |ppa| for
instructions.

.. |ppa| replace:: ``ppa:benoit.pierre/plover``
.. _ppa: https://launchpad.net/~benoit.pierre/+archive/ubuntu/plover

.. note::
    As of February 2019, The PPA method doesn't currently appear to work with
    Ubuntu 18.04 Bionic Beaver (there is a listing for Xenial however). One
    can use the AppImage method instead. Similarly for weeklies one can use
    the AppImage method or other approaches for installing on other Linux
    distributions.

Other distributions
^^^^^^^^^^^^^^^^^^^

An AppImage is provided: it includes all the necessary dependencies and should
run on most x86 64-bit distributions. To use it:

  1.  Download it
  2.  Add the user to the ``dialout`` group (``sudo adduser <user> dialout``)
  3.  After adding the group, logout and login again for the change to take effect
  4.  Make the AppImage executable
  5.  Launch it like a standard executable

.. note::
    You can install the AppImage for your current user (and register Plover in
    your standard applications menu) by executing it with the ``--install``
    flag. If you had previously installed another AppImage version of Plover,
    it will be automatically uninstalled and replaced.

As of January 2019 AppImage files are not in the latest stable version but can
be found in weeklies.

Other approaches
^^^^^^^^^^^^^^^^

Other approaches could include:

  * Installing from the ``.deb`` file if you are using Debian or a
    Debian-derived distribution (e.g. with ``sudo apt install path/to/.deb``
    or using ``dpkg``), but you may need to do some work to deal with handling
    the dependencies.

  * :doc:`Installing from source<from_source>`.
