from collections import Mapping

from confidence import Configuration, NotConfigured


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
    assert isinstance(subject.a_list, list)
    assert isinstance(subject.we_must, Mapping)


def test_not_configured():
    subject = Configuration({'key': 'value'})

    assert subject.key == 'value'
    assert subject.does_nope_exist is NotConfigured
    assert subject.does.nope.exist is NotConfigured
    assert subject.does_nope_exist is subject.does.nope.exist
    assert not NotConfigured
    assert bool(NotConfigured) is False
    assert (subject.does_not_exist or 'default') == 'default'
    assert 'not configured' in str(subject.does_nope.exist)
    assert str(subject.does_nope_exist) == repr(subject.does.nope.exist)


def test_dir():
    subject = Configuration({'key1': 'value', 'key2': 5, 'namespace.key3': False})

    assert 'keys' in dir(subject)
    assert 'key1' in dir(subject)
    assert 'namespace' in dir(subject)
    assert 'key3' in dir(subject.namespace)
