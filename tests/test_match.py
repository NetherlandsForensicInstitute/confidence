from collections.abc import Sequence

import pytest

from confidence import Configuration


def test_match_mapping_simple():
    config = Configuration({'a': 12, 'b': 34})

    match config:
        case {}:
            pass
        case _:
            pytest.fail()

    match config:
        case {'a': twelve}:
            assert twelve == 12
        case _:
            pytest.fail()

    match config:
        case {'a': 12, 'b': 34}:
            pass
        case _:
            pytest.fail()

    match config:
        case {'a': _, 'b': _, 'c': _}:
            pytest.fail()
        case _:
            pass


def test_match_mapping_complex():
    config = Configuration({'a': {'b': 12, 'c': 34}}, {'d': False, 'a.e.f.g': 42})

    match config:
        case {'a.b': twelve}:
            assert config.a.b == twelve == 12
        case _:
            pytest.fail()

    match config:
        case {'a.e.f.g': forty_two}:
            assert config.a.e.f.g == forty_two == 42
        case _:
            pytest.fail()

    match config:
        case {'a': {'b': twelve, 'e.f.g': forty_two}}:
            assert config.a.b == twelve == 12 and config.a.e.f.g == forty_two == 42
        case _:
            pytest.fail()

    match config:
        case {'a': {'b': twelve}, 'a.e.f.g': forty_two}:
            assert config.a.b == twelve == 12 and config.a.e.f.g == forty_two == 42
        case _:
            pytest.fail()


def test_match_sequence_simple():
    config = Configuration({'a': [1, 2, 3], 'b': []})

    match config:
        case {'a': [*nums]}:
            # TODO: a ConfigurationSequence is not equal to a similar sequence
            #       (though a list and a tuple are not equal either, so maybe that's ok?)
            assert list(config.a) == nums == [1, 2, 3]
        case _:
            pytest.fail()

    match config:
        case {'b': [] as empty}:
            # TODO: two empty ConfigurationSequences are not equal
            assert list(config.b) == list(empty)
        case _:
            pytest.fail()

    match config.a:
        case [1, 2, 3]:
            pass
        case _:
            pytest.fail()


def test_match_sequence_complex():
    config = Configuration({'a': [1, 2, '${b.c}'], 'b': {'c': 3, 'd': '${a}'}})

    match config:
        case {'a': [1, 2, c]}:
            assert c == 3
        case _:
            pytest.fail()

    match config:
        case {'b.d': [head, *tail]}:
            assert head == 1
            assert tail == [2, 3]
        case _:
            pytest.fail()

    match config:
        case {'a': Sequence(), 'b.d': [1, 2, 3]}:
            pass
        case _:
            pytest.fail()
