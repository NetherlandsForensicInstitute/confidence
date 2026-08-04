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
