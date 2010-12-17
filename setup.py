#!/usr/bin/env python
from setuptools import setup, find_packages
setup(
    name='delikat',
    description='A delicious Redis-backend bookmarking service.',
    version='0.1',
    packages=find_packages('src'),
    package_dir = {'':'src'},
)
