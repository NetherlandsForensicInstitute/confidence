from confidence import NOT_CONFIGURED, Configuration, dumps, loads
from confidence.models import ConfigurationSequence


def test_constructor_defaults():
    config = Configuration()

    assert config._missing == NOT_CONFIGURED
    assert len(config) == len(config._source) == 0
    assert list(config) == []


def test_wrapped_source():
    left = Configuration({'a': 'a', 'b': [2, 2]})
    right = Configuration({'a': [1], 'b': Configuration({'c': 42})})

    config = Configuration({'left': left, 'middle': right.a, 'right': right})

    assert not isinstance(config._source['left'], Configuration)
    assert not isinstance(config._source['middle'], ConfigurationSequence)
    assert not isinstance(config._source['right']['b'], Configuration)
    assert not isinstance(config._source['right']['a'], ConfigurationSequence)

    assert config.right.b.c == 42
    assert len(left.b) == len(config.left.b) == 2
    assert len(right.a) == len(config.middle) == 1
    assert config._source == loads(dumps(config))._source
