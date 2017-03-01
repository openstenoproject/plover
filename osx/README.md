# Mac Development

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Environment Setup](#environment-setup)
  - [Semi-automatic](#semi-automatic)
  - [Manual](#manual)
- [Running in Development](#running-in-development)
- [Building](#building)
- [Gotcha: Assistive Devices Permissions](#gotcha-assistive-devices-permissions)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Environment Setup

### Semi-automatic

With Homebrew installed, you should be able to have everything setup automatically by using: `./bootstrap.sh`.

At the moment, we need to overwrite the Python formula to get Python 3.5, as 3.6 [breaks the build process](https://github.com/pyinstaller/pyinstaller/issues/2331).

Note: you can use `./bootstrap.sh -n` to get a list of the commands that would be run.

### Manual

- install [Homebrew](http://brew.sh/)
- install Python3.5: `brew install python3`
- install other dependencies:

  ```
  ./setup.py write_requirements
  pip3 install -r requirements.txt -c requirements_constraints.txt
  ```

## Running in Development

To run from source, use `./launch.sh`.

## Building

To build to an **application bundle**, use: `./setup.py bdist_app`

To create a **disk image**, use: `./setup.py bdist_dmg`

## Gotcha: Assistive Devices Permissions

To grab user inputs and use the keyboard as a steno machine, Plover requires [Assistive Devices permissions to be granted (instructions included).](https://support.apple.com/kb/ph18391?locale=en_US)

When running from source, your terminal application must be granted Assistive Devices permissions.

If you are running from an application bundle (both in development and for releases), every new build will require a regranting of permissions.
