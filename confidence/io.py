from enum import IntEnum
from functools import partial
from itertools import product
import logging
from os import environ, path, PathLike
import re
import typing

import yaml

from confidence.models import Configuration, Missing, NoDefault, NotConfigured, unwrap


LOG = logging.getLogger(__name__)


def read_xdg_config_dirs(name: str, extension: str) -> Configuration:
    """
    Read from files found in XDG-specified system-wide configuration paths,
    defaulting to ``/etc/xdg``. Depends on ``XDG_CONFIG_DIRS`` environment
    variable.

    :param name: application or configuration set name
    :param extension: file extension to look for
    :returns: a `Configuration` instance with values read from XDG-specified
        directories
    """
    # XDG spec: "If $XDG_CONFIG_DIRS is either not set or empty, a value equal to /etc/xdg should be used."
    config_dirs = environ.get('XDG_CONFIG_DIRS', '/etc/xdg')
    # PATH-like env vars operate in decreasing precedence, reverse this path set to mimic the end result
    config_dirs = reversed(config_dirs.split(path.pathsep))

    # load a file from all config dirs, default to NotConfigured
    return loadf(*(path.join(config_dir, f'{name}.{extension}') for config_dir in config_dirs),
                 default=NotConfigured)


def read_xdg_config_home(name: str, extension: str) -> Configuration:
    """
    Read from file found in XDG-specified configuration home directory,
    expanding to ``${HOME}/.config/name.extension`` by default. Depends on
    ``XDG_CONFIG_HOME`` or ``HOME`` environment variables.

    :param name: application or configuration set name
    :param extension: file extension to look for
    :returns: a `Configuration` instance, possibly `NotConfigured`
    """
    # find optional value of ${XDG_CONFIG_HOME}
    config_home = environ.get('XDG_CONFIG_HOME')
    if not config_home:
        # XDG spec: "If $XDG_CONFIG_HOME is either not set or empty, a default equal to $HOME/.config should be used."
        # see https://specifications.freedesktop.org/basedir-spec/latest/ar01s03.html
        config_home = path.expanduser('~/.config')

    # expand to full path to configuration file in XDG config path
    return loadf(path.join(config_home, f'{name}.{extension}'), default=NotConfigured)


def read_envvars(name: str, extension: typing.Optional[str] = None) -> Configuration:
    """
    Read environment variables starting with ``NAME_``, where subsequent
    underscores are interpreted as namespaces. Underscores can be retained as
    namespaces by doubling them up, e.g. ``NAME_SPA__CE_KEY`` would be
    accessible in the resulting `Configuration` as
    ``c.spa_ce.key``, where ``c`` is the `Configuration` instance.

    .. note::

        An environment variable matching ``NAME_CONFIG_FILE`` (where the name
        part matches the *name* argument) is explicitly ignored here.
        Environment variables matching this pattern are used with
        `.read_envvar_file`.

    :param name: environment variable prefix to look for (without the ``_``)
    :param extension: *(unused)*
    :returns: a `Configuration` instance, possibly `NotConfigured`
    """
    prefix = f'{name}_'
    prefix_len = len(prefix)
    envvar_file = f'{name}_config_file'
    # create a new mapping from environment values starting with the prefix (but stripped of that prefix)
    values = {var.lower()[prefix_len:]: value
              for var, value in environ.items()
              if var.lower().startswith(prefix) and var.lower() != envvar_file}
    if not values:
        return NotConfigured

    def dotted(name: str) -> str:
        # replace 'regular' underscores (those between alphanumeric characters) with dots first
        name = re.sub(r'([0-9A-Za-z])_([0-9A-Za-z])', r'\1.\2', name)
        # unescape double underscores back to a single one
        return re.sub(r'__', '_', name)

    # include the number of variables matched for debugging purposes
    LOG.info(f'reading configuration from {len(values)} {prefix}* environment variables')

    # pass value to yaml.safe_load to align data type transformation with reading values from files
    return Configuration({dotted(name): yaml.safe_load(value) for name, value in values.items()})


def read_envvar_file(name: str, extension: typing.Optional[str] = None) -> Configuration:
    """
    Read values from a file provided as a environment variable
    ``NAME_CONFIG_FILE``.

    :param name: environment variable prefix to look for (without the
        ``_CONFIG_FILE``)
    :param extension: *(unused)*
    :returns: a `Configuration`, possibly `NotConfigured`
    """
    envvar_file = environ.get(f'{name}_config_file'.upper())
    if envvar_file:
        # envvar set, load value as file
        return loadf(envvar_file)
    else:
        # envvar not set, return an empty source
        return NotConfigured


def read_envvar_dir(envvar: str, name: str, extension: str) -> Configuration:
    """
    Read values from a file located in a directory specified by a particular
    environment file. ``read_envvar_dir('HOME', 'example', 'yaml')`` would
    look for a file at ``/home/user/example.yaml``. When the environment
    variable isn't set or the file does not exist, `NotConfigured` will be
    returned.

    :param envvar: the environment variable to interpret as a directory
    :param name: application or configuration set name
    :param extension: file extension to look for
    :returns: a `Configuration`, possibly `NotConfigured`
    """
    config_dir = environ.get(envvar)
    if not config_dir:
        return NotConfigured

    # envvar is set, construct full file path, expanding user to allow the envvar containing a value like ~/config
    config_path = path.join(path.expanduser(config_dir), f'{name}.{extension}')
    return loadf(config_path, default=NotConfigured)


class Locality(IntEnum):
    """
    Enumeration of localities defined by confidence, ranging from system-wide
    locations for configurations (e.g. ``/etc/name.yaml``) to environment
    variables.
    """

    SYSTEM = 0  #: system-wide configuration locations
    USER = 1  #: user-local configuration locations
    APPLICATION = 2  #: application-local configuration locations (dependent on the current working directory)
    ENVIRONMENT = 3  #: configuration from environment variables


Loadable = typing.Union[str, typing.Callable[[str, str], Configuration]]


_LOADERS: typing.Mapping[Locality, typing.Iterable[Loadable]] = {
    Locality.SYSTEM: (
        # system-wide locations
        read_xdg_config_dirs,
        '/etc/{name}/{name}.{extension}',
        '/etc/{name}.{extension}',
        '/Library/Preferences/{name}/{name}.{extension}',
        '/Library/Preferences/{name}.{extension}',
        partial(read_envvar_dir, 'PROGRAMDATA'),
    ),

    Locality.USER: (
        # user-local locations
        read_xdg_config_home,
        '~/Library/Preferences/{name}.{extension}',
        partial(read_envvar_dir, 'APPDATA'),
        partial(read_envvar_dir, 'LOCALAPPDATA'),
        '~/.{name}.{extension}',
    ),

    Locality.APPLICATION: (
        # application-local locations
        './{name}.{extension}',
    ),

    Locality.ENVIRONMENT: (
        # application-specific environment variables
        read_envvar_file,
        read_envvars,
    ),
}


def loaders(*specifiers: typing.Union[Locality, Loadable]) -> typing.Iterable[Loadable]:
    """
    Generates loaders in the specified order.

    Arguments can be `Locality` instances, producing the loader(s) available
    for that locality, `str` instances (used as file path templates) or
    `callable` s. These can be mixed:

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

    :param specifiers: loader specifiers, see description
    :yields: configuration loaders in the specified order
    """
    for specifier in specifiers:
        if isinstance(specifier, Locality):
            # localities can carry multiple loaders, flatten this
            yield from _LOADERS[specifier]
        else:
            # something not a locality, pass along verbatim
            yield specifier


DEFAULT_LOAD_ORDER = tuple(loaders(Locality.SYSTEM,
                                   Locality.USER,
                                   Locality.APPLICATION,
                                   Locality.ENVIRONMENT))


def load(*fps: typing.IO, missing: typing.Any = Missing.SILENT) -> Configuration:
    """
    Read a `Configuration` instance from file-like objects.

    :param fps: file-like objects (supporting ``.read()``)
    :param missing: policy to be used when a configured key is missing, either
        as a `Missing` instance or a default value
    :returns: a `Configuration` instance providing values from *fps*
    """
    return Configuration(*(yaml.safe_load(fp.read()) for fp in fps), missing=missing)


def loadf(*fnames: typing.Union[str, PathLike],
          default: typing.Any = NoDefault,
          missing: typing.Any = Missing.SILENT) -> Configuration:
    """
    Read a `Configuration` instance from named files.

    :param fnames: name of the files to ``open()``
    :param default: `dict` or `Configuration` to use when a file does not
        exist (default is to raise a `FileNotFoundError`)
    :param missing: policy to be used when a configured key is missing, either
        as a `Missing` instance or a default value
    :returns: a `Configuration` instance providing values from *fnames*
    """
    def readf(fname: str) -> typing.Mapping[str, typing.Any]:
        try:
            with open(fname, 'r') as fp:
                LOG.info(f'reading configuration from file {fname}')
                # default to empty dict, yaml.safe_load will return None for an empty document
                return yaml.safe_load(fp.read()) or {}
        except IOError:
            # file does not exist or inaccessible
            if default is NoDefault:
                # no explicit default provided, continue original error
                raise
            else:
                LOG.debug(f'unable to read configuration from file {fname}')
                return default

    return Configuration(*(readf(path.expanduser(fname)) for fname in fnames), missing=missing)


def loads(*strings: str, missing: typing.Any = Missing.SILENT) -> Configuration:
    """
    Read a `Configuration` instance from strings.

    :param strings: configuration contents
    :param missing: policy to be used when a configured key is missing, either
        as a `Missing` instance or a default value
    :returns: a `Configuration` instance providing values from *strings*
    """
    return Configuration(*(yaml.safe_load(string) for string in strings), missing=missing)


def load_name(*names: str,
              load_order: typing.Iterable[Loadable] = DEFAULT_LOAD_ORDER,
              extension: str = 'yaml',
              missing: typing.Any = Missing.SILENT) -> Configuration:
    """
    Read a `Configuration` instance by name, trying to read from files in
    increasing significance. The default load order is `.system`, `.user`,
    `.application`, `.environment`.

    Multiple names are combined with multiple loaders using names as the 'inner
    loop / selector', loading ``/etc/name1.yaml`` and ``/etc/name2.yaml``
    before ``./name1.yaml`` and ``./name2.yaml``.

    :param names: application or configuration set names, in increasing
        significance
    :param load_order: ordered list of name templates or `callable` s, in
        increasing order of significance
    :param extension: file extension to be used
    :param missing: policy to be used when a configured key is missing, either
        as a `Missing` instance or a default value
    :returns: a `Configuration` instances providing values loaded from *names*
        in *load_order* ordering
    """
    def generate_sources() -> typing.Iterable[typing.Mapping[str, typing.Any]]:
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


def dump(value: typing.Any, fp: typing.IO, encoding: str = 'utf-8') -> None:
    """
    Serialize the configuration in *value* to YAML format, writing it to *fp*.

    :param value: the value (like a `Configuration` object) to dump
    :param fp: a file-like object to write to
    :param encoding: encoding to use
    """
    # recursively unwrap the value to help yaml understand what we're trying to dump
    # use block style output for nested collections (flow style dumps nested dicts inline)
    yaml.safe_dump(unwrap(value), stream=fp, encoding=encoding, default_flow_style=False)


def dumpf(value: typing.Any, fname: typing.Union[str, PathLike], encoding: str = 'utf-8') -> None:
    """
    Serialize the configuration in *value* to a YAML-formatted file.

    :param value: the value (like a `Configuration` object) to dump
    :param fname: name or path of the file to write to
    :param encoding: encoding to use
    """
    with open(fname, 'wb') as out_file:
        dump(value, out_file, encoding=encoding)


def dumps(value: typing.Any) -> str:
    """
    Serialize the configuration in *value* as a YAML-formatted string.

    :param value: the value (like a `Configuration` object) to dump
    :returns: *configuration*, serialized as a `str` in YAML format
    """
    # recursively unwrap the value to help yaml understand what we're trying to dump
    # use block style output for nested collections (flow style dumps nested dicts inline)
    encoded = yaml.safe_dump(unwrap(value), default_flow_style=False)
    # omit explicit document end (...) included with simple values
    # (to be replaced with encoded.removesuffix('\n...\n') when python requirement hits 3.9+)
    return encoded[:-4] if encoded.endswith('...\n') else encoded
