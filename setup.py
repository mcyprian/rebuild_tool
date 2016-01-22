#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand

class PyTest(TestCommand):
    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

description = "Tool to plan order of packages building in Software Collections"
"creation. Finds all dependancies of the packagesi, prints order of building"
"and makes visualization of the relations between them."

setup(
    name='rebuild_tool',
    version='1.0.0',
    description='Plans order of packages building in scl creation',
    long_description=description,
    keywords='rhscl, build',
    author='Michal Cyprian',
    author_email='mcyprian@redhat.com',
    url='https://github.com/mcyprian/rebuild_tool',
    license='MIT',
    packages=['rebuild_tool', ],
    install_requires=['click',
                      'networkx',
                      'matplotlib',
                      'copr'],
    setup_requires=['setuptools',
                    'flexmock',
                    'pytest'],
    cmdclass={'test': PyTest},
    classifiers=['Development Status :: 2 - Pre-Alpha',
                 'Environment :: Console',
                 'Intended Audience :: Developers',
                 'Intended Audience :: Information Technology',
                 'License :: OSI Approved :: MIT License',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python',
                 'Topic :: Software Development :: Build Tools',
                 ]
)

