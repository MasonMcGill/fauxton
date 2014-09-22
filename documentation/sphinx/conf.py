from os.path import dirname, join
from sys import path
path.insert(1, join(dirname(__file__), '..', '..'))

import sphinx_rtd_theme

#===============================================================================
# Project Metadata
#===============================================================================

project = 'Fauxton'
version = '0.0.0'
language = 'en'
copyright = 'Mason McGill, 2014'

#===============================================================================
# Display Options
#===============================================================================

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode'
  ]

add_module_names = False
master_doc = 'index'
source_suffix = '.rst'
autodoc_default_flags = ['members', 'undoc-members']
autodoc_member_order = 'bysource'

#===============================================================================
# HTML Options
#===============================================================================

html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
