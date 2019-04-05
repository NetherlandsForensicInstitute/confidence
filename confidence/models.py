from collections.abc import Mapping
from enum import Enum
from itertools import chain
import re

from confidence.exceptions import ConfiguredReferenceError, NotConfiguredError
from confidence.utils import _Conflict, _merge, _split_keys


class Missing(Enum):
    silent = 'silent'  #: return `.NotConfigured` for unconfigured keys, avoiding errors
    error = 'error'  #: raise an `AttributeError` for unconfigured keys


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
                _merge(self._source,
                       _split_keys(source, separator=self._separator, colliding=_COLLIDING_KEYS),
                       conflict=_Conflict.overwrite)

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
