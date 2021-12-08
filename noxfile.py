import nox


nox.options.sessions = ('check', 'tests')


all_supported_pythons = ('3.6', '3.7', '3.8', '3.9', '3.10', 'pypy3')
oldest_python = '3.6'
newest_python = '3.10'


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


@nox.session(python=oldest_python)
def update_deps(session):
    session.install('pip-tools')

    session.run('pip-compile', '--upgrade', '--no-header', '--output-file', 'requirements.txt', 'setup.py')
    session.run('pip-compile', '--upgrade', '--no-header', '--output-file', 'check-requirements.txt', 'check-requirements.in')
    session.run('pip-compile', '--upgrade', '--no-header', '--output-file', 'test-requirements.txt', 'test-requirements.in')


@nox.session(python=oldest_python)
def dist(session):
    session.install('wheel')

    session.run('python', 'setup.py', 'bdist_wheel')
