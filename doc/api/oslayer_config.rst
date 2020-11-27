``plover.oslayer.config`` -- Platform-specific configuration
============================================================

This module provides platform-specific information like paths to configuration
files and asset directories.

.. py:module:: plover.oslayer.config

.. data:: PROGRAM_DIR

    The directory Plover is running from. In most cases, this will be the
    directory the Plover executable itself is in, but when running from an app
    bundle on macOS, this is the directory ``Plover.app`` is in.

.. data:: CONFIG_BASENAME

    The name of Plover's configuration file. By default this is ``plover.cfg``.

.. data:: CONFIG_DIR

    The directory containing Plover's configuration.

    If the main config file is in the same directory as the program itself,
    then Plover is running in `portable mode`, in which case this is equivalent
    to the program directory :data:`PROGRAM_DIR`.

    Otherwise, the location of this directory depends on the platform:

      * Windows: ``%USERPROFILE%\AppData\Local\plover``
      * macOS: ``~/Library/Application Support/plover``
      * Linux: ``~/.config/plover``

.. data:: CONFIG_FILE

    The full path name of the Plover configuration file.

.. data:: PLUGINS_PLATFORM

    The platform Plover is running on; one of either ``win``, ``darwin`` or
    ``linux``.

.. data:: ASSETS_DIR

    The directory containing Plover's assets, such as icons and dictionaries.

.. data:: plover_dist

    A :class:`pkg_resources.DistInfoDistribution` containing information about
    Plover's base distribution, such as resource paths and package metadata.

.. data:: HAS_GUI_QT

    ``True`` if Plover supports the Qt-based GUI and Qt is installed,
    ``False`` otherwise.
