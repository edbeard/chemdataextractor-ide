#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


if os.path.exists('README.rst'):
    long_description = open('README.rst').read()
else:
    long_description = '''A toolkit for extracting chemical information from the scientific literature.'''

setup(
    name='ChemDataExtractor-IDE',
    version='1.3.1',
    author='Matt Swain, Ed Beard',
    author_email='m.swain@me.com, ed.beard94@gmail.com',
    license='MIT',
    url='https://github.com/edbeard/chemdataextractor-ide.git',
    packages=find_packages(),
    description='A toolkit for extracting chemical information from the scientific literature.',
    long_description=long_description,
    keywords='text-mining mining chemistry cheminformatics nlp html xml science scientific',
    zip_safe=False,
    entry_points={'console_scripts': ['cde = chemdataextractor.cli:cli']},
    tests_require=['pytest'],
    install_requires=[
        'appdirs', 'beautifulsoup4', 'click', 'cssselect', 'lxml', 'nltk', 'pdfminer.six', 'python-dateutil',
        'requests', 'six', 'python-crfsuite', 'DAWG', 'PyYAML'
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Chemistry',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Text Processing :: Markup :: HTML',
    ],
)
