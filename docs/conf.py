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

import sphinx.ext.apidoc

sys.path.insert(0, os.path.abspath(os.path.join('..', 'src')))
sys.path.insert(0, os.path.abspath(os.path.join('..', 'src', 'wavfile')))

from wavfile.version import __VERSION__


# -- Project information -----------------------------------------------------

project = 'wavfile'
copyright = '2022, Chris Hummersone'
author = 'Chris Hummersone'

# The short X.Y version.
version = __VERSION__
# The full version, including alpha/beta/rc tags.
release = version


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

autodoc_default_options = {
    'show-inheritance': False,
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__, __copy__, __enter__, __exit__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}


def run_apidoc(_):
    curdir = os.path.abspath(os.path.dirname(__file__))
    srcdir = os.path.normpath(os.path.join(curdir, '..', 'src'))
    outdir = os.path.normpath(os.path.join(curdir, 'wavfile'))
    templatedir = os.path.normpath(os.path.join(curdir, '_templates'))
    sphinx.ext.apidoc.main(('-o', outdir, srcdir, '-f', '-M', '-T', '-e', '--templatedir', templatedir))


def setup(app):
    app.connect('builder-inited', run_apidoc)


rst_prolog = """
.. |wavfile.open| replace:: :meth:`wavfile.open`
.. |WavRead| replace:: :class:`wavfile.wavread.WavRead`
.. |num_channels| replace:: :attr:`num_channels <wavfile.base.Wavfile.num_channels>`
.. |sample_rate| replace:: :attr:`sample_rate <wavfile.base.Wavfile.sample_rate>`
.. |bits_per_sample| replace:: :attr:`bits_per_sample <wavfile.base.Wavfile.bits_per_sample>`
.. |num_frames| replace:: :attr:`num_frames <wavfile.base.Wavfile.num_frames>`
.. |duration| replace:: :attr:`duration <wavfile.base.Wavfile.duration>`
.. |hms| replace:: :attr:`hms <wavfile.base.Wavfile.hms>`
.. |format| replace:: :attr:`format <wavfile.base.Wavfile.format>`
.. |metadata| replace:: :attr:`metadata <wavfile.base.Wavfile.metadata>`
.. |read| replace:: :meth:`read() <wavfile.wavread.WavRead.read>`
.. |readN| replace:: :meth:`read([N]) <wavfile.wavread.WavRead.read>`
.. |read_int| replace:: :meth:`read_int() <wavfile.wavread.WavRead.read_int>`
.. |read_intN| replace:: :meth:`read_int([N]) <wavfile.wavread.WavRead.read_int>`
.. |read_float| replace:: :meth:`read_float() <wavfile.wavread.WavRead.read_float>`
.. |read_floatN| replace:: :meth:`read_float([N]) <wavfile.wavread.WavRead.read_float>`
.. |iter| replace:: :meth:`iter() <wavfile.wavread.WavRead.iter>`
.. |iterN| replace:: :meth:`iter([N]) <wavfile.wavread.WavRead.iter>`
.. |iter_intN| replace:: :meth:`iter_int([N]) <wavfile.wavread.WavRead.iter_int>`
.. |iter_floatN| replace:: :meth:`iter_float([N]) <wavfile.wavread.WavRead.iter_float>`
.. |seek| replace:: :meth:`seek() <wavfile.base.Wavfile.seek>`
.. |seekN| replace:: :meth:`seek(N [, whence]) <wavfile.base.Wavfile.seek>`
.. |tell| replace:: :meth:`tell() <wavfile.base.Wavfile.tell>`
.. |close| replace:: :meth:`close() <wavfile.wavread.WavRead.close>`
.. |wavfile.read| replace:: :meth:`wavfile.read`
.. |WavWrite| replace:: :class:`wavfile.wavwrite.WavWrite`
.. |write| replace:: :meth:`write(audio) <wavfile.wavwrite.WavWrite.write>`
.. |write_int| replace:: :meth:`write_int(audio) <wavfile.wavwrite.WavWrite.write_int>`
.. |write_float| replace:: :meth:`write_float(audio) <wavfile.wavwrite.WavWrite.write_float>`
.. |add_metadata| replace:: :meth:`add_metadata(**kwargs) <wavfile.wavwrite.WavWrite.add_metadata>`
.. |wavfile.write| replace:: :meth:`wavfile.write`
"""


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
