#!/usr/bin/env python
from setuptools import setup, find_packages

__version__ = '1.5.0'

name = 'pycats'

package_list = []

console_scripts = []

gui_scripts = []

entry_points = {
        'console_scripts': console_scripts,
        'gui_scripts': gui_scripts
    }

author = 'Guifre Cuni'
author_email = 'ctbeamlines@cells.es'
platforms = 'all'
license = 'GPL-3.0+'

description = 'Library to control and monitor the CATS Irelec sample changer.'

long_description = 'This library implements the API from the CATS Irelec ' \
                   'server. The library provides control and monitor of the ' \
                   'CATS sample changer.'

setup(
    name=name,
    version=__version__,
    packages=find_packages(),
    package_dir={},
    entry_points=entry_points,
    author=author,
    author_email=author_email,
    description=description,
    long_description=long_description,
    url='',
    platforms=platforms,
    package_data={'': package_list},
    include_package_data=True,
    install_requires=['setuptools', 'python'],
    requires=['pkg_resources'],
)
