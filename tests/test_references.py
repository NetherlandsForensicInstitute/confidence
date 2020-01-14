from os import path

import pytest

from confidence import Configuration, ConfigurationError, ConfiguredReferenceError, loadf, NotConfigured


test_files = path.join(path.dirname(__file__), 'files')


def test_reference_syntax():
    config = Configuration({
        'key1': '$(reference)',
        'key2': '${reference)',
        'key3': '${}',
        'key4': '$ {reference}',
        'key5': '#{reference}',
        'key_with_space ': 'value',
        'key with spaces': 'value2',
        'key6': '${key_with_space }',
        'key7': '${key with spaces}',
        'key8': '${key_with_space}',
    })

    assert config.reference is NotConfigured
    assert '$' in config.key1
    assert '$' in config.key2
    assert '$' in config.key3
    assert '$' in config.key4
    assert '#' in config.key5
    assert config.key6 == 'value'
    assert config.key7 == 'value2'

    with pytest.raises(ConfiguredReferenceError):
        assert not config.key8


def test_value_types():
    config = Configuration({
        'ns.str': 'string',
        'ns.int': 42,
        'ns.float': 2.0,
        'ns.bool': True,
        'ns.ref1': 'prefix ${ns.str} suffix',
        'ns.ref2': 'p${ns.int}s',
        'ns.ref3': '${ns.float}',
        'ns.ref4': '${ns.bool}',
    })

    assert config.ns.str == 'string'
    assert config.ns.ref1 == config.get('ns.ref1') == 'prefix string suffix'
    assert config.ns.ref2 == config.get('ns.ref2') == 'p42s'
    assert config.ns.ref3 == config.get('ns.ref3') == 2.0
    assert config.ns.ref4 == config.get('ns.ref4') is True


def test_multiple_references():
    config = Configuration({
        'key': 'A seemingly ${ns.word1}, ${ns.word2} sentence.',
        'ns.word1': 'full',
        'ns.word2': 'complete',
    })

    assert config.key == 'A seemingly full, complete sentence.'


def test_multi_level_reference():
    config = Configuration({
        'key': 'A ${ns.part1}',
        'ns.part1': 'seemingly full, ${ns.part2}.',
        'ns.part2': 'complete sentence',
    })

    assert config.ns.part2 == 'complete sentence'
    assert config.ns.part1 == 'seemingly full, complete sentence.'
    assert config.key == 'A seemingly full, complete sentence.'


def test_recursive_reference():
    config = Configuration({
        'ns': {'reference': 'final',
               'final': 'the actual value'},
        'wanted': '${ns.${ns.reference}}',
    })

    assert config.ns.final == 'the actual value'
    assert config.ns.reference == 'final'
    assert config.wanted == 'the actual value'


def test_sub_config_reference():
    config = Configuration({
        'key': 'string',
        'ns.test1': '${key}',
        'ns.test2': '${ns.test1}',
    })

    assert config.key == 'string'

    ns = config.ns
    assert ns.test1 == ns.get('test1') == 'string'
    assert ns.test2 == ns.get('test2') == 'string'

    ns = config.get('ns')
    assert ns.test1 == ns.get('test1') == 'string'
    assert ns.test2 == ns.get('test2') == 'string'


def test_reference_ns():
    config = Configuration({
        'key': '${ns}',
        'ns.key': 'string',
        'broken': 'no ${ns} inside',
    })

    assert config.ns.key == 'string'
    assert isinstance(config.key, Configuration)
    assert config.key.key == 'string'

    with pytest.raises(ConfiguredReferenceError) as e:
        assert not config.broken
    assert 'cannot insert namespace' in str(e.value)


def test_missing_reference():
    config = Configuration({
        'key': 'string',
        'template.working': '${key}',
        'template.missing': '${ns.key}',
    })

    assert config.key == 'string'
    assert config.template.working == 'string'

    with pytest.raises(ConfiguredReferenceError) as e:
        assert not config.template.missing
    assert 'ns.key' in str(e.value)

    with pytest.raises(ConfiguredReferenceError) as e:
        assert not config.get('template.missing')
    assert 'ns.key' in str(e.value)


def test_self_recursion():
    config = Configuration({
        'ns.key': '${ns.key}',
    })

    with pytest.raises(ConfigurationError) as e:
        assert not config.ns.key

    assert 'ns.key' in str(e.value) and 'recursive' in str(e.value)


def test_loop_recursion():
    config = Configuration({
        'ns.key': '${ns.ns.key}',
        'ns.ns.key': '${ns.key}',
    })

    with pytest.raises(ConfigurationError) as e:
        assert not config.ns.key

    assert 'ns.key' in str(e.value) and 'recursive' in str(e.value)


def test_references_from_file():
    config = loadf(path.join(test_files, 'complicated.yaml'))

    assert isinstance(config.a.simple.reference, Configuration)
    assert config.a.simple.reference.example == 'example'

    assert config.a.complicated.reference == 'value with a reference in it'


def test_missing_reference_during_merge():
    source1 = Configuration({'ns.key2': '${ns.key}'})  # reference should only be resolvable after merge
    source2 = {'ns.key': 'value'}

    config = Configuration(source1, source2)

    assert config.ns.key == config.ns.key2 == 'value'
