#!/usr/bin/env python
from setuptools import setup, find_packages
setup(
    name='delikat',
    description='A delicious Redis-backend bookmarking service.',
    version='0.1',
    packages=find_packages('src'),
    package_dir={'':'src'},
    install_requires=[
        # FIXME - Can't be arsed to figure out the appropriate version numbers
        # here.
        ### These are for the backend.
        'lxml',
        'jsonlib',
        'pymongo',
        'redis',
        ### These are for the web-apps.
        'genshi',
        'shpaml',
        'resolver',
        'werkzeug',
        'python-openid',
        ### These are for running the web-apps in development.
        'PasteScript',
        'WSGIUtils',
        ### These are for running all our processes.
        'supervisor',
    ],
)
