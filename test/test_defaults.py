from configuration import Configuration


def test_constructor_defaults():
    subject = Configuration()
    assert subject.separator == '.'
    assert len(subject) == len(subject.values) == 0
    assert list(subject) == []
