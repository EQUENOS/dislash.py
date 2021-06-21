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
import sys
import sphinx_pdj_theme


sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'dislash.py'
copyright = '2021, EQUENOS'
author = 'EQUENOS'

# The full version, including alpha/beta/rc tags
release = '1.0.17'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    # 'sphinx.ext.autodoc'
    'sphinx.ext.napoleon'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes. I added the dark theme (Hopefully)
#
html_theme = 'sphinx_pdj_theme'
html_theme_path = [sphinx_pdj_theme.get_html_theme_path()]
html_theme_options = {
    'style': 'darker'
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']



def replace_stylesheet(custom_css):
    base_path = html_theme_path[0]
    style_path = f"{base_path}/static/css/pdj.css"
    backup_path = f"{base_path}/static/css/old_pdj.css"
    # Move the code to another dir
    with open(style_path, "r", encoding="utf-8") as f:
        style_code = f.read()
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(style_code)
    # Replace with custom css
    with open(custom_css, "r", encoding="utf-8") as f:
        style_code = f.read()
    with open(style_path, "w", encoding="utf-8") as f:
        f.write(style_code)



replace_stylesheet('css/pdj_modified.css')
