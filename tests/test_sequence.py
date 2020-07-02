from collections.abc import Mapping, Sequence
from os import path

import pytest

from confidence import loadf


test_files = path.join(path.dirname(__file__), 'files')


@pytest.fixture
def complicated_config():
    return loadf(path.join(test_files, 'complicated.yaml'))


def test_configured_sequence(complicated_config):
    assert isinstance(complicated_config.different.types, Sequence)
    assert complicated_config.different.types[0] == 'a string'
    assert complicated_config.different.types[1] is True
    assert complicated_config.different.types[2] == 42.0
    assert complicated_config.different.types[5][0] == 1
    assert complicated_config.different.types[5][3] == 4


def test_sequence_mapping(complicated_config):
    assert isinstance(complicated_config.different.types[3], Mapping)
    assert complicated_config.different.types[3].also == 'a mapping'
    assert isinstance(complicated_config.different.types[4], Mapping)
    assert complicated_config.different.types[4].maybe == 'another mapping, for fun'


def test_nested_sequence_mapping(complicated_config):
    assert isinstance(complicated_config.different.types[3].containing.surprise, Sequence)
    assert complicated_config.different.types[3].containing.surprise[0] == 'another'


def test_deep_reference(complicated_config):
    ns = complicated_config.different.types[3].containing.surprise[1]

    assert isinstance(ns, Mapping)
    assert ns.sequence_with == 'a mapping inside it, with a reference (mind = blown)'
