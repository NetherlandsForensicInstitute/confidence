import logging

from confidence.exceptions import ConfigurationError, ConfiguredReferenceError, MergeConflictError, NotConfiguredError
from confidence.io import DEFAULT_LOAD_ORDER, Locality, dump, dumpf, dumps, load, load_name, loaders, loadf, loads
from confidence.models import Configuration, Missing, NotConfigured, merge, unwrap


__all__ = (
    'ConfigurationError',
    'ConfiguredReferenceError',
    'MergeConflictError',
    'NotConfiguredError',
    'DEFAULT_LOAD_ORDER',
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


# default confidence' loggers to silence, can be overridden from logging later if needed
logging.getLogger(__name__).addHandler(logging.NullHandler())
