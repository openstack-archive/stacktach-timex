import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

desc = """timex
=====

A time expressions library implementing a mini-language for manipulating
datetimes.

Much like regular expressions provide a mini-language for performing certain
operation on strings, Timex's time expressions provide a convenient way of
expressing datetime and date-range operations. These expressions are strings,
and can be safely read from a config file or user input.

Read README.md for syntax and examples.
"""

setup(
    name='timex',
    version='0.20.0',
    author='Monsyne Dragon',
    author_email='mdragon@rackspace.com',
    description=("A time expressions library implementing a mini-language "
                 "for manipulating datetimes"),
    license='Apache License (2.0)',
    keywords='datetime manipulation transformation DSL',
    packages=find_packages(exclude=['tests']),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    url='https://github.com/StackTach/timex',
    scripts=[],
    long_description=desc,
    install_requires=[
        "ply",
        "six >= 1.5.2",
    ],


    zip_safe=False
)
