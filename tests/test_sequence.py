from collections.abc import Mapping, Sequence

import pytest

from confidence import Configuration, loadf


@pytest.fixture
def complicated_config(test_files):
    return loadf(test_files / 'complicated.yaml')


def test_configured_sequence(complicated_config):
    assert isinstance(complicated_config.different.types, Sequence)
    assert complicated_config.different.types[0] == 'a string'
    assert complicated_config.different.types[1] is True
    assert complicated_config.different.types[2] == 42.0
    assert complicated_config.different.types[5][0] == 1
    assert complicated_config.different.types[5][3] == 4

    assert "'a string', True, 42.0" in repr(complicated_config.different.types)


def test_sequence_mapping(complicated_config):
    assert isinstance(complicated_config.different.types[3], Mapping)
    assert complicated_config.different.types[3].also == 'a mapping'
    assert isinstance(complicated_config.different.types[4], Mapping)
    assert complicated_config.different.types[4].maybe == 'another mapping, for fun'


def test_nested_sequence_mapping(complicated_config):
    assert isinstance(complicated_config.different.types[3].containing.surprise, Sequence)
    assert complicated_config.different.types[3].containing.surprise[0] == 'another'


def test_sequence_reference(complicated_config):
    seq = complicated_config.different.sequence

    assert isinstance(seq, Sequence)
    assert seq[0] == 'simple value'
    assert seq[1] == 'example'
    assert seq[2] == 'value with a reference in it'
    assert seq[3].example == 'example'


def test_deep_reference(complicated_config):
    ns = complicated_config.different.types[3].containing.surprise[1]

    assert isinstance(ns, Mapping)
    assert ns.sequence_with == 'a mapping inside it, with a reference (mind = blown)'


def test_sequence_slice(complicated_config):
    sequence = complicated_config.different.types[1:4]

    assert len(sequence) == 3
    assert sequence[0] is True
    assert sequence[1] == 42.0
    assert sequence[2].also == 'a mapping'


def test_addition(complicated_config):
    sequence = complicated_config.different.types

    assert len(sequence + [1, 2, 3]) == 9
    assert not isinstance(sequence + [1, 2, 3], list)
    assert len([1, 2, 3] + sequence) == 9
    assert isinstance([1, 2, 3] + sequence, list)
    assert len(sequence + (1, 2, 3)) == 9
    assert len((1, 2, 3) + sequence) == 9
    assert isinstance((1, 2, 3) + sequence, tuple)

    for value in ('str', 42):
        with pytest.raises(TypeError):
            assert sequence + value
        with pytest.raises(TypeError):
            assert value + sequence


def test_addition_wrap(complicated_config):
    sequence = complicated_config.different.types

    assert (sequence + [1, 2, 3])[3].containing.surprise[
        1
    ].sequence_with == 'a mapping inside it, with a reference (mind = blown)'
    assert ((1, 2, 3) + sequence)[6].containing.surprise[
        1
    ].sequence_with == 'a mapping inside it, with a reference (mind = blown)'

    mapping = {'a': {'mapping': 42}}
    sequence = sequence + [1, 2, mapping, 4]
    assert sequence[-2].a.mapping == 42


def test_repr(complicated_config):
    sequence = complicated_config.different.sequence

    assert 'mapping(' not in repr(sequence)
    assert 'keys=' not in repr(sequence)
    assert '[...]' not in repr(sequence)
    assert '${' in repr(sequence)

    assert 'mapping(keys=[' in repr(sequence + [{'namespaces': 'honking great idea'}])
    assert 'honking' not in repr(sequence + [{'namespaces': 'honking great idea'}])
    # any mapping-like object should be represented as its keys
    assert repr(sequence + [{'namespaces': 'honking great idea'}]) == repr(
        sequence + [Configuration({'namespaces': 'honking great idea'})]
    )

    assert '[...]' in repr(sequence + [[1, 2, 42]])
    assert '42' not in repr(sequence + [[1, 2, 42]])
    # any sequence-like object should be represented as [...]
    # (this includes a recursive reference, even though that shouldn't happen in practice)
    assert repr(sequence + [[1, 2, 42]]) == repr(sequence + [(2, 4, 8)]) == repr(sequence + [sequence])
