from functools import partial
from itertools import cycle
from os import path
import pytest
from unittest.mock import call, mock_open, patch

from confidence import Configuration, DEFAULT_LOAD_ORDER, load, load_name, loaders, loadf, loads, Locality, NotConfigured
from confidence.io import dumpf, dumps, read_envvar_file, read_envvars, read_xdg_config_dirs, read_xdg_config_home


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


class str_containing:
    def __init__(self, substr):
        self._substr = substr

    def __eq__(self, other):
        return isinstance(other, str) and self._substr in other

    def __repr__(self):
        return f'string containing "{self._substr}"'


def _assert_values(conf):
    assert conf.key == 'value'
    assert isinstance(conf.some, Configuration)
    assert conf.some.thing is False
    assert conf.does_not.exist is NotConfigured


def _patched_expanduser(value):
    return value.replace('~', '/home/user')


@pytest.fixture
def broken_open():
    errors = cycle((FileNotFoundError, IOError, PermissionError))

    def broken(*args, **kwargs):
        raise next(errors)

    return broken


def test_load_defaults():
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


def test_loads_defaults():
    _assert_values(loads(yaml_str))
    _assert_values(loads(json_str))


def test_loads_yaml():
    _assert_values(loads(yaml_str))


def test_loads_json():
    _assert_values(loads(json_str))


def test_loads_multiple():
    _assert_values(loads(json_str,
                         yaml_str))


def test_loadf_defaults():
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
    with patch('confidence.io.path') as mocked_path:
        # actual expanded home directory not under test, verify that it was called
        mocked_path.expanduser.return_value = path.join(test_files, 'config.yaml')
        _assert_values(loadf('~/config.yaml'))

    mocked_path.expanduser.assert_called_once_with('~/config.yaml')


def test_loadf_default():
    with patch('confidence.io.path') as mocked_path:
        mocked_path.expanduser.side_effect = _patched_expanduser

        config = loadf('/path/to/file', default={'a': 2})
        assert config.a == 2

        config = loadf('/path/to/file', default=Configuration({'b': 2}))
        assert config.b == 2


def test_loadf_missing():
    with patch('confidence.io.path') as mocked_path:
        mocked_path.expanduser.side_effect = _patched_expanduser
        with pytest.raises(FileNotFoundError):
            loadf('/path/to/file')


def test_loadf_empty():
    assert len(loadf(path.join(test_files, 'empty.yaml'))) == 0
    assert len(loadf(path.join(test_files, 'comments.yaml'))) == 0
    assert len(loadf(path.join(test_files, 'empty.yaml'),
                     path.join(test_files, 'comments.yaml'))) == 0

    _assert_values(loadf(path.join(test_files, 'empty.yaml'),
                         path.join(test_files, 'config.yaml'),
                         path.join(test_files, 'comments.yaml')))


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


def test_load_name_order(broken_open):
    env = {
        'HOME': '/home/user',
        'LOCALAPPDATA': 'C:/Users/user/AppData/Local'
    }

    with patch('confidence.io.path') as mocked_path, patch('confidence.io.open', side_effect=broken_open) as mocked_open, patch('confidence.io.environ', env):
        # hard-code user-expansion, unmock join, unmock pathsep
        mocked_path.expanduser.side_effect = _patched_expanduser
        mocked_path.join.side_effect = path.join
        mocked_path.pathsep = path.pathsep

        assert len(load_name('foo', 'bar')) == 0

    mocked_open.assert_has_calls([
        call('/etc/xdg/foo.yaml', 'r'),
        call('/etc/xdg/bar.yaml', 'r'),
        call('/etc/foo/foo.yaml', 'r'),
        call('/etc/bar/bar.yaml', 'r'),
        call('/etc/foo.yaml', 'r'),
        call('/etc/bar.yaml', 'r'),
        call('/Library/Preferences/foo/foo.yaml', 'r'),
        call('/Library/Preferences/bar/bar.yaml', 'r'),
        call('/Library/Preferences/foo.yaml', 'r'),
        call('/Library/Preferences/bar.yaml', 'r'),
        call('/home/user/.config/foo.yaml', 'r'),
        call('/home/user/.config/bar.yaml', 'r'),
        call('/home/user/Library/Preferences/foo.yaml', 'r'),
        call('/home/user/Library/Preferences/bar.yaml', 'r'),
        call('C:/Users/user/AppData/Local/foo.yaml', 'r'),
        call('C:/Users/user/AppData/Local/bar.yaml', 'r'),
        call('/home/user/.foo.yaml', 'r'),
        call('/home/user/.bar.yaml', 'r'),
        call('./foo.yaml', 'r'),
        call('./bar.yaml', 'r'),
    ], any_order=False)


def test_load_name_xdg_config_dirs(broken_open):
    env = {
        'XDG_CONFIG_DIRS': '/etc/xdg-desktop/:/etc/not-xdg',
    }

    with patch('confidence.io.path') as mocked_path, patch('confidence.io.open', side_effect=broken_open) as mocked_open, patch('confidence.io.environ', env):
        # hard-code path separator, unmock join
        mocked_path.expanduser.side_effect = _patched_expanduser
        mocked_path.pathsep = ':'
        mocked_path.join.side_effect = path.join
        # avoid actually opening files that might unexpectedly exist
        mocked_path.exists.return_value = False

        assert len(load_name('foo', 'bar', load_order=(read_xdg_config_dirs,))) == 0

    mocked_open.assert_has_calls([
        # this might not be ideal (/etc/not-xdg should maybe show up twice first), but also not realistic…
        call('/etc/not-xdg/foo.yaml', 'r'),
        call('/etc/xdg-desktop/foo.yaml', 'r'),
        call('/etc/not-xdg/bar.yaml', 'r'),
        call('/etc/xdg-desktop/bar.yaml', 'r'),
    ], any_order=False)


def test_load_name_xdg_config_dirs_fallback():
    with patch('confidence.io.path') as mocked_path, patch('confidence.io.loadf') as mocked_loadf, patch('confidence.io.environ', {}):
        # hard-code path separator, unmock join
        mocked_path.expanduser.side_effect = _patched_expanduser
        mocked_path.pathsep = ':'
        mocked_path.join.side_effect = path.join
        mocked_path.exists.return_value = True

        assert len(load_name('foo', 'bar', load_order=(read_xdg_config_dirs,))) == 0

    mocked_loadf.assert_has_calls([
        call('/etc/xdg/foo.yaml', default=NotConfigured),
        call('/etc/xdg/bar.yaml', default=NotConfigured),
    ], any_order=False)


def test_load_name_xdg_config_home(broken_open):
    env = {
        'XDG_CONFIG_HOME': '/home/user/.not-config',
        'HOME': '/home/user'
    }

    with patch('confidence.io.path') as mocked_path, patch('confidence.io.open', side_effect=broken_open) as mocked_open, patch('confidence.io.environ', env):
        # hard-code user-expansion, unmock join
        mocked_path.expanduser.side_effect = _patched_expanduser
        mocked_path.join.side_effect = path.join
        # avoid actually opening files that might unexpectedly exist
        mocked_path.exists.return_value = False

        assert len(load_name('foo', 'bar', load_order=(read_xdg_config_home,))) == 0

    mocked_open.assert_has_calls([
        call('/home/user/.not-config/foo.yaml', 'r'),
        call('/home/user/.not-config/bar.yaml', 'r'),
    ], any_order=False)


def test_load_name_xdg_config_home_fallback():
    env = {
        'HOME': '/home/user'
    }

    with patch('confidence.io.path') as mocked_path, patch('confidence.io.loadf') as mocked_loadf, patch('confidence.io.environ', env):
        # hard-code user-expansion, unmock join
        mocked_path.expanduser.side_effect = _patched_expanduser
        mocked_path.join.side_effect = path.join
        mocked_path.exists.return_value = True
        mocked_loadf.return_value = NotConfigured

        assert len(load_name('foo', 'bar', load_order=(read_xdg_config_home,))) == 0

    mocked_loadf.assert_has_calls([
        call('/home/user/.config/foo.yaml', default=NotConfigured),
        call('/home/user/.config/bar.yaml', default=NotConfigured),
    ], any_order=False)


def test_load_name_envvars():
    env = {
        'FOO_KEY': 'foo',
        'FOO_NS_KEY': 'value',
        'FOO_TYPES_NUM': '42',
        'BAR_KEY': 'bar',
        'BAR_N__S_KEY': 'space',
        'BAR_TYPES_MAYBE': 'yes',
    }

    with patch('confidence.io.environ', env):
        subject = load_name('foo', 'bar', load_order=(read_envvars,))

    assert subject.key == 'bar'
    assert subject.ns.key == 'value'
    assert subject.n_s.key == 'space'
    assert subject.types.num == 42
    assert subject.types.maybe is True


def test_load_name_envvar_file():
    env = {
        'FOO_CONFIG_FILE': path.join(test_files, 'foo.yaml'),
        'BAR_CONFIG_FILE': path.join(test_files, 'bar.yaml'),
    }

    with patch('confidence.io.environ', env):
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

    with patch('confidence.io.environ', env):
        subject = load_name('foo', 'bar', load_order=loaders(Locality.ENVIRONMENT))

    assert subject.key == 'bar'
    assert subject.ns.key == 'value'
    assert subject.foo.config.file is NotConfigured
    assert subject.bar.config.file is NotConfigured
    assert subject.config.file is NotConfigured
    assert len(subject.semi.overlapping) == 2
    assert subject.semi.overlapping.foo is True
    assert subject.semi.overlapping.bar is False
    assert subject.overlapping.fully == 'bar'


def test_load_name_envvar_dir():
    env = {
        'PROGRAMDATA': 'C:/ProgramData',
        'APPDATA': 'D:/Users/user/AppData/Roaming'
    }

    # only the envvar dir loaders are partials in DEFAULT_LOAD_ORDER
    load_order = [loader for loader in DEFAULT_LOAD_ORDER if isinstance(loader, partial)]

    with patch('confidence.io.path') as mocked_path, patch('confidence.io.loadf') as mocked_loadf, patch('confidence.io.environ', env):
        # hard-code user-expansion, unmock join
        mocked_path.expanduser.side_effect = _patched_expanduser
        mocked_path.join.side_effect = path.join
        mocked_path.exists.return_value = True
        mocked_loadf.return_value = NotConfigured

        assert len(load_name('foo', 'bar', load_order=load_order)) == 0

    mocked_loadf.assert_has_calls([
        call('C:/ProgramData/foo.yaml', default=NotConfigured),
        call('C:/ProgramData/bar.yaml', default=NotConfigured),
        call('D:/Users/user/AppData/Roaming/foo.yaml', default=NotConfigured),
        call('D:/Users/user/AppData/Roaming/bar.yaml', default=NotConfigured),
    ], any_order=False)


def test_dumps():
    subject = dumps(Configuration({'ns.key': 42}))

    assert 'ns:' in subject
    assert 'key: 42' in subject
    assert '{' not in subject and '}' not in subject

    subject = dumps(Configuration({'ns.key1': True, 'ns.key2': None}))

    assert subject.count('ns') == 1
    assert 'key1: true' in subject
    assert 'key2: null' in subject
    assert '{' not in subject and '}' not in subject


def test_dumpf():
    with patch('confidence.io.open', mock_open()) as mocked:
        dumpf(Configuration({'ns.key1': True, 'ns.key2': None}), '/path/to/dumped.yaml')

    mocked.assert_called_once_with('/path/to/dumped.yaml', 'wb')
    write = mocked().write
    for s in ('ns', 'key1', 'key2', 'null'):
        write.assert_any_call(str_containing(s))
