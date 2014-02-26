from configuration import _merge


def test_merge_trivial():
    left = {'key': 'value'}
    right = {'another_key': 42}

    merged = _merge(left, right)

    assert len(merged) == 2, 'trivial merge of incorrect length'
    assert merged['key'] == 'value', 'trivial merge supplied wrong value'
    assert merged['another_key'] == 42, 'trivial merge supplied wrong value'


def test_merge_update():
    left = {'first': {'key': 1}}
    right = {'second': {'key': True}}

    merged = _merge(left, right)

    assert len(merged) == 2, 'update merge of incorrect length'
    assert len(merged['first']) == len(merged['second']) == 1, 'update merge values of incorrect length'
    assert merged['first']['key'] == 1, 'update merge supplied wrong value'
    assert merged['second']['key'], 'update merge supplied wrong value'


def test_merge_overlap():
    left = {'parent': {'first': 123, 'second': 456}}
    right = {'parent': {'third': 789, 'fourth': True}}

    merged = _merge(left, right)

    assert len(merged) == 1, 'overlapping merge of incorrect length'
    assert len(merged['parent']) == 4, 'value in overlapping merge of incorrect length'
    assert (merged['parent']['second'], merged['parent']['third']) == (456, 789), \
        'incorrect values in overlapping merge'


def test_merge_equal():
    left = {'parent': {'first': 1, 'second': 2}}
    right = {'parent': {'third': 3, 'first': 1}}  # parent.first == 1 in both operands

    merged = _merge(left, right)

    assert len(merged) == 1, 'equality merge of incorrect length'
    assert len(merged['parent']) == 3, 'equality merge value of incorrect length'
    assert merged['parent']['first'] == 1, 'equality merge supplied wrong value'


def test_merge_conflict():
    left = {'parent': {'first': 1, 'second': 2}}
    right = {'parent': {'third': 3, 'first': 4}}  # parent.first differs

    try:
        merged = _merge(left, right)
    except Exception as e:
        assert 'parent.first' in str(e), "conflict error didn't specify conflicting key"
    else:
        raise AssertionError('conflicting merge was accepted')
