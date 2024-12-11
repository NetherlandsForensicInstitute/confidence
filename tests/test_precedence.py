import pytest

from confidence import Configuration, Missing, NotConfigured, merge
from confidence.models import NoDefault


def test_multiple_sources():
    subject = Configuration({'key': 'value'},
                            {'another.key': 42})

    assert len(subject) == 2
    assert subject.key == 'value'
    assert subject.another.key == 42


def test_overlapping_sources():
    subject = Configuration({'namespace.key': 'value'},
                            {'namespace.another.key': 42})

    assert len(subject) == 1
    assert subject.namespace.key == 'value'
    assert subject.namespace.another.key == 42


def test_single_overwrite():
    subject = Configuration({'key1': 1, 'key2': 2},
                            {'key2': 4, 'key3': 3})

    assert len(subject) == 3
    assert subject.key1 == 1
    assert subject.key2 == 4
    assert subject.key3 == 3


def test_multiple_overwrite():
    subject = Configuration({'key1': 1, 'namespace.key1': 1, 'namespace.key2': 2, 'key2': 2},
                            {'key2': 4, 'key3': 3, 'namespace.key1': 1},
                            {'key3': 6, 'namespace.key3': 3})

    assert len(subject) == 4
    assert subject.key1 == 1
    assert subject.key2 == 4
    assert subject.key3 == 6
    assert subject.namespace.key1 == 1
    assert subject.namespace.key2 == 2
    assert subject.namespace.key3 == 3


def test_overwrite_multiple_merge():
    subject = original = Configuration({'key1': 1, 'namespace.key1': 1, 'namespace.key2': 2, 'key2': 2})
    subject |= {'key3': 6, 'namespace.key3': 3}

    # |= should *not* imply an in-place update
    assert subject is not original

    subject = subject | {'key2': 4, 'key3': 3, 'namespace.key1': 1}

    assert set(subject.keys()) == {'key1', 'namespace', 'key2', 'key3'}
    assert subject == (original | subject) == merge(original, original, subject, subject)


def test_overwrite_namespace_with_value():
    subject = Configuration({'key1': 1, 'namespace.key1': 1},
                            {'key2': 2, 'namespace': 'namespace'})

    assert len(subject) == 3
    assert subject.key1 == 1
    assert subject.key2 == 2
    assert subject.namespace == 'namespace'


def test_overwrite_value_with_namespace():
    subject = Configuration({'key2': 2, 'namespace': 'namespace'},
                            {'key1': 1, 'namespace.key1': 1})

    assert len(subject) == 3
    assert subject.key1 == 1
    assert subject.key2 == 2
    assert subject.namespace.key1 == 1


def test_merge_settings():
    source = {'key1': 42, 'key2': True}
    silent = Configuration(source, missing=Missing.SILENT)
    error = Configuration(source, missing=Missing.ERROR)
    value = Configuration(source, missing=5)

    assert merge(source, source)._missing is NotConfigured
    assert merge(source, source, missing=Missing.SILENT)._missing is NotConfigured
    assert merge(silent, source)._missing is (silent | source)._missing is NotConfigured
    assert merge(silent, error, value, missing=Missing.ERROR)._missing is NoDefault
    assert merge(error, source)._missing is (error | source)._missing is NoDefault
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
    assert NotConfigured | a == a
    assert a | NotConfigured == a
    assert NotConfigured | b == b
    assert b | NotConfigured == b

    with pytest.raises(TypeError):
        assert not Configuration(a) | 5
    with pytest.raises(TypeError):
        assert not 5 | Configuration(b)
