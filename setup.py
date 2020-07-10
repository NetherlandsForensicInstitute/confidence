import codecs
from os import path
from setuptools import find_packages, setup


here = path.abspath(path.dirname(__file__))


with open(path.join(here, 'README.md'), 'r', encoding='utf-8') as readme:
    # use the contents of the readme as the long_description for the module
    def strip_readme(file):
        line = file.readline()
        # drop content before the first header
        while not line.startswith('confidence'):
            line = file.readline()
        # drop section on installing
        while not line.startswith('installing'):
            yield line
            line = file.readline()

    readme = ''.join(strip_readme(readme))


with open(path.join(here, 'CHANGES.md'), 'r', encoding='utf-8') as changes:
    changes = changes.read()


dependencies = [
    'pyyaml',
]


setup(
    name='confidence',
    version='0.7',
    url='https://github.com/HolmesNL/confidence/',
    author='Netherlands Forensic Institute',
    author_email=codecs.encode('ubyzrfay@hfref.abercyl.tvguho.pbz', 'rot-13'),
    license='Apache Software License 2.0',
    description="Simple module to load and use configuration in a clean, 'pythonic' way.",
    keywords='configuration',
    long_description='\n\n'.join((readme, changes)),
    long_description_content_type='text/markdown',

    packages=find_packages(),
    install_requires=dependencies,

    classifiers=(
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Utilities',
    )
)
