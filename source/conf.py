# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os

# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Theme set full width ----------------------------------------------------

on_rtd = os.environ.get("READTHEDOCS", None) == "True"

if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme

    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
    # Override default css
    def setup(app):
        # app.add_javascript("custom.js")
        app.add_css_file("overrides.css")


else:
    html_context = {
        "css_files": [
            "https://media.readthedocs.org/css/sphinx_rtd_theme.css",
            "https://media.readthedocs.org/css/readthedocs-doc-embed.css",
            "_static/overrides.css",
        ],
    }


# -- Project information -----------------------------------------------------

project = "MQTTany"
copyright = "2020, MQTTany Contributors"
author = "Michael Murton"

# The full version, including alpha/beta/rc tags
release = "v0.11.0"
version = release


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.githubpages",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

autosectionlabel_prefix_document = True


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


# -- Options for Sphinx RTD Theme --------------------------------------------

html_theme_options = {
    "canonical_url": "",
    #'analytics_id': 'UA-XXXXXXX-1',  #  Provided by Google in your dashboard
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": True,
    #'vcs_pageview_mode': 'blob',
    "style_nav_header_background": "navy",
    # Toc options
    "collapse_navigation": False,
    "sticky_navigation": False,
    "navigation_depth": 3,
    "includehidden": True,
    "titles_only": False,
}
