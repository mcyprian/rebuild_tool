#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

description = "Tool to plan order of packages building in Software Collections"
"creation. Finds all dependancies of the packagesi, prints order of building"
"and makes visualization of the relations between them."

setup(
    name='sclbuilder',
    version='1.0.0',
    description='Plans order of packages building in scl creation',
    long_description=description,
    keywords='rhscl, build',
    author='Michal Cyprian',
    author_email='mcyprian@redhat.com',
    url='https://github.com/mcyprian/sclbuilder',
    license='MIT',
    packages=['sclbuilder', ],
    install_requires=['click',
                      'networkx',
                      'matplotlib'],
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

