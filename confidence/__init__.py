import logging
from collections.abc import Sequence

from confidence.exceptions import ConfigurationError, ConfiguredReferenceError, MergeConflictError, NotConfiguredError
from confidence.formats import JSON, YAML, Format, _toml_available
from confidence.io import DEFAULT_LOAD_ORDER, Locality, dump, dumpf, dumps, load, load_name, loaders, loadf, loads
from confidence.models import Configuration, Missing, NotConfigured, merge, unwrap


__all__: Sequence[str] = sorted(
    {
        'Configuration',
        'ConfigurationError',
        'ConfiguredReferenceError',
        'DEFAULT_LOAD_ORDER',
        'Format',
        'JSON',
        'Locality',
        'MergeConflictError',
        'Missing',
        'NotConfigured',
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
        'merge',
        'unwrap',
    }
)


if _toml_available:
    from confidence.formats import TOML

    __all__ = sorted({*__all__, 'TOML'})


# default confidence' loggers to silence, can be overridden from logging later if needed
logging.getLogger(__name__).addHandler(logging.NullHandler())
