import codecs
from os import path
from setuptools import find_packages, setup


here = path.abspath(path.dirname(__file__))


with open(path.join(here, 'README.rst'), 'r', encoding='utf-8') as readme:
    # use the contents of the readme as the long_description for the module
    # strip the first line (no need for repo badges on PyPI)
    readme.readline()
    readme = readme.read()


with open(path.join(here, 'CHANGES.rst'), 'r', encoding='utf-8') as changes:
    changes = changes.read()


dependencies = [
    'pyyaml',
]


setup(
    name='confidence',
    version='0.6',
    url='https://github.com/HolmesNL/confidence/',
    author='Netherlands Forensic Institute',
    author_email=codecs.encode('ubyzrfay@hfref.abercyl.tvguho.pbz', 'rot-13'),
    license='Apache Software License 2.0',
    description="Simple module to load and use configuration in a clean, 'pythonic' way.",
    keywords='configuration',
    long_description='\n\n'.join((readme, changes)),

    packages=find_packages(),
    install_requires=dependencies,

    classifiers=(
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Utilities',
    )
)
