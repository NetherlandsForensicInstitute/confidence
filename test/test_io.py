from os import path

from configuration import Configuration, load, loads, NotConfigured


here = path.dirname(__file__)

yaml_str = """
    key: value
    some:
        other.key:
            - 1
            - 2
            - 3

    some.thing: false
"""

json_str = """{
    "key": "value",
    "some.other.key": [1, 2, 3],
    "some.thing": false
}"""


def _assert_values(conf):
    assert conf.key == 'value'
    assert isinstance(conf.some, Configuration)
    assert conf.some.thing is False
    assert conf.does_not.exist is NotConfigured


def test_loads_default():
    _assert_values(loads(yaml_str))
    # as json is a subset of yaml, this should work identical
    _assert_values(loads(json_str))


def test_loads_yaml():
    _assert_values(loads(yaml_str, 'yaml'))


def test_loads_json():
    _assert_values(loads(json_str, 'json'))


def test_load_default():
    _assert_values(load(path.join(here, 'config.yaml')))
    _assert_values(load(path.join(here, 'config.json')))


def test_load_yaml():
    _assert_values(load(path.join(here, 'config.yaml'), 'yaml'))


def test_load_json():
    _assert_values(load(path.join(here, 'config.json'), 'json'))
