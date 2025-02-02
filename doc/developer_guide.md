# Environment setup

You need Python >= 3.8 installed, and you need [tox](https://pypi.org/project/tox/) >= 4.0.

Using tox takes care of all the details of creating and managing an isolated
virtual environment, installing the necessary dependencies, and isolating
testsuite runs.

The command for using tox is: `tox r {-e envlist} {-- arguments}`. Use `tox -a
-v` to get a list of available environments.

The same virtual environment is reused by the following tox environments:

- `tox r -e test -- ARGS`: run the testsuite. This is the default environment
  when not provided.
- `tox r -e launch -- ARGS`: run Plover from source.
- `tox r -e setup -- COMMAND`: run `./setup.py COMMAND`.
- `tox r -e packaging_checks`: run the same packaging checks as the CI (add `--
-n` to see a dry-run of the exact checks).
- `tox r -e plugins_install`: install the distribution plugins (or the specified
  plugins when run with `tox -e plugins_install -- REQS`). Note that this does
  not use the plugins manager for installing.
- `tox r -e release_prepare -- NEW_VERSION`: execute all the steps necessary for
  preparing a new release: patch the version to `NEW_VERSION` and update
  `NEWS.md`, staging all the changes for review.
- `tox r -e release_finalize`: finalize the release: commit the staged changes,
  create an annotated tag, and print the git command necessary for pushing the
  release to GitHub.

The actual virtual environment lives in `.tox/dev`, and can be ["activated" like
any other virtual environment](https://virtualenv.pypa.io/en/latest/user_guide.html#activators).

The configuration also provides support for lightweight tests only environment:
`pyX`, where `X` is the version of the Python interpreter to use. E.g. running
`tox r -e 'py3,py36,py37,py38,py39` will execute the testsuite for each version of Python we
support.

# Creating a binary distribution

A number of commands are provided by `setup.py` for creating binary
distributions (which include all the necessary dependencies):

- `bdist_appimage`: Linux only, create an [AppImage](https://appimage.org/).
- `bdist_app`: macOS only, build an **application bundle**.
- `bdist_dmg`: macOS only, create a **disk image**.
- `bdist_win`: Windows only, create a portable version.

Use `bdist_xxx --help` to get more information on each command supported options.

# Making a pull request

When making a pull request, please include a short summary of the changes
and a reference to any issue tickets that the PR is intended to solve.
All PRs with code changes should include tests. All changes should include a
changelog entry.

Plover uses [towncrier](https://pypi.org/project/towncrier) for changelog
management, so when making a PR, please add a news fragment in the `news.d/`
folder. Changelog files are written in Markdown and should be a 1 or 2 sentence
description of the substantive changes in the PR.

They should be named `<section>/<pr_number>.<category>.md`, where the sections
/ categories are:

- `feature`: New features:

  - `core`: Core changes.
  - `dict`: Updates to the default dictionaries.
  - `ui`: Changes to the user interface.
  - `linux`: Linux specific changes.
  - `osx`: macOS specific changes.
  - `windows`: Windows specific changes.

- `bugfix`: For bugfixes, support the same categories as for `feature`.

- `api`: For documenting changes to the public/plugins API:

  - `break`: For breaking (backward incompatible) changes.
  - `dnr`: For deprecations of an existing feature or behavior.
  - `new`: For other (backward compatible) changes, like new APIs.

A pull request may have more than one of these components, for example a code
change may introduce a new feature that deprecates an old feature, in which
case two fragments should be added. It is not necessary to make a separate
documentation fragment for documentation changes accompanying the relevant
code changes. See the following for an example news fragment:

```bash
$ cat news.d/bugfix/1041.ui.md
Fix possible crash when changing machine parameters in the configuration dialog.
```
