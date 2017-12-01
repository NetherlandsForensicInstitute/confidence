from configuration import Configuration


def test_constructor_defaults():
    subject = Configuration(None)
    assert subject.separator == '.'
    assert len(subject) == len(subject.values) == 0
    assert list(subject) == []
