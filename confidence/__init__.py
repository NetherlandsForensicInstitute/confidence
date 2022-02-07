import logging

from confidence.exceptions import ConfigurationError, ConfiguredReferenceError, MergeConflictError, NotConfiguredError
from confidence.io import DEFAULT_LOAD_ORDER, dump, dumpf, dumps, load, load_name, loaders, loadf, loads, Locality
from confidence.models import Configuration, Missing, NotConfigured


__all__ = (
    'ConfigurationError', 'ConfiguredReferenceError', 'MergeConflictError', 'NotConfiguredError',
    'DEFAULT_LOAD_ORDER', 'dump', 'dumpf', 'dumps', 'load', 'load_name', 'loaders', 'loadf', 'loads', 'Locality',
    'Configuration', 'Missing', 'NotConfigured',
)


# default confidence' loggers to silence, can be overridden from logging later if needed
logging.getLogger(__name__).addHandler(logging.NullHandler())
