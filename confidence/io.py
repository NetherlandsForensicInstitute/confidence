from enum import IntEnum
from functools import partial
from itertools import product
from os import environ, path
import re

import yaml

from confidence.models import _NoDefault, Configuration, Missing, NotConfigured


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
