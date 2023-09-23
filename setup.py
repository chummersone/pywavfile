#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build the wavfile package.
"""

import pathlib
import sys
from setuptools import find_packages, setup

import project

with open('src/wavfile/version.py') as f:
    __VERSION__ = ""
    exec(f.read())

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.rst").read_text()

install_requires = []
if sys.version_info < (3, 8):
    install_requires += ['typing_extensions']

# This call to setup() does all the work
setup(
    **project.information.setup_info,
    version=__VERSION__,
    long_description=README,
    long_description_content_type="text/x-rst",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=install_requires,
    entry_points={},
)
