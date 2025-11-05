import string

from confidence import Configuration, NotConfigured, dumps, loads
from confidence.models import ConfigurationSequence


def test_constructor_defaults():
    subject = Configuration()

    assert subject._missing == NotConfigured
    assert len(subject) == len(subject._source) == 0
    assert list(subject) == []


def test_wrapped_source():
    left = Configuration({'a': 'a', 'b': [2, 2]})
    right = Configuration({'a': [1], 'b': Configuration({'c': 42})})

    subject = Configuration({'left': left, 'middle': right.a, 'right': right})

    assert not isinstance(subject._source['left'], Configuration)
    assert not isinstance(subject._source['middle'], ConfigurationSequence)
    assert not isinstance(subject._source['right']['b'], Configuration)
    assert not isinstance(subject._source['right']['a'], ConfigurationSequence)

    assert subject.right.b.c == 42
    assert len(left.b) == len(subject.left.b) == 2
    assert len(right.a) == len(subject.middle) == 1
    assert subject._source == loads(dumps(subject))._source


def _items_dict(items):
    return {item: {item: 42} for item in items}


def test_benchmark_init_no_overlap(benchmark):
    a = _items_dict(string.ascii_lowercase)
    b = _items_dict(string.ascii_uppercase)

    assert benchmark(Configuration, a, b) == a | b


def test_benchmark_init_partial_overlap(benchmark):
    a = _items_dict(string.ascii_letters)
    b = _items_dict(string.ascii_lowercase)

    assert benchmark(Configuration, a, b) == a


def test_benchmark_init_full_overlap(benchmark):
    a = _items_dict(string.ascii_letters)
    b = _items_dict(string.ascii_letters)

    assert benchmark(Configuration, a, b) == a == b
