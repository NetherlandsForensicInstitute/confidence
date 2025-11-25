from dataclasses import FrozenInstanceError

import pytest

from confidence import Configuration, unwrap
from confidence.formats import JSON, TOML, YAML


@pytest.mark.parametrize('format', (JSON, TOML, YAML))
@pytest.mark.parametrize('value', (None, True, 1, 42.0, 'a string'))
def test_singular_value_roundtrip(format, value):
    if (format, value) == (TOML, None):
        # None / null / nil is not supported by the TOML spec, see https://github.com/toml-lang/toml/issues/30
        pytest.skip('None is unsupported for TOML format')

    assert format.loads(format.dumps(value)) == value


@pytest.mark.parametrize('format', (JSON, TOML, YAML, YAML(suffix='.conf', encoding='utf-32')))
@pytest.mark.parametrize(
    'value',
    (
        [],
        {},
        [1, 2, 'a'],
        {'a': 1, 'b': 42.0, 'c': {'d': 'str'}, 'e': [{'g': True}]},
        # nested configuration object should get unwrapped before serialization
        Configuration({'a.b.c': 42}),
        # serialization should not be trying to resolve references, this one would cause a recursion error if it does
        Configuration({'a.b': [1, 2, '${a}']}),
    ),
)
def test_multiple_values_roundtrip(format, value, tmp_path):
    fname = tmp_path / f'config{format.suffix}'

    format.dumpf(value, fname)
    assert format.loadf(fname) == unwrap(value)


def test_edit_format():
    format = JSON(encoding='iso-8859-1')

    assert format is not JSON
    assert format != JSON
    assert format.encoding == 'iso-8859-1'
    assert format == JSON(suffix='.json', encoding='iso-8859-1')

    with pytest.raises(FrozenInstanceError):
        YAML.suffix = '.yml'
