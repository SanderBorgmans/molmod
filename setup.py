#!/usr/bin/env python
# -*- coding: utf-8 -*-
# MolMod is a collection of molecular modelling tools for python.
# Copyright (C) 2007 - 2012 Toon Verstraelen <Toon.Verstraelen@UGent.be>, Center
# for Molecular Modeling (CMM), Ghent University, Ghent, Belgium; all rights
# reserved unless otherwise stated.
#
# This file is part of MolMod.
#
# MolMod is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# MolMod is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --


from __future__ import print_function

import os
import subprocess
import sys

import numpy as np
from setuptools import setup
from setuptools.extension import Extension
import Cython.Build


# Try to get the version from git describe
__version__ = None
try:
    git_describe = subprocess.check_output(["git", "describe", "--tags"])
    version_words = git_describe.decode('utf-8').strip().split('-')
    __version__ = version_words[0]
    if len(version_words) > 1:
        __version__ += '.post' + version_words[1]
except subprocess.CalledProcessError:
    pass

# Interact with version.py
fn_version = os.path.join(os.path.dirname(__file__), 'molmod', 'version.py')
version_template = """\
\"""Do not edit this file, versioning is governed by ``git describe --tags`` and ``setup.py``.\"""
__version__ = '{}'
"""
if __version__ is None:
    # Try to load the git version tag from version.py
    try:
        with open(fn_version, 'r') as fh:
            __version__ = fh.read().split('=')[-1].replace('\'', '').strip()
    except IOError:
        print('Could not determine version. Giving up.')
        sys.exit(1)
else:
    # Store the git version tag in version.py
    with open(fn_version, 'w') as fh:
        fh.write(version_template.format(__version__))


setup(
    name='molmod',
    version=__version__,
    description='MolMod is a collection of molecular modelling tools for python.',
    author='Toon Verstraelen',
    author_email='Toon.Verstraelen@UGent.be',
    url='https://github.com/molmod/molmod',
    cmdclass={'build_ext': Cython.Build.build_ext},
    package_dir = {'molmod': 'molmod'},
    packages=['molmod', 'molmod.test', 'molmod.io', 'molmod.io.test'],
    include_package_data=True,
    ext_modules=[Extension(
        "molmod.ext",
        sources=["molmod/ext.pyx", "molmod/common.c", "molmod/ff.c",
                 "molmod/graphs.c", "molmod/similarity.c", "molmod/molecules.c",
                 "molmod/unit_cells.c"],
        depends=["molmod/common.h", "molmod/ff.h", "molmod/ff.pxd", "molmod/graphs.h",
                 "molmod/graphs.pxd", "molmod/similarity.h", "molmod/similarity.pxd",
                 "molmod/molecules.h", "molmod/molecules.pxd", "molmod/unit_cells.h",
                 "molmod/unit_cells.pxd"],
        include_dirs=[np.get_include()],
    )],
    setup_requires=['numpy>=1.0', 'cython>=0.24.1'],
    install_requires=['numpy>=1.0', 'nose>=0.11', 'cython>=0.24.1', 'future'],
    classifiers=[
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Scientific/Engineering :: Chemistry',
        'Intended Audience :: Science/Research',
    ],
)
