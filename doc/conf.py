# Configuration file for the Sphinx documentation builder.

# -- Path setup --------------------------------------------------------------

import os
import sys
# Add Plover base directory so we can import plover below
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------

from plover import __name__ as __software_name__, __version__, __copyright__

project = __software_name__.capitalize()
copyright = "2020 " + __copyright__.replace("(C) ", "")
author = copyright

release = __version__
version = release

# -- General configuration ---------------------------------------------------

import sphinx_rtd_theme

extensions = [
  'sphinx_rtd_theme',
  'sphinxcontrib.yt',
]

templates_path = ['_templates']

exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'

html_static_path = ['_static']

html_sidebars = {
  '**': [
    'globaltoc.html',
    'relations.html',
    'sourcelink.html',
    'searchbox.html',
  ],
}
