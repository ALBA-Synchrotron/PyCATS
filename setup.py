#!/usr/bin/env python
import sys
from setuptools import setup
from setuptools import find_packages

# The version is updated automatically with bumpversion
# Do not update manually
__version__ = '2.2.1'

requirements = ['pytango', 'click']

setup_requirements = []

TESTING = any(x in sys.argv for x in ["test", "pytest"])
if TESTING:
    setup_requirements += ['pytest-runner']
test_requirements = ['pytest', 'pytest-cov']

SPHINX = any(x in sys.argv for x in ["build_sphinx"])
if SPHINX:
    setup_requirements += ['sphinx', 'sphinx-argparse', 'sphinx_rtd_theme']

setup(
    name="pycats",
    description='Library for the CATS Irelec sample changer.',
    version=__version__,
    author="Guifre Cuni",
    author_email="ctbeamlines@cells.es",
    url="https://github.com/ALBA-Synchrotron/PyCATS",
    packages=find_packages(),
    # package_data={'': package_list},
    include_package_data=False,
    license="GPLv3",
    platforms='all',
    long_description="""
    This library implements the API from the CATS Irelec server.
     The library provides control and monitor of the CATS sample changer.
    """,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3.5',
        'Topic :: Communications',
        'Topic :: Software Development :: Libraries',
    ],
    entry_points={
        'console_scripts': [
            'pyCATS = pycats.tango.server:run',
        ],
        'gui_scripts': [
            'cats-monitor = pycats.gui.tango_monitor:run [gui]'
        ]
    },
    install_requires=requirements,
    setup_requires=setup_requirements,
    tests_require=test_requirements,
    extras_require={"gui": ['PyQt5']},
    python_requires='>=3.5',
)
