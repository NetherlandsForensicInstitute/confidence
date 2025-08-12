from collections.abc import Mapping, Sequence

import pytest

from confidence import Configuration, loadf
from confidence.models import NoDefault


def test_empty():
    def run_test(subject):
        assert subject.get('path.without.value', default=None) is None
        assert subject.get('another.path.without.value', default=4) == 4
        assert subject.get('some_long.path') is None
        with pytest.raises(KeyError, match='some_long'):
            subject['some_long']
        with pytest.raises(KeyError, match='some_long') as e:
            subject['some_long.path']
        assert 'path' not in str(e.value)

    run_test(Configuration())
    run_test(Configuration({}))


def test_value_types():
    def run_test(subject, key, expected_type):
        assert isinstance(subject.get(key), expected_type), f'key {key} not of type {expected_type}'

    run_test(Configuration({'just': 'string'}), 'just', str)
    run_test(Configuration({'a': 42}), 'a', int)
    run_test(Configuration({'simple': 3.14}), 'simple', float)
    run_test(Configuration({'silly': False}), 'silly', bool)
    run_test(Configuration({'test': [1, 2, 3]}), 'test', Sequence)
    run_test(Configuration({'case': {'surprise!': None}}), 'case', Mapping)
    run_test(Configuration({'we_must': {'go_deeper': True}}), 'we_must.go_deeper', bool)


def test_as_type():
    subject = Configuration({'as_int': 5, 'as_str': '5'})

    assert subject.get('as_int') == 5
    assert subject.get('as_str') == '5'
    assert subject.get('as_str', as_type=str) == '5'
    assert subject.get('as_str', as_type=int) == 5
    assert subject.get('as_str', as_type=bool) is True
    assert subject.get('as_str', as_type=lambda value: int(value) - 2) == 3


def test_no_default_doc_friendly():
    assert 'raise' in repr(NoDefault)


def test_key_types_from_file(test_files):
    config = loadf(test_files / 'complicated.yaml')

    assert isinstance(config.get('a.complicated.2019'), Configuration)
    assert config.get('a.complicated.2019.a') == 'a'
    assert config.get('a.complicated.2019.b') == 'b'
