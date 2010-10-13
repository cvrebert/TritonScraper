#!/usr/bin/env python

from sys import exit
exit("Does not work yet")

from setuptools import setup, find_packages
setup(
    name = "TritonScraper",
    version = "0.5",
    packages = find_packages(),
    scripts = ['demo.py'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['lxml>=2.2.8'],

    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst'],
        # And include any *.msg files found in the 'hello' package, too:
        'triton_scraper': ['config.cfg'],
    },
    packages = ['triton_scraper']
    package_dir = {'':'src'},   # tell distutils packages are under src
    exclude_package_data = { '': ['README.txt'] },

    # metadata for upload to PyPI
    author = "Chris Rebert",
    author_email = "code@rebertia.com",
    description = "This is an Example Package",
    long_descripion = ""
    license = "MIT",
    keywords = "hello world example examples",
    url = "http://example.com/HelloWorld/",   # project home page, if any

    # could also include long_description, download_url, classifiers, etc.
    platforms = [""],
    classifiers = ["Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "Topic :: Education",
        "Topic :: Internet :: WWW/HTTP :: Browsers"],
    download_url = "",
)

#FIXME: instead of using __file__:
from pkg_resources import Requirement, resource_filename
filename = resource_filename(Requirement.parse("MyProject"),"sample.conf")
