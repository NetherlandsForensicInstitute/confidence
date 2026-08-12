import pytest

from confidence import NOT_CONFIGURED, Configuration, Missing, merge
from confidence.models import NO_DEFAULT


def test_multiple_sources():
    config = Configuration({'key': 'value'}, {'another.key': 42})

    assert len(config) == 2
    assert config.key == 'value'
    assert config.another.key == 42


def test_overlapping_sources():
    config = Configuration({'namespace.key': 'value'}, {'namespace.another.key': 42})

    assert len(config) == 1
    assert config.namespace.key == 'value'
    assert config.namespace.another.key == 42


def test_single_overwrite():
    config = Configuration({'key1': 1, 'key2': 2}, {'key2': 4, 'key3': 3})

    assert len(config) == 3
    assert config.key1 == 1
    assert config.key2 == 4
    assert config.key3 == 3


def test_multiple_overwrite():
    config = Configuration(
        {'key1': 1, 'namespace.key1': 1, 'namespace.key2': 2, 'key2': 2},
        {'key2': 4, 'key3': 3, 'namespace.key1': 1},
        {'key3': 6, 'namespace.key3': 3},
    )

    assert len(config) == 4
    assert config.key1 == 1
    assert config.key2 == 4
    assert config.key3 == 6
    assert config.namespace.key1 == 1
    assert config.namespace.key2 == 2
    assert config.namespace.key3 == 3


def test_overwrite_multiple_merge():
    config = original = Configuration({'key1': 1, 'namespace.key1': 1, 'namespace.key2': 2, 'key2': 2})
    config |= {'key3': 6, 'namespace.key3': 3}

    # |= should *not* imply an in-place update
    assert config is not original

    config = config | {'key2': 4, 'key3': 3, 'namespace.key1': 1}

    assert set(config.keys()) == {'key1', 'namespace', 'key2', 'key3'}
    assert config == (original | config) == merge(original, original, config, config)


def test_overwrite_namespace_with_value():
    config = Configuration({'key1': 1, 'namespace.key1': 1}, {'key2': 2, 'namespace': 'namespace'})

    assert len(config) == 3
    assert config.key1 == 1
    assert config.key2 == 2
    assert config.namespace == 'namespace'


def test_overwrite_value_with_namespace():
    config = Configuration({'key2': 2, 'namespace': 'namespace'}, {'key1': 1, 'namespace.key1': 1})

    assert len(config) == 3
    assert config.key1 == 1
    assert config.key2 == 2
    assert config.namespace.key1 == 1


def test_merge_settings():
    source = {'key1': 42, 'key2': True}
    silent = Configuration(source, missing=Missing.SILENT)
    error = Configuration(source, missing=Missing.ERROR)
    value = Configuration(source, missing=5)

    assert merge(source, source)._missing is NOT_CONFIGURED
    assert merge(source, source, missing=Missing.SILENT)._missing is NOT_CONFIGURED
    assert merge(silent, source)._missing is (silent | source)._missing is NOT_CONFIGURED
    assert merge(silent, error, value, missing=Missing.ERROR)._missing is NO_DEFAULT
    assert merge(error, source)._missing is (error | source)._missing is NO_DEFAULT
    assert merge(value, source)._missing == (value | source)._missing == 5

    with pytest.raises(ValueError):
        assert not merge(source, silent, error)
    with pytest.raises(ValueError):
        assert not silent | error
    with pytest.raises(ValueError):
        assert not value | error


def test_merge_direction():
    a = {'key': 'a'}
    b = {'key': 'b'}

    assert (Configuration(a) | b).key == 'b'
    assert (a | Configuration(b)).key == 'b'
    # NotConfigured should support the operator, but never contribute content
    assert NOT_CONFIGURED | a == a
    assert a | NOT_CONFIGURED == a
    assert NOT_CONFIGURED | b == b
    assert b | NOT_CONFIGURED == b

    with pytest.raises(TypeError):
        assert not Configuration(a) | 5
    with pytest.raises(TypeError):
        assert not 5 | Configuration(b)
