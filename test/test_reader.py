import pytest
from yaml import load as load_yaml
from json import loads as load_json

from configuration import ConfigurationError, _get_reader


def test_get_default():
    assert _get_reader() == load_yaml


def test_get_named():
    assert _get_reader('yaml') is load_yaml
    assert _get_reader(reader='json') is load_json


def test_get_unknown():
    with pytest.raises(ConfigurationError) as e:
        _get_reader('blah')

    assert 'blah' in str(e.value)
    assert 'invalid reader' in str(e.value)


def test_get_callable():
    assert _get_reader(load_yaml) is load_yaml

    local_reader = lambda s: {'key': 'value'}
    assert _get_reader(local_reader) is local_reader
