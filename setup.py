#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

files = ["__init__.py", "paz.py"]

setup(name = "fdsnws",
    author = "Joachim Saul",
    author_email = "saul@gfz-potsdam.de",
    packages = ['fdsnws'],
    package_data = {'fdsnws' : files },
    scripts = [ "fdsnxml2sacpz.py" ]
)
