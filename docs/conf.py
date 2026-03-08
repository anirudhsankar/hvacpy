# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'hvacpy'
copyright = '2026, hvacpy contributors'
author = 'hvacpy contributors'
release = '0.4.1'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',       # Google/NumPy style docstrings
    'sphinx.ext.viewcode',       # [source] links
    'sphinx.ext.intersphinx',    # cross-links to Python docs
    'myst_parser',               # Markdown support
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'show-inheritance': True,
}

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
