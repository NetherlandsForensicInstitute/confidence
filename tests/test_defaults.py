from configuration import Configuration


def test_constructor_defaults():
    subject = Configuration()
    assert subject._separator == '.'
    assert len(subject) == len(subject._source) == 0
    assert list(subject) == []
