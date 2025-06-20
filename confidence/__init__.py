import logging

from confidence.exceptions import ConfigurationError, ConfiguredReferenceError, MergeConflictError, NotConfiguredError
from confidence.formats import JSON, YAML, Format
from confidence.io import DEFAULT_LOAD_ORDER, Locality, dump, dumpf, dumps, load, load_name, loaders, loadf, loads
from confidence.models import Configuration, Missing, NotConfigured, merge, unwrap


__all__ = (
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


# default confidence' loggers to silence, can be overridden from logging later if needed
logging.getLogger(__name__).addHandler(logging.NullHandler())
