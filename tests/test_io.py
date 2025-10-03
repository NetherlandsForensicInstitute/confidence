# ruff: noqa: PTH118, PTH123 (allow use of os.path to test pathlib usage)

from functools import partial
from os import path
from pathlib import Path
from unittest.mock import MagicMock, call, mock_open, patch

import pytest
import yaml

from confidence import (
    DEFAULT_LOAD_ORDER,
    Configuration,
    Locality,
    NotConfigured,
    load,
    load_name,
    loaders,
    loadf,
    loads,
)
from confidence.formats import JSON, TOML, YAML
from confidence.io import dump, dumpf, dumps, read_envvar_file, read_envvars, read_xdg_config_dirs, read_xdg_config_home


@pytest.fixture(autouse=True)
def unix_style_pathsep():
    # hard-code the path separator to unix style throughout the tests here for consistency
    with patch('confidence.io.pathsep', ':'):
        yield


@pytest.fixture
def tilde_home_user():
    def expanduser(self):
        return Path(str(self).replace('~', '/home/user'))

    with patch.object(Path, 'expanduser', expanduser):
        yield expanduser


json_str = """{
    "key": "value",
    "some": {
        "other.key": [1, 2, 3]
    },
    "some.thing": false
}"""

yaml_str = """
    key: value
    some:
        other.key:
            - 1
            - 2
            - 3

    some.thing: false
"""

toml_str = """
key = "value"

# a comment regarding the some table
[some]
other.key = [1, 2, 3]
thing = false
"""


class str_containing:  # noqa: N801
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


def test_load_defaults(test_files):
    with open(path.join(test_files, 'config.yaml')) as file:
        _assert_values(load(file))
    # as json is a subset of yaml, this should work just fine
    with open(path.join(test_files, 'config.json')) as file:
        _assert_values(load(file))


def test_load_json(test_files):
    with open(path.join(test_files, 'config.json')) as file:
        _assert_values(load(file, format=JSON))


def test_load_toml(test_files):
    with open(path.join(test_files, 'config.toml')) as file:
        _assert_values(load(file, format=TOML))


def test_load_yaml(test_files):
    with open(path.join(test_files, 'config.yaml')) as file:
        _assert_values(load(file, format=YAML))


def test_load_multiple(test_files):
    with open(path.join(test_files, 'config.json')) as file1, open(path.join(test_files, 'config.yaml')) as file2:
        # NB: JSON is valid YAML, the default format will read both files
        _assert_values(load(file1, file2))


def test_loads_defaults():
    _assert_values(loads(json_str))
    _assert_values(loads(yaml_str))
    # toml_str won't parse with the default format


def test_loads_json():
    _assert_values(loads(json_str, format=JSON))


def test_loads_yaml():
    _assert_values(loads(yaml_str, format=YAML))


def test_loads_toml():
    _assert_values(loads(toml_str, format=TOML))


def test_loads_multiple():
    _assert_values(loads(json_str, yaml_str))


def test_loadf_defaults(test_files):
    _assert_values(loadf(path.join(test_files, 'config.json')))
    _assert_values(loadf(path.join(test_files, 'config.yaml')))


def test_loadf_json(test_files):
    _assert_values(loadf(path.join(test_files, 'config.json')))  # NB: JSON is valid YAML, the default format does fit
    _assert_values(loadf(path.join(test_files, 'config.json'), format=JSON))


def test_loadf_toml(test_files):
    _assert_values(loadf(path.join(test_files, 'config.toml'), format=TOML))


def test_loadf_yaml(test_files):
    _assert_values(loadf(path.join(test_files, 'config.yaml')))
    _assert_values(loadf(path.join(test_files, 'config.yaml'), format=YAML))


def test_loadf_multiple(test_files):
    _assert_values(loadf(path.join(test_files, 'config.json'), path.join(test_files, 'config.yaml')))


def test_loadf_home(test_files):
    def expanduser(self):
        return Path(str(self).replace('~', str(test_files)))

    with patch.object(Path, 'expanduser', expanduser):
        _assert_values(loadf('~/config.yaml'))
        assert Path('~/config.yaml').expanduser().exists()


def test_loadf_default():
    assert not Path('/path/to/file-that-should-not-exist').exists()

    config = loadf('/path/to/file-that-should-not-exist', default={'a': 2})
    assert config.a == 2

    config = loadf('/path/to/file-that-should-not-exist', default=Configuration({'b': 2}))
    assert config.b == 2


def test_loadf_missing():
    assert not Path('/path/to/file-that-should-not-exist').exists()

    with pytest.raises(FileNotFoundError):
        loadf('/path/to/file-that-should-not-exist')


def test_loadf_empty(test_files):
    assert len(loadf(path.join(test_files, 'empty.yaml'))) == 0
    assert len(loadf(path.join(test_files, 'comments.yaml'))) == 0
    assert len(loadf(path.join(test_files, 'empty.yaml'), path.join(test_files, 'comments.yaml'))) == 0

    _assert_values(
        loadf(
            path.join(test_files, 'empty.yaml'),
            path.join(test_files, 'config.yaml'),
            path.join(test_files, 'comments.yaml'),
        )
    )


def test_load_name_single(test_files):
    test_path = path.join(test_files, '{name}{suffix}')

    _assert_values(load_name('config', load_order=(test_path,)))
    _assert_values(load_name('config', load_order=(test_path,), format=JSON))


def test_load_name_multiple(test_files):
    test_path = path.join(test_files, '{name}{suffix}')

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


def test_load_name_order(tilde_home_user):
    # override actual environment variables for testing purposes
    # (HOME is used for some XDG-specified locations, LOCALAPPDATA is used for windows-specific locations)
    env = {
        'HOME': '/home/user',
        'LOCALAPPDATA': 'C:/Users/user/AppData/Local',
        'FOO_TEST': '21',
        'BAR_TEST': '42',
    }

    with (
        patch('confidence.io.environ', env),
        patch('confidence.io.loadf', return_value=NotConfigured) as mocked_loadf,
    ):
        subject = load_name('foo', 'bar')
        assert len(subject) == 1
        assert subject.test == 42

    mocked_loadf.assert_has_calls(
        [
            call(Path('/etc/xdg/foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('/etc/xdg/bar.yaml'), format=YAML, default=NotConfigured),
            call(Path('/etc/foo/foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('/etc/bar/bar.yaml'), format=YAML, default=NotConfigured),
            call(Path('/etc/foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('/etc/bar.yaml'), format=YAML, default=NotConfigured),
            call(Path('/Library/Preferences/foo/foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('/Library/Preferences/bar/bar.yaml'), format=YAML, default=NotConfigured),
            call(Path('/Library/Preferences/foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('/Library/Preferences/bar.yaml'), format=YAML, default=NotConfigured),
            call(Path('/home/user/.config/foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('/home/user/.config/bar.yaml'), format=YAML, default=NotConfigured),
            # loadf is usually the one to expand ~ to /home/user here, but we've mocked it, so the value being passed
            # will still contain the ~
            call(Path('~/Library/Preferences/foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('~/Library/Preferences/bar.yaml'), format=YAML, default=NotConfigured),
            call(Path('C:/Users/user/AppData/Local/foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('C:/Users/user/AppData/Local/bar.yaml'), format=YAML, default=NotConfigured),
            call(Path('~/.foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('~/.bar.yaml'), format=YAML, default=NotConfigured),
            call(Path('./foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('./bar.yaml'), format=YAML, default=NotConfigured),
        ],
        any_order=False,
    )


def test_load_name_xdg_config_dirs():
    env = {
        'XDG_CONFIG_DIRS': '/etc/xdg-desktop/:/etc/not-xdg',
    }

    with (
        patch('confidence.io.environ', env),
        patch('confidence.io.loadf', return_value=NotConfigured) as mocked_loadf,
    ):
        assert len(load_name('foo', 'bar', load_order=(read_xdg_config_dirs,))) == 0

    mocked_loadf.assert_has_calls(
        [
            call(Path('/etc/not-xdg/foo.yaml'), Path('/etc/xdg-desktop/foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('/etc/not-xdg/bar.yaml'), Path('/etc/xdg-desktop/bar.yaml'), format=YAML, default=NotConfigured),
        ],
        any_order=False,
    )


def test_load_name_xdg_config_dirs_fallback():
    with (
        patch('confidence.io.loadf', return_value=NotConfigured) as mocked_loadf,
        patch('confidence.io.environ', {}),
    ):
        assert len(load_name('foo', 'bar', load_order=(read_xdg_config_dirs,))) == 0

    mocked_loadf.assert_has_calls(
        [
            call(Path('/etc/xdg/foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('/etc/xdg/bar.yaml'), format=YAML, default=NotConfigured),
        ],
        any_order=False,
    )


def test_load_name_xdg_config_home(tilde_home_user):
    env = {'XDG_CONFIG_HOME': '/home/user/.not-config', 'HOME': '/home/user'}

    with (
        patch('confidence.io.environ', env),
        patch('confidence.io.loadf', return_value=NotConfigured) as mocked_loadf,
    ):
        assert len(load_name('foo', 'bar', load_order=(read_xdg_config_home,))) == 0

    mocked_loadf.assert_has_calls(
        [
            call(Path('/home/user/.not-config/foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('/home/user/.not-config/bar.yaml'), format=YAML, default=NotConfigured),
        ],
        any_order=False,
    )


def test_load_name_xdg_config_home_fallback(tilde_home_user):
    env = {'HOME': '/home/user'}

    with (
        patch('confidence.io.environ', env),
        patch('confidence.io.loadf', return_value=NotConfigured) as mocked_loadf,
    ):
        assert len(load_name('foo', 'bar', load_order=(read_xdg_config_home,))) == 0

    mocked_loadf.assert_has_calls(
        [
            call(Path('/home/user/.config/foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('/home/user/.config/bar.yaml'), format=YAML, default=NotConfigured),
        ],
        any_order=False,
    )


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

    with patch('confidence.io.environ', {'KEY_FOO': 'foo', 'BAR_CONFIG_FILE': '/tmp/bar.conf'}):
        # neither environment variable should be hit here
        assert not load_name('foo', 'bar', load_order=(read_envvars,))


def test_load_name_envvar_file(test_files):
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


def test_load_name_overlapping_envvars(test_files):
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


def test_load_name_envvar_dir(tilde_home_user):
    env = {'PROGRAMDATA': 'C:/ProgramData', 'APPDATA': 'D:/Users/user/AppData/Roaming'}

    # only the envvar dir loaders are partials in DEFAULT_LOAD_ORDER
    load_order = [loader for loader in DEFAULT_LOAD_ORDER if isinstance(loader, partial)]

    with (
        patch('confidence.io.environ', env),
        patch('confidence.io.loadf', return_value=NotConfigured) as mocked_loadf,
    ):
        assert len(load_name('foo', 'bar', load_order=load_order)) == 0

    mocked_loadf.assert_has_calls(
        [
            call(Path('C:/ProgramData/foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('C:/ProgramData/bar.yaml'), format=YAML, default=NotConfigured),
            call(Path('D:/Users/user/AppData/Roaming/foo.yaml'), format=YAML, default=NotConfigured),
            call(Path('D:/Users/user/AppData/Roaming/bar.yaml'), format=YAML, default=NotConfigured),
        ],
        any_order=False,
    )


def test_load_name_deprecated_extension():
    loader = MagicMock()

    with pytest.warns(DeprecationWarning, match='extension argument'):
        load_name('app', extension='yml', load_order=[loader])
    loader.assert_called_once_with('app', YAML(suffix='.yml'))

    with pytest.raises(ValueError, match='format and extension'):
        load_name('app', extension='jsn', format=JSON)


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
    with patch.object(Path, 'open', mock_open()) as mocked_open:
        dumpf(Configuration({'ns.key1': True, 'ns.key2': None}), '/path/to/dumped.yaml')

    mocked_open.assert_called_once_with('wt', encoding='utf-8')
    write = mocked_open().write
    for s in ('ns', 'key1', 'key2', 'null'):
        write.assert_any_call(str_containing(s))


@pytest.mark.parametrize('value', (123, 16.0, 'abc', True, False, None, [1, 2, 3], {'a': 1, 'b': 'c'}))
def test_dump_roundtrip(value, tmp_path):
    with (tmp_path / 'config.yaml').open('wt') as fp:
        dump(value, fp)
    with (tmp_path / 'config.yaml').open('rt') as fp:
        assert YAML.load(fp) == value


@pytest.mark.parametrize('value', (123, 16.0, 'abc', True, False, None, [1, 2, 3], {'a': 1, 'b': 'c'}))
def test_dumps_roundtrip(value):
    encoded = dumps(value)
    assert yaml.safe_load(encoded) == value
    assert '...' not in encoded


@pytest.mark.parametrize('value', (123, 16.0, 'abc', True, False, None, [1, 2, 3], {'a': 1, 'b': 'c'}))
def test_dumpf_roundtrip(value, tmp_path):
    dumpf(value, tmp_path / 'config.yaml')

    with open(tmp_path / 'config.yaml', 'r') as in_file:
        assert yaml.safe_load(in_file) == value


def test_dumpf_deprecated_encoding(tmp_path):
    with pytest.warns(DeprecationWarning, match='encoding argument'):
        dumpf({'a': 1}, tmp_path / 'dumpf.yaml', encoding='utf-32')

    with pytest.raises(ValueError, match="use format's encoding"):
        dumpf({'a': 1}, tmp_path / 'dumpf.yaml', format=JSON, encoding='utf-32')
