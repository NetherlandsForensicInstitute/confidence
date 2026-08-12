from collections.abc import Mapping, Sequence
from unittest.mock import patch

import pytest

from confidence import NOT_CONFIGURED, Configuration, Missing


def test_empty():
    def run_test(config):
        assert config.key is NOT_CONFIGURED
        assert config.deeper.key is NOT_CONFIGURED
        assert '(keys=[])' in repr(config)

    run_test(Configuration())
    run_test(Configuration({}))


def test_value_types():
    config = Configuration(
        {
            'a_string': 'just',
            'an_int': 42,
            'a_float': 3.14,
            'a_boolean': False,
            'a_list': [1, 2, 3],
            'we_must': {'go_deeper': True},
        }
    )

    assert isinstance(config.a_string, str)
    assert isinstance(config.an_int, int)
    assert isinstance(config.a_float, float)
    assert isinstance(config.a_boolean, bool)
    assert isinstance(config.a_list, Sequence)
    assert isinstance(config.we_must, Mapping)

    assert 'a_string' in repr(config)
    assert 'just' not in repr(config)
    assert 'go_deeper' not in repr(config)


def test_not_configured():
    config = Configuration({'key': 'value'}, missing=Missing.SILENT)

    assert config.key == 'value'
    assert config.does_nope_exist is NOT_CONFIGURED
    assert config.does.nope.exist is NOT_CONFIGURED
    assert config.does_nope_exist is config.does.nope.exist
    assert not NOT_CONFIGURED
    assert bool(NOT_CONFIGURED) is False
    assert (config.does_not_exist or 'default') == 'default'
    assert 'not configured' in str(config.does_nope.exist)
    assert str(config.does_nope_exist) == repr(config.does.nope.exist)


def test_collisions():
    with patch('confidence.utils.LOG') as logger:
        config = Configuration({'key': 'value', 'keys': [1, 2], '_missing': 'error'})

    for collision in ('keys', '_missing'):
        logger.warning.assert_any_call(
            'key "%s" collides with a named member, use the get() method to retrieve its value', collision
        )

    assert config.key == 'value'
    assert callable(config.keys)


def test_dir():
    config = Configuration({'key1': 'value', 'key2': 5, 'namespace.key3': False})

    assert 'keys' in dir(config)
    assert 'key1' in dir(config)
    assert 'namespace' in dir(config)
    assert 'key3' in dir(config.namespace)


def test_assignments():
    config = Configuration({'key1': 'value', 'key2': 5, 'namespace.key3': False})

    config._private = 42
    config.__very_private = 43

    assert config._private == 42
    assert config.__very_private == 43

    with pytest.raises(AttributeError) as e:
        config.non_existent = True
    assert 'assignment not supported' in str(e.value) and 'non_existent' in str(e.value)

    with pytest.raises(AttributeError) as e:
        config.key1 = True
    assert 'assignment not supported' in str(e.value) and 'key1' in str(e.value)

    with pytest.raises(AttributeError) as e:
        config.namespace.key3 = True
    assert 'assignment not supported' in str(e.value) and 'key3' in str(e.value)

    with pytest.raises(AttributeError) as e:
        config.namespace.key4 = True
    assert 'assignment not supported' in str(e.value) and 'key4' in str(e.value)

    with pytest.raises(AttributeError) as e:
        config.non_existent.key6 = True
    assert 'assignment not supported' in str(e.value) and 'key6' in str(e.value)

    with pytest.raises(AttributeError) as e:
        config.we.must.go.deeper = True
    assert 'assignment not supported' in str(e.value) and 'deeper' in str(e.value)


def test_missing_error():
    config = Configuration({'key1': 'value', 'key2': 5, 'namespace.key3': False}, missing=Missing.ERROR)

    assert config.key1 == 'value'

    with pytest.raises(AttributeError) as e:
        assert config.namespace.key3 is False
        assert not config.key3

    assert 'key3' in str(e.value)


def test_missing_default():
    config = Configuration({'key1': 'value', 'key2': 5, 'namespace.key3': False}, missing='just a default')

    assert config.namespace.key3 is False
    assert config.key3 == 'just a default'
