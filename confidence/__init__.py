from collections.abc import Mapping
from enum import Enum, IntEnum
from functools import partial
from itertools import chain, product
from os import environ, path
import re
import warnings

import yaml


class ConfigurationError(KeyError):
    pass


class MergeConflictError(ConfigurationError):
    """
    Error raised during loading configuration sources that conflict internally.
    """
    def __init__(self, *args, key):
        super().__init__(*args)
        self.conflict = key


class NotConfiguredError(ConfigurationError):
    """
    Error raised when a requested configuration key is unavailable and no
    default / fallback value is provided.
    """
    def __init__(self, *args, key):
        super().__init__(*args)
        self.key = key


class ConfiguredReferenceError(ConfigurationError):
    """
    Error raised a referenced configuration key is unavailable.
    """
    def __init__(self, *args, key):
        super().__init__(*args)
        self.key = key


class _Conflict(IntEnum):
    overwrite = 0
    error = 1


class Missing(Enum):
    silent = 'silent'  #: return `.NotConfigured` for unconfigured keys, avoiding errors
    error = 'error'  #: raise an `AttributeError` for unconfigured keys


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
                    conflict_path = '.'.join(path + [key])
                    raise MergeConflictError('merge conflict at {}'.format(conflict_path), key=conflict_path)
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

        if key in _COLLIDING_KEYS:
            # warn about configured keys colliding with Configuration members
            warnings.warn('key {key} collides with member of Configuration type, use get() method to retrieve the '
                          'value for {key}'.format(key=key),
                          UserWarning)

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

    # match a reference as ${key.to.be.resolved}
    _reference_pattern = re.compile(r'\${(?P<path>[^}]+?)}')

    def __init__(self, *sources, separator='.', missing=Missing.silent):
        """
        Create a new `.Configuration`, based on one or multiple source mappings.

        :param sources: source mappings to base this `.Configuration` on,
            ordered from least to most significant
        :param separator: the character(s) to use as the separator between keys
        :param missing: policy to be used when a configured key is missing,
            either as a `.Missing` instance or a default value
        """
        self._separator = separator
        self._missing = missing
        self._root = self

        if isinstance(self._missing, Missing):
            self._missing = {Missing.silent: NotConfigured,
                             Missing.error: _NoDefault}[missing]

        self._source = {}
        for source in sources:
            if source:
                # merge values from source into self._source, overwriting any corresponding keys
                _merge(self._source, _split_keys(source, separator=self._separator), conflict=_Conflict.overwrite)

    def _resolve(self, value):
        match = self._reference_pattern.search(value)
        references = set()
        try:
            while match:
                path = match.group('path')
                if path in references:
                    raise ConfiguredReferenceError(
                        'cannot resolve recursive reference {path}'.format(path=path),
                        key=path
                    )

                # avoid resolving references recursively (breaks reference tracking)
                reference = self._root.get(path, resolve_references=False)

                if match.span(0) != (0, len(value)):
                    # matched a reference inside of another value (template)
                    if isinstance(reference, Configuration):
                        raise ConfiguredReferenceError(
                            'cannot insert namespace at {path} into referring value'.format(path=path),
                            key=path
                        )

                    # render the template containing the referenced value
                    value = '{start}{reference}{end}'.format(
                        start=value[:match.start(0)],
                        reference=reference,
                        end=value[match.end(0):]
                    )
                else:
                    # value is only a reference, avoid rendering a template (keep referenced value type)
                    value = reference

                # track that we've seen path
                references.add(path)
                # either keep finding references or stop resolving and return value
                if isinstance(value, str):
                    match = self._reference_pattern.search(value)
                else:
                    match = None

            return value
        except NotConfiguredError as e:
            raise ConfiguredReferenceError(
                'unable to resolve referenced key {reference}'.format(reference=match.group('path')),
                key=e.key
            ) from e

    def get(self, path, default=_NoDefault, as_type=None, resolve_references=True):
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
        :param resolve_references: whether to resolve references in values
        :return: the value associated with the supplied configuration key, if
            available, or a supplied default value if the key was not found
        :raises ConfigurationError: when no value was found for *path* and
            *default* was not provided or a reference could not be resolved
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
                # create an instance of our current type, copying 'configured' properties / policies
                namespace = type(self)(separator=self._separator, missing=self._missing)
                namespace._source = value
                # carry the root object from namespace to namespace, references are always resolved from root
                namespace._root = self._root
                return namespace
            elif resolve_references and isinstance(value, str):
                # only resolve references in str-type values (the only way they can be expressed)
                return self._resolve(value)
            else:
                return value
        except ConfiguredReferenceError:
            # also a KeyError, but this one should bubble to caller
            raise
        except KeyError as e:
            if default is not _NoDefault:
                return default
            else:
                missing_key = self._separator.join(steps_taken)
                raise NotConfiguredError('no configuration for key {}'.format(missing_key), key=missing_key) from e

    def __getattr__(self, attr):
        """
        Gets a 'single step value', as either a configured value or a
        namespace-like object in the form of a `.Configuration` instance. An
        unconfigured value will return `.NotConfigured`, a 'silent' sentinel
        value.

        :param attr: the 'step' (key, attribute, …) to take
        :return: a value, as either an actual value or a `.Configuration`
            instance (`.NotConfigured` in case of an unconfigured 'step')
        """
        try:
            return self.get(attr, default=self._missing)
        except NotConfiguredError as e:
            raise AttributeError(attr) from e

    def __setattr__(self, name, value):
        """
        Attempts to set a named attribute to this `.Configuration` instance.
        Only protected / private style attribute names are accepted, anything
        not starting with an underscore will raise an `AttributeError`.

        :param name: name of the attribute to set
        :param value: value to be associated to *name*
        """
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            raise AttributeError('assignment not supported ({})'.format(name))

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
NotConfigured = NotConfigured()
# NB: NotConfigured._missing refers to the NotConfigured *class* at this point, fix this after the name override
NotConfigured._missing = NotConfigured


_COLLIDING_KEYS = frozenset(dir(Configuration()))


def load(*fps, missing=Missing.silent):
    """
    Read a `.Configuration` instance from file-like objects.

    :param fps: file-like objects (supporting ``.read()``)
    :param missing: policy to be used when a configured key is missing, either
        as a `.Missing` instance or a default value
    :return: a `.Configuration` instance providing values from *fps*
    :rtype: `.Configuration`
    """
    return Configuration(*(yaml.safe_load(fp.read()) for fp in fps), missing=missing)


def loadf(*fnames, default=_NoDefault, missing=Missing.silent):
    """
    Read a `.Configuration` instance from named files.

    :param fnames: name of the files to ``open()``
    :param default: `dict` or `.Configuration` to use when a file does not
        exist (default is to raise a `FileNotFoundError`)
    :param missing: policy to be used when a configured key is missing, either
        as a `.Missing` instance or a default value
    :return: a `.Configuration` instance providing values from *fnames*
    :rtype: `.Configuration`
    """
    def readf(fname):
        if default is _NoDefault or path.exists(fname):
            # (attempt to) open fname if it exists OR if we're expected to raise an error on a missing file
            with open(fname, 'r') as fp:
                # default to empty dict, yaml.safe_load will return None for an empty document
                return yaml.safe_load(fp.read()) or {}
        else:
            return default

    return Configuration(*(readf(path.expanduser(fname)) for fname in fnames), missing=missing)


def loads(*strings, missing=Missing.silent):
    """
    Read a `.Configuration` instance from strings.

    :param strings: configuration contents
    :param missing: policy to be used when a configured key is missing, either
        as a `.Missing` instance or a default value
    :return: a `.Configuration` instance providing values from *strings*
    :rtype: `.Configuration`
    """
    return Configuration(*(yaml.safe_load(string) for string in strings), missing=missing)


def read_xdg_config_dirs(name, extension):
    """
    Read from files found in XDG-specified system-wide configuration paths,
    defaulting to ``/etc/xdg``. Depends on ``XDG_CONFIG_DIRS`` environment
    variable.

    :param name: application or configuration set name
    :param extension: file extension to look for
    :return: a `.Configuration` instance with values read from XDG-specified
        directories
    """
    # find optional value of ${XDG_CONFIG_DIRS}
    config_dirs = environ.get('XDG_CONFIG_DIRS')
    if config_dirs:
        # PATH-like env vars operate in decreasing precedence, reverse this path set to mimic the end result
        config_dirs = reversed(config_dirs.split(path.pathsep))
    else:
        # XDG spec: "If $XDG_CONFIG_DIRS is either not set or empty, a value equal to /etc/xdg should be used."
        config_dirs = ['/etc/xdg']

    # load a file from all config dirs, default to NotConfigured
    fname = '{name}.{extension}'.format(name=name, extension=extension)
    return loadf(*(path.join(config_dir, fname) for config_dir in config_dirs),
                 default=NotConfigured)


def read_xdg_config_home(name, extension):
    """
    Read from file found in XDG-specified configuration home directory,
    expanding to ``${HOME}/.config/name.extension`` by default. Depends on
    ``XDG_CONFIG_HOME`` or ``HOME`` environment variables.

    :param name: application or configuration set name
    :param extension: file extension to look for
    :return: a `.Configuration` instance, possibly `.NotConfigured`
    """
    # find optional value of ${XDG_CONFIG_HOME}
    config_home = environ.get('XDG_CONFIG_HOME')
    if not config_home:
        # XDG spec: "If $XDG_CONFIG_HOME is either not set or empty, a default equal to $HOME/.config should be used."
        # see https://specifications.freedesktop.org/basedir-spec/latest/ar01s03.html
        config_home = path.expanduser('~/.config')

    # expand to full path to configuration file in XDG config path
    return loadf(path.join(config_home, '{name}.{extension}'.format(name=name, extension=extension)),
                 default=NotConfigured)


def read_envvars(name, extension):
    """
    Read environment variables starting with ``NAME_``, where subsequent
    underscores are interpreted as namespaces. Underscores can be retained as
    namespaces by doubling them up, e.g. ``NAME_SPA__CE_KEY`` would be
    accessible in the resulting `.Configuration` as
    ``c.spa_ce.key``, where ``c`` is the `.Configuration` instance.

    .. note::

        Environment variables are always `str`s, this function makes no effort
        to changes this. All values read from command line variables will be
        `str` instances.

    :param name: environment variable prefix to look for (without the ``_``)
    :param extension: *(unused)*
    :return: a `.Configuration` instance, possibly `.NotConfigured`
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
    if not values:
        return NotConfigured

    def dotted(name):
        # replace 'regular' underscores (those between alphanumeric characters) with dots first
        name = re.sub(r'([0-9A-Za-z])_([0-9A-Za-z])', r'\1.\2', name)
        # unescape double underscores back to a single one
        return re.sub(r'__', '_', name)

    return Configuration({dotted(name): value for name, value in values.items()})


def read_envvar_file(name, extension):
    """
    Read values from a file provided as a environment variable
    ``NAME_CONFIG_FILE``.

    :param name: environment variable prefix to look for (without the
        ``_CONFIG_FILE``)
    :param extension: *(unused)*
    :return: a `.Configuration`, possibly `.NotConfigured`
    """
    envvar_file = environ.get('{}_config_file'.format(name).upper())
    if envvar_file:
        # envvar set, load value as file
        return loadf(envvar_file)
    else:
        # envvar not set, return an empty source
        return NotConfigured


def read_envvar_dir(envvar, name, extension):
    """
    Read values from a file located in a directory specified by a particular
    environment file. ``read_envvar_dir('HOME', 'example', 'yaml')`` would
    look for a file at ``/home/user/example.yaml``. When the environment
    variable isn't set or the file does not exist, `NotConfigured` will be
    returned.

    :param envvar: the environment variable to interpret as a directory
    :param name: application or configuration set name
    :param extension: file extension to look for
    :return: a `.Configuration`, possibly `.NotConfigured`
    """
    config_dir = environ.get(envvar)
    if not config_dir:
        return NotConfigured

    # envvar is set, construct full file path, expanding user to allow the envvar containing a value like ~/config
    config_path = path.join(path.expanduser(config_dir), '{name}.{extension}'.format(name=name, extension=extension))
    return loadf(config_path, default=NotConfigured)


class Locality(IntEnum):
    """
    Enumeration of localities defined by confidence, ranging from system-wide
    locations for configurations (e.g. ``/etc/name.yaml``) to environment
    variables.
    """

    system = 0  #: system-wide configuration locations
    user = 1  #: user-local configuration locations
    application = 2  #: application-local configuration locations (dependent on the current working directory)
    environment = 3  #: configuration from environment variables


_LOADERS = {
    Locality.system: (
        # system-wide locations
        read_xdg_config_dirs,
        '/etc/{name}.{extension}',
        '/Library/Preferences/{name}.{extension}',
        partial(read_envvar_dir, 'PROGRAMDATA'),
    ),

    Locality.user: (
        # user-local locations
        read_xdg_config_home,
        '~/Library/Preferences/{name}.{extension}',
        partial(read_envvar_dir, 'APPDATA'),
        partial(read_envvar_dir, 'LOCALAPPDATA'),
        '~/.{name}.{extension}',
    ),

    Locality.application: (
        # application-local locations
        './{name}.{extension}',
    ),

    Locality.environment: (
        # application-specific environment variables
        read_envvar_file,
        read_envvars,
    )
}


def loaders(*specifiers):
    """
    Generates loaders in the specified order.

    Arguments can be `.Locality` instances, producing the loader(s) available
    for that locality, `str` instances (used as file path templates) or
    `callable`s. These can be mixed:

    .. code-block:: python

        # define a load order using predefined user-local locations,
        # an explicit path, a template and a user-defined function
        load_order = loaders(Locality.user,
                             '/etc/defaults/hard-coded.yaml',
                             '/path/to/{name}.{extension}',
                             my_loader)

        # load configuration for name 'my-application' using the load order
        # defined above
        config = load_name('my-application', load_order=load_order)

    :param specifiers:
    :return: a `generator` of configuration loaders in the specified order
    """
    for specifier in specifiers:
        if isinstance(specifier, Locality):
            # localities can carry multiple loaders, flatten this
            yield from _LOADERS[specifier]
        else:
            # something not a locality, pass along verbatim
            yield specifier


DEFAULT_LOAD_ORDER = tuple(loaders(Locality.system,
                                   Locality.user,
                                   Locality.application,
                                   Locality.environment))


def load_name(*names, load_order=DEFAULT_LOAD_ORDER, extension='yaml', missing=Missing.silent):
    """
    Read a `.Configuration` instance by name, trying to read from files in
    increasing significance. The default load order is `.system`, `.user`,
    `.application`, `.environment`.

    Multiple names are combined with multiple loaders using names as the 'inner
    loop / selector', loading ``/etc/name1.yaml`` and ``/etc/name2.yaml``
    before ``./name1.yaml`` and ``./name2.yaml``.

    :param names: application or configuration set names, in increasing
        significance
    :param load_order: ordered list of name templates or `callable`s, in
        increasing order of significance
    :param extension: file extension to be used
    :param missing: policy to be used when a configured key is missing, either
        as a `.Missing` instance or a default value
    :return: a `.Configuration` instances providing values loaded from *names*
        in *load_order* ordering
    """
    def generate_sources():
        # argument order for product matters, for names "foo" and "bar":
        # /etc/foo.yaml before /etc/bar.yaml, but both of them before ~/.foo.yaml and ~/.bar.yaml
        for source, name in product(load_order, names):
            if callable(source):
                yield source(name, extension)
            else:
                # expand user to turn ~/.name.yaml into /home/user/.name.yaml
                candidate = path.expanduser(source.format(name=name, extension=extension))
                yield loadf(candidate, default=NotConfigured)

    return Configuration(*generate_sources(), missing=missing)
