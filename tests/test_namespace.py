from collections.abc import Mapping, Sequence
from unittest.mock import patch

import pytest

from confidence import Configuration, Missing, NotConfigured


def test_empty():
    def run_test(subject):
        assert subject.key is NotConfigured
        assert subject.deeper.key is NotConfigured

    run_test(Configuration())
    run_test(Configuration({}))


def test_value_types():
    subject = Configuration({
        'a_string': 'just',
        'an_int': 42,
        'a_float': 3.14,
        'a_boolean': False,
        'a_list': [1, 2, 3],
        'we_must': {'go_deeper': True},
    })

    assert isinstance(subject.a_string, str)
    assert isinstance(subject.an_int, int)
    assert isinstance(subject.a_float, float)
    assert isinstance(subject.a_boolean, bool)
    assert isinstance(subject.a_list, Sequence)
    assert isinstance(subject.we_must, Mapping)


def test_not_configured():
    subject = Configuration({'key': 'value'}, missing=Missing.silent)

    assert subject.key == 'value'
    assert subject.does_nope_exist is NotConfigured
    assert subject.does.nope.exist is NotConfigured
    assert subject.does_nope_exist is subject.does.nope.exist
    assert not NotConfigured
    assert bool(NotConfigured) is False
    assert (subject.does_not_exist or 'default') == 'default'
    assert 'not configured' in str(subject.does_nope.exist)
    assert str(subject.does_nope_exist) == repr(subject.does.nope.exist)


def test_collisions():
    with patch('confidence.utils.warnings') as warnings:
        subject = Configuration({'key': 'value', 'keys': [1, 2], '_separator': '_'})

    for collision in ('keys', '_separator'):
        warnings.warn.assert_any_call('key {key} collides with a named member, use get() method to '
                                      'retrieve the value for {key}'.format(key=collision),
                                      UserWarning)

    assert subject.key == 'value'
    assert callable(subject.keys)
    assert subject._separator == '.'


def test_dir():
    subject = Configuration({'key1': 'value', 'key2': 5, 'namespace.key3': False})

    assert 'keys' in dir(subject)
    assert 'key1' in dir(subject)
    assert 'namespace' in dir(subject)
    assert 'key3' in dir(subject.namespace)


def test_assignments():
    subject = Configuration({'key1': 'value', 'key2': 5, 'namespace.key3': False})

    subject._private = 42
    subject.__very_private = 43

    assert subject._private == 42
    assert subject.__very_private == 43

    with pytest.raises(AttributeError) as e:
        subject.non_existent = True
    assert 'assignment not supported' in str(e.value) and 'non_existent' in str(e.value)

    with pytest.raises(AttributeError) as e:
        subject.key1 = True
    assert 'assignment not supported' in str(e.value) and 'key1' in str(e.value)

    with pytest.raises(AttributeError) as e:
        subject.namespace.key3 = True
    assert 'assignment not supported' in str(e.value) and 'key3' in str(e.value)

    with pytest.raises(AttributeError) as e:
        subject.namespace.key4 = True
    assert 'assignment not supported' in str(e.value) and 'key4' in str(e.value)

    with pytest.raises(AttributeError) as e:
        subject.non_existent.key6 = True
    assert 'assignment not supported' in str(e.value) and 'key6' in str(e.value)

    with pytest.raises(AttributeError) as e:
        subject.we.must.go.deeper = True
    assert 'assignment not supported' in str(e.value) and 'deeper' in str(e.value)


def test_missing_error():
    subject = Configuration({'key1': 'value', 'key2': 5, 'namespace.key3': False}, missing=Missing.error)

    assert subject.key1 == 'value'

    with pytest.raises(AttributeError) as e:
        assert subject.namespace.key3 is False
        assert not subject.key3

    assert 'key3' in str(e.value)


def test_missing_default():
    subject = Configuration({'key1': 'value', 'key2': 5, 'namespace.key3': False}, missing='just a default')

    assert subject.namespace.key3 is False
    assert subject.key3 == 'just a default'
