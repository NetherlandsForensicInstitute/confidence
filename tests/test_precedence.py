from confidence import Configuration


def test_multiple_sources():
    subject = Configuration({'key': 'value'},
                            {'another.key': 42})

    assert len(subject) == 2
    assert subject.key == 'value'
    assert subject.another.key == 42


def test_overlapping_sources():
    subject = Configuration({'namespace.key': 'value'},
                            {'namespace.another.key': 42})

    assert len(subject) == 1
    assert subject.namespace.key == 'value'
    assert subject.namespace.another.key == 42


def test_single_overwrite():
    subject = Configuration({'key1': 1, 'key2': 2},
                            {'key2': 4, 'key3': 3})

    assert len(subject) == 3
    assert subject.key1 == 1
    assert subject.key2 == 4
    assert subject.key3 == 3


def test_multiple_overwrite():
    subject = Configuration({'key1': 1, 'namespace.key1': 1, 'namespace.key2': 2, 'key2': 2},
                            {'key2': 4, 'key3': 3, 'namespace.key1': 1},
                            {'key3': 6, 'namespace.key3': 3})

    assert len(subject) == 4
    assert subject.key1 == 1
    assert subject.key2 == 4
    assert subject.key3 == 6
    assert subject.namespace.key1 == 1
    assert subject.namespace.key2 == 2
    assert subject.namespace.key3 == 3


def test_overwrite_namespace_with_value():
    subject = Configuration({'key1': 1, 'namespace.key1': 1},
                            {'key2': 2, 'namespace': 'namespace'})

    assert len(subject) == 3
    assert subject.key1 == 1
    assert subject.key2 == 2
    assert subject.namespace == 'namespace'


def test_overwrite_value_with_namespace():
    subject = Configuration({'key2': 2, 'namespace': 'namespace'},
                            {'key1': 1, 'namespace.key1': 1})

    assert len(subject) == 3
    assert subject.key1 == 1
    assert subject.key2 == 2
    assert subject.namespace.key1 == 1
