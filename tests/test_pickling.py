import pickle

import pytest

from confidence.models import NOT_CONFIGURED, Configuration, Missing


def test_empty():
    config = Configuration()

    reencoded = pickle.loads(pickle.dumps(config))

    # not testing pickle itself, but if this returns the same instance, all of the other tests are meaningless
    assert config is not reencoded
    assert config == reencoded


def test_simple():
    config = Configuration({'testing': 123})

    reencoded = pickle.loads(pickle.dumps(config))

    assert config.testing == reencoded.testing == 123
    assert config.get('testing') == reencoded.get('testing') == 123
    assert config.not_there is reencoded.not_there is NOT_CONFIGURED
    assert reencoded._root is reencoded


def test_not_configured():
    assert pickle.loads(pickle.dumps(NOT_CONFIGURED)) is NOT_CONFIGURED


def test_missing_error():
    config = Configuration({'testing': 123}, missing=Missing.ERROR)

    reencoded = pickle.loads(pickle.dumps(config))

    assert config.testing == reencoded.testing == 123
    assert reencoded.get('not_there') is None  # should *not* trigger the missing setting
    with pytest.raises(AttributeError):
        assert not reencoded.not_there


def test_missing_custom():
    config = Configuration({'testing': 123}, missing=False)

    reencoded = pickle.loads(pickle.dumps(config))

    assert config.testing == reencoded.testing == 123
    assert config.not_there is reencoded.not_there is False


def test_namespace():
    config = Configuration({'ns1': {'ns2': {'key': 42}}})

    reencoded_ns1 = pickle.loads(pickle.dumps(config.ns1))

    assert config.ns1.ns2.key == reencoded_ns1.ns2.key == 42
    # looks odd, but make sure the reencoded namespace's root is able to reach the whole shebang
    assert reencoded_ns1._root.ns1.ns2.key == 42
    # reencoding should not lead to the exact same root instance, (…)
    assert reencoded_ns1._root is not config.ns1._root
    # (…) but the reencoded instance should pass its own root through to other namespaces
    assert reencoded_ns1.ns2._root is reencoded_ns1._root
