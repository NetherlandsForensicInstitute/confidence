from collections.abc import Mapping
from enum import IntEnum
from itertools import chain, product
from os import environ, path

import yaml


class ConfigurationError(KeyError):
    """
    `KeyError` raised when merge conflicts are detected during `.Configuration`
    construction (see `.Configuration.__init__`) or retrieving an unavailable
    configured value when no default is supplied (see `.Configuration.get`).
    """
    pass


class _Conflict(IntEnum):
    overwrite = 0
    error = 1


def _merge(left, right, path=None, conflict=_Conflict.error):
    """
    Merges values in place from *right* into *left*.

    :param left: mapping to merge into
    :param right: mapping to merge from
    :param path: `list` of keys processed before (used for error reporting
        only, should only need to be provided by recursive calls)
    :param conflict: action to be taken on merge conflict, raising an error
        or overwriting an existing value
    :return: *left*, for convenience
    """
    path = path or []
    conflict = _Conflict(conflict)

    for key in right:
        if key in left:
            if isinstance(left[key], Mapping) and isinstance(right[key], Mapping):
                # recurse, merge left and right dict values, update path for current 'step'
                _merge(left[key], right[key], path + [key], conflict=conflict)
            elif left[key] != right[key]:
                if conflict is _Conflict.error:
                    # not both dicts we could merge, but also not the same, this doesn't work
                    raise ConfigurationError('merge conflict at {}'.format('.'.join(path + [key])))
                else:
                    # overwrite left value with right value
                    left[key] = right[key]
            # else: left[key] is already equal to right[key], no action needed
        else:
            # key not yet in left or not considering conflicts, simple addition of right's mapping to left
            left[key] = right[key]

    return left


def _split_keys(mapping, separator='.'):
    """
    Recursively walks *mapping* to split keys that contain the separator into
    nested mappings.

    :param mapping: the mapping to process
    :param separator: the character (sequence) to use as the separator between
        keys
    :return: a mapping where keys containing *separator* are split into nested
        mappings
    """
    result = {}

    for key, value in mapping.items():
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
    def __repr__(self):
        return '(raise)'

    __str__ = __repr__


# overwrite _NoDefault as an instance of itself
_NoDefault = _NoDefault()


class Configuration(Mapping):
    """
    A collection of configured values, retrievable as either `dict`-like items
    or attributes.
    """

    def __init__(self, *sources, separator='.'):
        """
        Create a new `.Configuration`, based on one or multiple source mappings.

        :param sources: source mappings to base this `.Configuration` on,
            ordered from least to most significant
        :param separator: the character (sequence) to use as the separator
            between keys
        """
        self._separator = separator

        self._source = {}
        for source in sources:
            # merge values from source into self._source, overwriting any corresponding keys
            _merge(self._source, _split_keys(source, separator=self._separator), conflict=_Conflict.overwrite)

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
        value = self._source
        steps_taken = []
        try:
            # walk through the values dictionary
            for step in path.split(self._separator):
                steps_taken.append(step)
                value = value[step]

            if as_type:
                return as_type(value)
            elif isinstance(value, Mapping):
                namespace = Configuration()
                namespace._source = value
                return namespace
            else:
                return value
        except KeyError:
            if default is not _NoDefault:
                return default
            else:
                raise ConfigurationError('no configuration for key {}'.format(self._separator.join(steps_taken)))

    def __getattr__(self, attr):
        """
        Gets a 'single step value', as either a configured value or a
        namespace-like object in the form of a `.Configuration` instance. An
        unconfigured value will return `.NotConfigured`, a 'safe' sentinel
        value.

        :param attr: the 'step' (key, attribute, …) to take
        :return: a value, as either an actual value or a `.Configuration`
            instance (`.NotConfigured` in case of an unconfigured 'step')
        """
        return self.get(attr, default=NotConfigured)

    def __len__(self):
        return len(self._source)

    def __getitem__(self, item):
        return self.get(item)

    def __iter__(self):
        return iter(self._source)

    def __dir__(self):
        return sorted(set(chain(super().__dir__(), self.keys())))


class NotConfigured(Configuration):
    """
    Sentinel value to signal there is no value for a requested key.
    """
    def __bool__(self):
        return False

    def __repr__(self):
        return '(not configured)'

    __str__ = __repr__


# overwrite NotConfigured as an instance of itself, a Configuration instance without any values
NotConfigured = NotConfigured({})


def load(*fps):
    """
    Read a `.Configuration` instance from file-like objects.

    :param fps: file-like objects (supporting ``.read()``)
    :return: a `.Configuration` instance providing values from *fps*
    :rtype: `.Configuration`
    """
    return Configuration(*(yaml.load(fp.read()) for fp in fps))


def loadf(*fnames):
    """
    Read a `.Configuration` instance from named files.

    :param fnames: name of the files to ``open()``
    :return: a `.Configuration` instance providing values from *fnames*
    :rtype: `.Configuration`
    """
    def readf(fname):
        with open(fname, 'r') as fp:
            return yaml.load(fp.read())

    return Configuration(*(readf(fname) for fname in fnames))


def loads(*strings):
    """
    Read a `.Configuration` instance from strings.

    :param strings: configuration contents
    :return: a `.Configuration` instance providing values from *strings*
    :rtype: `.Configuration`
    """
    return Configuration(*(yaml.load(string) for string in strings))


def read_envvars(name):
    """
    Read environment variables starting with ``NAME_``, where subsequent
    underscores are interpreted as namespaces.

    .. note::

        Environment variables are always `str`s, this function makes no effort
        to changes this. All values read from command line variables will be
        `str` instances.

    :param name: environment variable prefix to look for (without the ``_``)
    :return: a nested (possibly empty) `dict` with values read from
        environment variables
    """
    prefix = '{}_'.format(name)
    prefix_len = len(prefix)
    envvar_file = '{}_config_file'.format(name)
    # create a new mapping from environment values starting with the prefix (but stripped of that prefix)
    values = {var.lower()[prefix_len:]: value
              for var, value in environ.items()
              # TODO: document ignoring envvar_file
              if var.lower().startswith(prefix) and var.lower() != envvar_file}
    # TODO: envvar values can only be str, how do we configure non-str values?
    # provide it as a nested dict, treating _'s as separators, FOO_NS_KEY=bar resulting in {'ns': {'key': 'bar'}}
    return _split_keys(values, separator='_')


def read_envvar_file(name):
    """
    Read values from a file provided as a environment variable
    ``NAME_CONFIG_FILE``.

    :param name: environment variable prefix to look for (without the
        ``_CONFIG_FILE``)
    :return: a nested (possibly empty) `dict` with values read from file
    """
    envvar_file = environ.get('{}_config_file'.format(name).upper())
    if envvar_file:
        # envvar set, load value as file
        with open(envvar_file) as fp:
            return yaml.load(fp)
    else:
        # envvar not set, return an empty source
        return {}


# ordered sequence of name templates to load, in increasing significance
LOAD_ORDER = (
    '/etc/{name}.{extension}',
    '~/.{name}.{extension}',
    './{name}.{extension}',
    read_envvar_file,
    read_envvars,
)


def load_name(*names, load_order=LOAD_ORDER, extension='yaml'):
    """
    Read a `.Configuration` instance by name, trying to read from files in
    increasing significance. System-wide configuration locations are preceded
    by user locations, and again by local files.

    :param names: application or configuration set names, in increasing
        significance
    :param load_order: ordered list of name templates or `callable`s, in
        increasing order of significance
    :param extension: file extension to be used
    :return: a `.Configuration` instances providing values loaded from *names*
        in *load_order* ordering
    """
    def generate_sources():
        # argument order for product matters, for names "foo" and "bar":
        # /etc/foo.yaml before /etc/bar.yaml, but both of them before ~/.foo.yaml and ~/.bar.yaml
        for source, name in product(load_order, names):
            if callable(source):
                yield source(name)
            else:
                # expand user to turn ~/.name.yaml into /home/user/.name.yaml
                candidate = path.expanduser(source.format(name=name, extension=extension))
                if path.exists(candidate):
                    with open(candidate, 'r') as fd:
                        yield yaml.load(fd.read())

    return Configuration(*generate_sources())