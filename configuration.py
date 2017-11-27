from collections import Mapping


class ConfigurationError(KeyError):
    """
    TODO: Document me.
    """
    pass


def _merge(left, right, _path=None):
    """
    TODO: Document me.
    """
    _path = _path or []

    for key in right:
        if key in left:
            if isinstance(left[key], Mapping) and isinstance(right[key], Mapping):
                # recurs, merge left and right dict values, update _path for current 'step'
                _merge(left[key], right[key], _path + [key])
            elif left[key] != right[key]:
                # not both dicts we could merge, but also not the same, this doesn't work
                raise ConfigurationError('merge conflict at {}'.format('.'.join(_path + [key])))
            # else: left[key] is already equal to right[key], no action needed
        else:
            # key not yet in left, simple addition of right's mapping to left
            left[key] = right[key]

    return left


def _split_keys(values, separator='.'):
    """
    TODO: Document me.
    """
    result = {}

    for key, value in values.items():
        if isinstance(value, Mapping):
            # recursively split key(s) in value
            value = _split_keys(value, separator)

        if separator in key:
            # update key to be the first part before the separator
            key, rest = key.split(separator, 1)
            # use rest as the new key of value, recursively split that and update value
            value = _split_keys({rest: value}, separator)

        # merge the result so far with the (possibly updated / fixed / split) current key and value
        _merge(result, {key: value})

    return result


class _NoDefault:
    def __str__(self):
        return '(raise)'
    __repr__ = __str__

# overwrite _NoDefault as an instance of itself
_NoDefault = _NoDefault()


class Configuration(Mapping):
    """
    TODO: Document me.
    """

    def __init__(self, values=None, separator='.'):
        """
        TODO: Document me.
        """
        self.values = _split_keys(values or {})
        self.separator = separator

    def get(self, path, default=_NoDefault, as_type=None):
        """
        Gets a value for the specified path.

        :param path: the configuration key to fetch a value for, steps
            separated by the separator supplied to the constructor (default
            ``.``)
        :param default: a value to return if no value is found for the
            supplied path (``None`` is allowed)
        :param as_type: an optional callable to apply to the value found for
            the supplied path (possibly raising exceptions of its own if the
            value can not be coerced to the expected type)
        :return: the value associated with the supplied configuration key, if
            available, or a supplied default value if the key was not found
        :raises ConfigurationError: when no value was found for *path* and
            *default* was not provided
        """
        value = self.values
        steps_taken = []
        try:
            # walk through the values dictionary
            for step in path.split(self.separator):
                steps_taken.append(step)
                value = value[step]

            return as_type(value) if as_type else value
        except KeyError:
            if default is not _NoDefault:
                return default
            else:
                raise ConfigurationError('no configuration for key {}'.format(self.separator.join(steps_taken)))

    def __getattr__(self, item):
        """
        TODO: Document me.
        """
        value = self.get(item, default=NotConfigured)
        if isinstance(value, Configuration):
            return value
        elif isinstance(value, Mapping):
            # deeper levels are treated as Configuration objects as well
            return Configuration(value)
        else:
            # value is not a dict, so it will either be an actual value or NotConfigured
            # in either case, it should be returned as provided
            return value

    def __len__(self):
        return len(self.values)

    def __getitem__(self, item):
        return self.get(item)

    def __iter__(self):
        return iter(self.values)


class NotConfigured(Configuration):
    """
    Sentinel value to signal there is no value for a requested key.
    """
    def __bool__(self):
        return False

    def __str__(self):
        return '(not configured)'

    __repr__ = __str__

# overwrite NotConfigured as an instance of itself
NotConfigured = NotConfigured()


_readers = {}

try:
    import yaml
    _readers['yaml'] = yaml.load
except ImportError:
    pass

try:
    import json
    _readers['json'] = json.loads
except ImportError:
    pass


def _get_reader(reader='yaml'):
    if isinstance(reader, str):
        instance = _readers.get(reader)
    else:
        instance = reader

    if not callable(instance):
        raise ConfigurationError('invalid reader: {}'.format(reader))

    return instance


def _do_load(stream, reader):
    return Configuration(reader(stream))


def load(fp, reader='yaml'):
    """
    Read a `.Configuration` instance from a file-like object.

    :param fp: file-like object (supporting ``.read()``)
    :param reader: the reader (`callable`) or reader type (`str`) to use
    :return: a `.Configuration` instance providing values from *fp*
    :rtype: `.Configuration`
    """
    return _do_load(fp.read(), _get_reader(reader))


def loadf(fname, reader='yaml'):
    """
    Read a `.Configuration` instance from a named file.

    :param fname: name of the file to ``open()``
    :param reader: the reader (`callable`) or reader type (`str`) to use
    :return: a `.Configuration` instance providing values from *fname*
    :rtype: `.Configuration`
    """
    reader = _get_reader(reader)
    with open(fname, 'r') as fp:
        return _do_load(fp.read(), reader)


def loads(s, reader='yaml'):
    """
    Read a `.Configuration` instance from a string.

    :param s: configuration content (a `str`)
    :param reader: the reader (`callable`) or reader type (`str`) to use
    :return: a `.Configuration` instance providing values from *s*
    :rtype: `.Configuration`
    """
    return _do_load(s, _get_reader(reader))
