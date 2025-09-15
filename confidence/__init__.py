import logging
from collections.abc import Sequence

from confidence.exceptions import ConfigurationError, ConfiguredReferenceError, MergeConflictError, NotConfiguredError
from confidence.formats import JSON, YAML, Format, _toml_available
from confidence.io import DEFAULT_LOAD_ORDER, Locality, dump, dumpf, dumps, load, load_name, loaders, loadf, loads
from confidence.models import Configuration, Missing, NotConfigured, merge, unwrap


__all__: Sequence[str] = (
    'ConfigurationError',
    'ConfiguredReferenceError',
    'DEFAULT_LOAD_ORDER',
    'Format',
    'JSON',
    'MergeConflictError',
    'NotConfiguredError',
    'YAML',
    'dump',
    'dumpf',
    'dumps',
    'load',
    'load_name',
    'loaders',
    'loadf',
    'loads',
    'Locality',
    'Configuration',
    'merge',
    'Missing',
    'NotConfigured',
    'unwrap',
)


if _toml_available:
    from confidence.formats import TOML

    __all__ = (*__all__, 'TOML')


# default confidence' loggers to silence, can be overridden from logging later if needed
logging.getLogger(__name__).addHandler(logging.NullHandler())
