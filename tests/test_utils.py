import warnings
from datetime import date

import pytest

from confidence.utils import Conflict, merge, merge_into, split_keys


def test_merge_trivial():
    left = {'key': 'value'}
    right = {'another_key': 42}

    merged = merge_into(left, right)

    assert len(merged) == 2, 'trivial merge of incorrect length'
    assert merged['key'] == 'value', 'trivial merge supplied wrong value'
    assert merged['another_key'] == 42, 'trivial merge supplied wrong value'


def test_merge_update():
    left = {'first': {'key': 1}}
    right = {'second': {'key': True}}

    merged = merge_into(left, right)

    assert len(merged) == 2, 'update merge of incorrect length'
    assert len(merged['first']) == len(merged['second']) == 1, 'update merge values of incorrect length'
    assert merged['first']['key'] == 1, 'update merge supplied wrong value'
    assert merged['second']['key'], 'update merge supplied wrong value'


def test_merge_overlap():
    left = {'parent': {'first': 123, 'second': 456}}
    right = {'parent': {'third': 789, 'fourth': True}}

    merged = merge_into(left, right)

    assert len(merged) == 1, 'overlapping merge of incorrect length'
    assert len(merged['parent']) == 4, 'value in overlapping merge of incorrect length'
    assert (merged['parent']['second'], merged['parent']['third']) == (456, 789), (
        'incorrect values in overlapping merge'
    )


def test_merge_equal():
    left = {'parent': {'first': 1, 'second': 2}}
    right = {'parent': {'third': 3, 'first': 1}}  # parent.first == 1 in both operands

    merged = merge_into(left, right)

    assert len(merged) == 1, 'equality merge of incorrect length'
    assert len(merged['parent']) == 3, 'equality merge value of incorrect length'
    assert merged['parent']['first'] == 1, 'equality merge supplied wrong value'


def test_merge_conflict():
    left = {'parent': {'first': 1, 'second': 2}}
    right = {'parent': {'third': 3, 'first': 4}}  # parent.first differs

    try:
        _ = merge_into(left, right)
    except Exception as e:
        assert 'parent.first' in str(e), "conflict error didn't specify conflicting key"
    else:
        raise AssertionError('conflicting merge was accepted')


def test_merge_conflict_overwrite():
    left = {'parent': {'first': 1, 'second': 2}}
    right = {'parent': {'third': 3, 'first': 4}}  # parent.first differs

    merged = merge_into(left, right, conflict=Conflict.OVERWRITE)

    assert len(merged) == 1
    assert len(merged['parent']) == 3
    assert merged['parent']['first'] == 4


def test_split_none():
    subject = {'key': 'value', 'another_key': 123}

    separated = split_keys(subject)

    assert subject == separated


def test_split_trivial():
    subject = {'dotted.key': 42}

    separated = split_keys(subject)

    assert separated['dotted']['key'] == 42


def test_split_multiple():
    subject = {'dotted.key': 123, 'another.dotted.key': 456}

    separated = split_keys(subject)

    assert len(separated) == 2
    assert separated['dotted']['key'] == 123
    assert separated['another']['dotted']['key'] == 456


def test_split_overlap_simple():
    subject = {'dotted.key': 123, 'dotted.something_else': 456}

    separated = split_keys(subject)

    assert len(separated) == 1
    assert len(separated['dotted']) == 2
    assert separated['dotted']['something_else'] == 456


def test_split_overlap_complex():
    subject = {
        'dotted': {'key': 1},
        'dotted.something_else': {'again': 2},
        'dotted.something_else.entirely': 3,
        'key.thing': {'key': 4},
        'key': {'thing.another_key': 5},
    }

    separated = split_keys(subject)

    assert separated == {
        'dotted': {'key': 1, 'something_else': {'again': 2, 'entirely': 3}},
        'key': {'thing': {'key': 4, 'another_key': 5}},
    }


def test_split_key_types():
    subject = {'ns.1234.key': 42, 'ns': {1234: {'key2': 43}}}

    with pytest.raises(ValueError) as e:
        assert not split_keys(subject)

    assert '1234' in str(e.value)
    assert 'int' in str(e.value)

    subject = {'ns.2019-04-01.key': 42, 'ns': {date(2019, 4, 1): {'key2': 43}}}

    with pytest.raises(ValueError) as e:
        assert not split_keys(subject)

    assert '2019-04-01' in str(e.value)
    assert 'datetime.date' in str(e.value)


def test_merge_deprecation():
    with warnings.catch_warnings(record=True) as warned:
        assert merge({}, {'a': 5}) == {'a': 5}

    assert len(warned) == 1
    assert issubclass(warned[0].category, DeprecationWarning)
    assert 'renamed' in str(warned[0].message)
