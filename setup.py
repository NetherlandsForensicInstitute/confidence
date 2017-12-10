import codecs
from os import path
from setuptools import setup


here = path.abspath(path.dirname(__file__))


with open(path.join(here, 'README.rst'), 'r') as readme:
    readme = readme.read()


dependencies = [
    'pyyaml',
]


setup(
    name='confidence',
    version='0.0',
    author='Mattijs Ugen',
    author_email=codecs.encode('nxnvqvbg@hfref.abercyl.tvguho.pbz', 'rot-13'),
    description="Simple module to load and use configuration in a clean, 'pythonic' way.",
    long_description=readme,

    py_modules=['confidence'],
    install_requires=dependencies,

    classifiers=(
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Utilities',
    )
)
