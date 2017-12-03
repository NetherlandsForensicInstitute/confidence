from os import path

from configuration import Configuration, load, loadf, loads, NotConfigured


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


def test_load_default():
    with open(path.join(here, 'config.yaml')) as file:
        _assert_values(load(file))
    # as json is a subset of yaml, this should work just fine
    with open(path.join(here, 'config.json')) as file:
        _assert_values(load(file))


def test_load_yaml():
    with open(path.join(here, 'config.yaml')) as file:
        _assert_values(load(file))


def test_load_json():
    with open(path.join(here, 'config.json')) as file:
        _assert_values(load(file))


def test_load_multiple():
    with open(path.join(here, 'config.json')) as file1, open(path.join(here, 'config.yaml')) as file2:
        _assert_values(load(file1, file2))


def test_loads_default():
    _assert_values(loads(yaml_str))
    _assert_values(loads(json_str))


def test_loads_yaml():
    _assert_values(loads(yaml_str))


def test_loads_json():
    _assert_values(loads(json_str))


def test_loads_multiple():
    _assert_values(loads(json_str,
                         yaml_str))


def test_loadf_default():
    _assert_values(loadf(path.join(here, 'config.yaml')))
    _assert_values(loadf(path.join(here, 'config.json')))


def test_loadf_yaml():
    _assert_values(loadf(path.join(here, 'config.yaml')))


def test_loadf_json():
    _assert_values(loadf(path.join(here, 'config.json')))


def test_loadf_multiple():
    _assert_values(loadf(path.join(here, 'config.json'),
                         path.join(here, 'config.yaml')))
