# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------

project = "Plover"
copyright = "Open Steno Project"
author = copyright

release = "4.0.0-dev10"
version = release

# -- General configuration ---------------------------------------------------

extensions = [
  "sphinxcontrib.yt",
  "myst_parser",
]

templates_path = ["_templates"]

exclude_patterns = []

pygments_style = "manni"
pygments_dark_style = "monokai"

source_suffix = [".rst", ".md"]

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"

html_static_path = ["_static"]

html_title = f"{project} {version}"

html_favicon = "_static/favicon.ico"

html_css_files = [
  "custom.css",
]

html_theme_options = {
  "navigation_with_keys": True,
  "light_css_variables": {
    "color-brand-primary": "#3d6961",
    "color-brand-content": "#3d6961",
    "color-sidebar-background": "#3d6961",
    "color-sidebar-brand-text": "white",
    "color-sidebar-brand-text--hover": "white",
    "color-sidebar-caption-text": "white",
    "color-sidebar-link-text": "white",
    "color-sidebar-link-text--top-level": "white",
    "color-sidebar-item-background--hover": "#71a89f",
    "color-sidebar-item-expander-background--hover": "#71a89f",
    "color-inline-code-background": "transparent",
    "font-stack--header": "'Patua One', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji'",
    "font-stack--monospace": "'JetBrains Mono', SFMono-Regular, Menlo, Consolas, Monaco, Liberation Mono, Lucida Console, monospace",
  },
  "dark_css_variables": {
    "color-link": "#68a69b",
    "color-link--hover": "#68a69b",
  },
  "light_logo": "dolores.svg",
  "dark_logo": "dolores.svg",
}
