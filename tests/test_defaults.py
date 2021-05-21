from confidence import Configuration, NotConfigured


def test_constructor_defaults():
    subject = Configuration()
    assert subject._missing == NotConfigured
    assert len(subject) == len(subject._source) == 0
    assert list(subject) == []
