from dataclasses import FrozenInstanceError

import pytest

from confidence.formats import JSON, YAML


@pytest.mark.parametrize('format', (JSON, YAML))
@pytest.mark.parametrize('value', (None, True, 1, 42.0, 'a string'))
def test_singular_value_roundtrip(format, value):
    assert format.loads(format.dumps(value)) == value


@pytest.mark.parametrize('format', (JSON, YAML, YAML(suffix='.conf', encoding='utf-32')))
@pytest.mark.parametrize('value', ([], {}, [1, 2, 'a'], {'a': 1, 'b': 42.0, 'c': {'d': 'str'}}))
def test_multiple_values_roundtrip(format, value, tmp_path):
    fname = tmp_path / f'config{format.suffix}'

    format.dumpf(value, fname)
    assert format.loadf(fname) == value


def test_edit_format():
    format = JSON(encoding='iso-8859-1')

    assert format is not JSON
    assert format != JSON
    assert format.encoding == 'iso-8859-1'
    assert format == JSON(suffix='.json', encoding='iso-8859-1')

    with pytest.raises(FrozenInstanceError):
        YAML.suffix = '.yml'
