from configuration import Configuration, NotConfigured


def test_empty():
    def run_test(subject):
        assert subject.key is NotConfigured
        assert subject.deeper.key is NotConfigured

    run_test(Configuration())
    run_test(Configuration({}))


def test_value_types():
    subject = Configuration({
        'a_string': 'just',
        'an_int': 42,
        'a_float': 3.14,
        'a_boolean': False,
        'a_list': [1, 2, 3],
        'we_must': {'go_deeper': True},
    })

    assert type(subject.a_string) is str
    assert type(subject.an_int) is int
    assert type(subject.a_float) is float
    assert type(subject.a_boolean) is bool
    assert type(subject.a_list) is list
    assert type(subject.we_must) is Configuration  # TODO: this test makes it look like a dict would be more logical...


def test_not_configured():
    subject = Configuration({'key': 'value'})

    assert subject.key == 'value'
    assert subject.does_nope_exist is NotConfigured
    assert subject.does.nope.exist is NotConfigured
    assert subject.does_nope_exist is subject.does.nope.exist
