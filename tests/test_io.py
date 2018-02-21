from os import path
from unittest.mock import call, patch

from confidence import Configuration, load, load_name, loadf, loads, NotConfigured, read_envvar_file, read_envvars


test_files = path.join(path.dirname(__file__), 'files')

yaml_str = """
    key: value
    some:
        other.key:
            - 1
            - 2
            - 3

    some.thing: false
"""

json_str = """{
    "key": "value",
    "some.other.key": [1, 2, 3],
    "some.thing": false
}"""


def _assert_values(conf):
    assert conf.key == 'value'
    assert isinstance(conf.some, Configuration)
    assert conf.some.thing is False
    assert conf.does_not.exist is NotConfigured


def test_load_default():
    with open(path.join(test_files, 'config.yaml')) as file:
        _assert_values(load(file))
    # as json is a subset of yaml, this should work just fine
    with open(path.join(test_files, 'config.json')) as file:
        _assert_values(load(file))


def test_load_yaml():
    with open(path.join(test_files, 'config.yaml')) as file:
        _assert_values(load(file))


def test_load_json():
    with open(path.join(test_files, 'config.json')) as file:
        _assert_values(load(file))


def test_load_multiple():
    with open(path.join(test_files, 'config.json')) as file1, open(path.join(test_files, 'config.yaml')) as file2:
        _assert_values(load(file1, file2))


def test_loads_default():
    _assert_values(loads(yaml_str))
    _assert_values(loads(json_str))


def test_loads_yaml():
    _assert_values(loads(yaml_str))


def test_loads_json():
    _assert_values(loads(json_str))


def test_loads_multiple():
    _assert_values(loads(json_str,
                         yaml_str))


def test_loadf_default():
    _assert_values(loadf(path.join(test_files, 'config.yaml')))
    _assert_values(loadf(path.join(test_files, 'config.json')))


def test_loadf_yaml():
    _assert_values(loadf(path.join(test_files, 'config.yaml')))


def test_loadf_json():
    _assert_values(loadf(path.join(test_files, 'config.json')))


def test_loadf_multiple():
    _assert_values(loadf(path.join(test_files, 'config.json'),
                         path.join(test_files, 'config.yaml')))


def test_loadf_home():
    with patch('confidence.path') as mocked_path:
        # actual expanded home directory not under test, verify that it was called
        mocked_path.expanduser.return_value = path.join(test_files, 'config.yaml')
        _assert_values(loadf('~/config.yaml'))

    mocked_path.expanduser.assert_called_once_with('~/config.yaml')


def test_load_name_single():
    test_path = path.join(test_files, '{name}.{extension}')

    _assert_values(load_name('config', load_order=(test_path,)))
    _assert_values(load_name('config', load_order=(test_path,), extension='json'))


def test_load_name_multiple():
    test_path = path.join(test_files, '{name}.{extension}')

    # bar has precedence over foo
    subject = load_name('foo', 'fake', 'bar', load_order=(test_path,))

    assert len(subject.semi.overlapping) == 2
    assert subject.semi.overlapping.foo is True
    assert subject.semi.overlapping.bar is False
    assert subject.overlapping.fully == 'bar'

    # foo has precedence over bar
    subject = load_name('fake', 'bar', 'foo', load_order=(test_path,))

    assert len(subject.semi.overlapping) == 2
    assert subject.semi.overlapping.foo is True
    assert subject.semi.overlapping.bar is False
    assert subject.overlapping.fully == 'foo'


def test_load_name_order():
    env = {
        'HOME': '/home/user'
    }

    with patch('confidence.path') as mocked, patch('confidence.environ', env):
        mocked.expanduser.return_value = mocked
        # avoid actually opening files that might unexpectedly exist
        mocked.exists.return_value = False

        assert len(load_name('foo', 'bar')) == 0

    mocked.expanduser.assert_has_calls([
        call('/etc/foo.yaml'),
        call('/etc/bar.yaml'),
        call('~/.foo.yaml'),
        call('~/.bar.yaml'),
        call('./foo.yaml'),
        call('./bar.yaml'),
    ], any_order=False)


def test_load_name_envvars():
    env = {
        'FOO_KEY': 'foo',
        'FOO_NS_KEY': 'value',
        'BAR_KEY': 'bar',
    }

    with patch('confidence.environ', env):
        subject = load_name('foo', 'bar', load_order=(read_envvars,))

    assert subject.key == 'bar'
    assert subject.ns.key == 'value'


def test_load_name_envvar_file():
    env = {
        'FOO_CONFIG_FILE': path.join(test_files, 'foo.yaml'),
        'BAR_CONFIG_FILE': path.join(test_files, 'bar.yaml'),
    }

    with patch('confidence.environ', env):
        subject = load_name('foo', 'bar', load_order=(read_envvar_file,))

    assert len(subject.semi.overlapping) == 2
    assert subject.semi.overlapping.foo is True
    assert subject.semi.overlapping.bar is False
    assert subject.overlapping.fully == 'bar'


def test_load_name_overlapping_envvars():
    env = {
        'FOO_KEY': 'foo',
        'FOO_NS_KEY': 'value',
        'BAR_KEY': 'bar',
        'FOO_CONFIG_FILE': path.join(test_files, 'foo.yaml'),
        'BAR_CONFIG_FILE': path.join(test_files, 'bar.yaml'),
    }

    with patch('confidence.environ', env):
        subject = load_name('foo', 'bar', load_order=(read_envvar_file, read_envvars))

    assert subject.key == 'bar'
    assert subject.ns.key == 'value'
    assert subject.foo.config.file is NotConfigured
    assert subject.bar.config.file is NotConfigured
    assert subject.config.file is NotConfigured
    assert len(subject.semi.overlapping) == 2
    assert subject.semi.overlapping.foo is True
    assert subject.semi.overlapping.bar is False
    assert subject.overlapping.fully == 'bar'
