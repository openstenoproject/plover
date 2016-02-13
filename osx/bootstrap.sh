#!/bin/bash
# Copyright (c) 2016 Jeremy W. Sherman, distributed under GPLv2+ WITHOUT ANY
# WARRANTY.
#
# Environment setup script for OS X Plover dev.

# Exit Statuses
EX_FAILURE_NO_CCTOOLS=1
EX_FAILURE_NO_PYTHON=2
EX_FAILURE_NO_WXPYTHON=3

PYTHON=${PYTHON:=$(which python)}
PIP=${PIP:=$(which pip)}

REAL_PYTHON=$("$PYTHON" -c 'import sys; print sys.executable')

echo "$0: using python: $PYTHON (executable: $REAL_PYTHON)"
echo "$0: using pip: $PIP (version: $($PIP --version))"


has_cli_tools() {
    echo "$0: checking for functioning cli tools by trying clang"
    if clang --version; then
      "true"
    else
      "false"
    fi
}


has_python() {
    echo "$0: checking for functioning python"
    if $PYTHON -c 'import sys; sys.exit(0)'; then
        "true"
    else
        "false"
    fi
}


has_wxPython() {
    echo "$0: checking for functioning wxPython"
    if $PYTHON -c 'import wx' 2>&1 >/dev/null; then
        "true"
    else
        "false"
    fi
}


main() {
    if ! has_cli_tools; then
        cat 1>&2 <<EOT
CLI tools are not installed. Install Homebrew and do what it says. :)
Double-click the URL to visit: http://brew.sh/ for install instructions.
EOT
        exit $EX_FAILURE_NO_CCTOOLS
    else
        echo "$0: found clang, continuing"
    fi


    if ! has_python; then
        cat 1>&2 <<EOT
$0: Python is required, but
$PYTHON
appears not to be executable. Please run:

    brew install python --framework

or use a different Python by setting the PYTHON env var.
EOT
        exit $EX_FAILURE_NO_PYTHON
    else
        echo "$0: python works"
    fi


    if ! has_wxPython; then
        cat 1>&2 <<EOT
$0: wxPython is required, but |import wx| when running
$PYTHON
failed. Please run:

    brew install wxpython
EOT
        exit $EX_FAILURE_NO_64BIT_WXPYTHON
    else
        echo "$0: successfully imported wx"
    fi


    echo "$0: installing required libraries using pip"
    pip install -r requirements.txt
}

main
