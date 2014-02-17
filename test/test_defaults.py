from configuration import Configuration


def test_constructor_defaults():
    subject = Configuration()
    assert subject.separator == '.'
    assert len(subject.values) == 0
