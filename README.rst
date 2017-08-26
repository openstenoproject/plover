Plover
======

    Bringing stenography to everyone.

|Windows build status| |Linux build status| |Mac build status|

+---------------+---------------+-----------+-----------+-------------------+-------------------+
| `Homepage`_   | `Releases`_   | `Wiki`_   | `Blog`_   | `Google Group`_   | `Discord Chat`_   |
+---------------+---------------+-----------+-----------+-------------------+-------------------+

-  `About <#about>`__
-  `Installation <#installation>`__
-  `Getting help <#getting-help>`__
-  `Contributing <#contributing>`__
-  `Donations <#donations>`__
-  `Programming <#programming>`__
-  `Writing, Art, UX, and Web Design <#writing-art-ux-and-web-design>`__
-  `Development Environment and Building <#development-environment-and-building>`__

About
-----

Plover (rhymes with "lover") is a desktop application that allows anyone
to use stenography to write on their computer, up to speeds of 200WPM
and beyond.

Plover is part of the `Open Steno Project`_. The Open Steno Project's
goal is to provide everything you need to learn machine shorthand on
your own, from free software, to cheap hardware, to learning resources.

Plover is GPLv2+ as of version 3.1.0. See the `license`_ for details.

Installation
------------

Plover runs on Windows, Linux, and Mac.

View the `installation guide`_ which covers downloading, installation,
and initial configuration.

Getting help
------------

Having trouble with Plover?

The Wiki has several pages to help you:

-  `Installation Guide`_
-  `Beginner's Guide`_
-  `Supported Hardware`_
-  `Troubleshooting Common Issues`_

If you are still having trouble, have found a bug, or would like to
request a new feature, please `search for or create an issue
<Issues_>`_.  When making a new issue, fill out the form as best you can
so that we can help you quickly.

If you are looking for more general support (i.e. you don't have a
specific issue), consider joining the community. We are active on the
`Discord Chat`_, a live chatroom service; and on the `Google Group`_,
a more traditional mailing list.

Contributing
------------

The Open Steno Project is always growing, and could use your help!

Donations
~~~~~~~~~

Plover is developed by volunteers. Donations to Open Steno help fund new
projects as well as any maintenance costs with publishing Plover.

`Donate here <Donate_>`_, donations of any size are very appreciated!

Programming
~~~~~~~~~~~

Plover is a cross-platform desktop application written in Python. To
contribute to Plover, see `contributing`_.

If Python isn't your thing, there are other steno-related projects,
including `StenoJig`_ (JavaScript) and `StenoTray`_ (Java).

Writing, Art, UX, and Web Design
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The `Plover Wiki <Wiki_>`_ discusses Plover and Open Steno in
   general. Edits to the Wiki and new page ideas are welcome.
-  Graphic art for Plover and stenography in general is always
   appreciated. The app's icons are worked on at `morinted/plover\_icons
   <Icons_>`_. You may consider reimagining or reposing `Plover's
   mascot, Dolores <Mascot_>`_.
-  UX improvement suggestions are welcome. Plover runs on Windows, Mac,
   and Linux, and should be powerful but out of the way, which poses
   some interesting challenges. Please drop in to the Discord server to
   brainstorm with users and the developers.
-  Open Steno has websites that accept contributions, including the
   `Open Steno Project Homepage <Open Steno Project_>`_ (`source <Open
   Steno Project Homepage Source_>`_) and `Plover's Homepage
   <Homepage_>`_ (`source <Homepage Source_>`_).

Development Environment and Building
------------------------------------

Plover is cross-platform and has separate build instructions for each
platform.

Please follow through for your system:

-  `Windows <windows/README.md>`_
-  `Linux <linux/README.md>`_
-  `Mac <osx/README.md>`_

.. _Beginner's Guide: https://github.com/openstenoproject/plover/wiki/Beginner's-Guide:-Get-Started-with-Plover
.. _Blog: http://plover.stenoknight.com
.. _Contributing: CONTRIBUTING.md
.. _Discord Chat: https://discord.gg/0lQde43a6dGmAMp2
.. _Donate: http://www.openstenoproject.org/donate
.. _Google Group: https://groups.google.com/forum/#!forum/ploversteno
.. _Homepage Source: https://github.com/openstenoproject/plover/tree/gh-pages
.. _Homepage: http://opensteno.org/plover
.. _Icons: https://github.com/morinted/plover_icons
.. _Installation Guide: https://github.com/openstenoproject/plover/wiki/Installation-Guide
.. _Issues: https://github.com/openstenoproject/plover/issues?q=is%3Aissue
.. _License: LICENSE.txt
.. _Mascot: http://plover.stenoknight.com/2010/10/new-logo.html
.. _Open Steno Project Homepage Source: https://github.com/openstenoproject/openstenoproject.github.io
.. _Open Steno Project: http://opensteno.org
.. _Releases: https://github.com/openstenoproject/plover/releases
.. _StenoJig: https://github.com/JoshuaGrams/steno-jig
.. _StenoTray: https://github.com/SmackleFunky/StenoTray
.. _Supported Hardware: https://github.com/openstenoproject/plover/wiki/Supported-Hardware
.. _Troubleshooting Common Issues: https://github.com/openstenoproject/plover/wiki/Troubleshooting:-Common-Issues
.. _Wiki: https://github.com/openstenoproject/plover/wiki

.. |Windows build status| image:: https://ci.appveyor.com/api/projects/status/9edrnjpukrag17h7?svg=true
   :target: https://ci.appveyor.com/project/morinted/plover
.. |Linux build status| image:: https://travis-ci.org/openstenoproject/plover.svg?branch=master
   :target: https://travis-ci.org/openstenoproject/plover
.. |Mac build status| image:: https://circleci.com/gh/openstenoproject/plover.svg?&style=shield
   :target: https://circleci.com/gh/openstenoproject/plover

.. vim: tw=72
