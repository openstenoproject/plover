---------------------
Making a pull request
---------------------

When making a pull request, please include a short summary of the changes
and a reference to any issue tickets that the PR is intended to solve.
All PRs with code changes should include tests. All changes should include a
changelog entry.

Plover uses `towncrier <https://pypi.org/project/towncrier/>`_
for changelog management, so when making a PR, please add a news fragment in
the ``news.d/`` folder. Changelog files are written in reStructuredText and
should be a 1 or 2 sentence description of the substantive changes in the PR.
They should be named ``<section>/<pr_number>.<category>.rst``, where the
sections / categories are:

* ``feature``: New features:

  - ``core``: Core changes.
  - ``dict``: Updates to the default dictionaries.
  - ``ui``: Changes to the user interface.
  - ``linux``: Linux specific changes.
  - ``osx``: macOS specific changes.
  - ``windows``: Windows specific changes.

* ``bugfix``: For bugfixes, support the same categories as for ``feature``.

* ``api``: For documenting changes to the public/plugins API:

  - ``break``: For breaking (backward incompatible) changes.
  - ``dnr``: For deprecations of an existing feature or behavior.
  - ``new``: For other (backward compatible) changes, like new APIs.

A pull request may have more than one of these components, for example a code
change may introduce a new feature that deprecates an old feature, in which
case two fragments should be added. It is not necessary to make a separate
documentation fragment for documentation changes accompanying the relevant
code changes. See the following for an example news fragment:

.. code-block:: bash

    $ cat news.d/bugfix/1041.ui.rst
    Fix possible crash when changing machine parameters in the configuration dialog.
