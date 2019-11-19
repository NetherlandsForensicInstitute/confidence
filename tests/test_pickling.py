import pickle

import pytest

from confidence.exceptions import NotConfiguredError
from confidence.models import Configuration, Missing, NotConfigured


def test_empty():
    subject = Configuration()

    reencoded = pickle.loads(pickle.dumps(subject))

    # not testing pickle itself, but if this returns the same instance, all of the other tests are meaningless
    assert subject is not reencoded
    assert subject == reencoded


def test_simple():
    subject = Configuration({'testing': 123})

    reencoded = pickle.loads(pickle.dumps(subject))

    assert subject.testing == reencoded.testing == 123
    assert subject.get('testing') == reencoded.get('testing') == 123
    assert subject.not_there is reencoded.not_there is NotConfigured
    assert reencoded._root is reencoded


def test_missing_error():
    subject = Configuration({'testing': 123}, missing=Missing.error)

    reencoded = pickle.loads(pickle.dumps(subject))

    assert subject.testing == reencoded.testing == 123
    with pytest.raises(NotConfiguredError):
        assert not reencoded.get('not_there')
    with pytest.raises(AttributeError):
        assert not reencoded.not_there


def test_missing_custom():
    subject = Configuration({'testing': 123}, missing=False)

    reencoded = pickle.loads(pickle.dumps(subject))

    assert subject.testing == reencoded.testing == 123
    assert subject.not_there is reencoded.not_there is False


def test_namespace():
    subject = Configuration({'ns1': {'ns2': {'key': 42}}})

    reencoded_ns1 = pickle.loads(pickle.dumps(subject.ns1))

    assert subject.ns1.ns2.key == reencoded_ns1.ns2.key == 42
    # looks odd, but make sure the reencoded namespace's root is able to reach the whole shebang
    assert reencoded_ns1._root.ns1.ns2.key == 42
    # reencoding should not lead to the exact same root instance, (…)
    assert reencoded_ns1._root is not subject.ns1._root
    # (…) but the reencoded instance should pass its own root through to other namespaces
    assert reencoded_ns1.ns2._root is reencoded_ns1._root
