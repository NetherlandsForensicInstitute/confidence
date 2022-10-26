import nox


nox.options.sessions = ('check', 'test')


all_supported_pythons = ('3.7', '3.8', '3.9', '3.10', '3.11', 'pypy3')
oldest_python = '3.7'
newest_python = '3.11'


@nox.session(python=newest_python)
def check(session):
    session.install('-r', 'requirements.txt')
    session.install('-r', 'check-requirements.txt')

    session.run('bandit', '--recursive', 'confidence/')
    session.run('flake8',
                '--max-line-length', '120',
                '--import-order-style', 'google',
                '--application-import-names', 'confidence',
                '--docstring-style', 'sphinx',
                'confidence/')
    session.run('mypy', 'confidence/')


@nox.session(python=all_supported_pythons)
def test(session):
    session.install('-r', 'requirements.txt')
    session.install('-r', 'test-requirements.txt')

    session.run('coverage', 'run',
                '--branch',
                '--source', 'confidence',
                '--module', 'py.test',
                '--strict-markers',
                'tests/')


@nox.session(python=newest_python)
def update(session):
    session.install('pip-tools')

    # compile runtime and test deps against the oldest supported python version, check deps aginst the newest
    session.run('pip-compile', '--upgrade', '--no-header', '--no-emit-index-url', '--pip-args', f'--python-version {oldest_python}', '--output-file', 'requirements.txt', 'setup.py')
    session.run('pip-compile', '--upgrade', '--no-header', '--no-emit-index-url', '--pip-args', f'--python-version {newest_python}', '--output-file', 'check-requirements.txt', 'check-requirements.in')
    session.run('pip-compile', '--upgrade', '--no-header', '--no-emit-index-url', '--pip-args', f'--python-version {oldest_python}', '--output-file', 'test-requirements.txt', 'test-requirements.in')


@nox.session(python=oldest_python)
def dist(session):
    session.install('wheel')

    session.run('python', 'setup.py', 'bdist_wheel')
