import re
from collections.abc import Callable, Iterable, Iterator, Mapping, MutableMapping, Sequence
from enum import Enum
from itertools import chain
from typing import Any

from typing_extensions import Self, sentinel

from confidence.exceptions import ConfigurationError, ConfiguredReferenceError, NotConfiguredError
from confidence.utils import Conflict, merge_into, split_keys


class Missing(Enum):
    SILENT = 'silent'  #: return `NOT_CONFIGURED` for unconfigured keys, avoiding errors
    ERROR = 'error'  #: raise an `AttributeError` for unconfigured keys


# define a sentinel value to indicate there is no default value specified (None would be a valid default value)
# as this is used as an argument default to indicate that an error should be raised when a value is not found, make
# sure that the repr-value of NO_DEFAULT shows up as '(raise)' in documentation
NO_DEFAULT = sentinel('NO_DEFAULT', repr='(raise)')
# retain old name for backwards compatibility
NoDefault = NO_DEFAULT


def unwrap(source: Any) -> Any:
    """
    Recursively walks *source* to turn occurrences of wrapper types into their
    simple counterparts.

    :param source: the object to be unwrapped
    :return: *source*, recursively unwrapped if needed
    """
    while isinstance(source, Configuration):
        # unwrap a Configuration into its source attribute
        source = source._source

    match source:
        case ConfigurationSequence():
            # sequence will resolve references, unwrap values in its source
            return [unwrap(value) for value in source._source]
        case {}:
            # mapping type can no longer be a Configuration, use .items() to unwrap values
            return {key: unwrap(value) for key, value in source.items()}
        case _:
            # nothing needed, use value as-is
            return source


def merge(*sources: Mapping[str, Any], missing: Any = None) -> 'Configuration':
    """
    Merges *sources* into a union, keeping right-side precedence.

    :param sources: source mappings to base the union on, ordered from least to
        most significance
    :param missing: policy for the resulting `Configuration` (defaults to
        `Missing.SILENT`)
    :return: a `Configuration` instance that encompasses all of the keys and
        values in *sources*
    :raises ValueError: when the missing policies of *source* cannot be aligned
    """
    if missing is None:
        # no explicit missing setting, collect settings from arguments, should be either nothing if sources are not
        # Configuration instances, or a single overlapping value, refuse union otherwise
        if len(missing := {source._missing for source in sources if isinstance(source, Configuration)}) > 1:
            raise ValueError(f'no union for incompatible instances: {missing}')
        # use the one remaining missing setting, or default to Missing.SILENT
        missing = missing.pop() if missing else Missing.SILENT

    return Configuration(*sources, missing=missing)


class Configuration(Mapping):
    """
    A collection of configured values, retrievable as either `dict`-like items
    or attributes.
    """

    # match a reference as either ${key.to.be.resolved} or ${callback:arg1:arg2}
    _reference_pattern = re.compile(r'\${(?:(?P<path>[^${}:]+?)|(?P<callback>\w+?):(?P<arguments>[^${}]+?))}')

    def __init__(
        self,
        *sources: Mapping[str, Any],
        missing: Any = Missing.SILENT,
        callbacks: Mapping[str, Callable] | None = None,
    ):
        """
        Create a new `Configuration`, based on one or multiple source mappings.

        :param sources: source mappings to base this `Configuration` on,
            ordered from least to most significant
        :param missing: policy to be used when a configured key is missing,
            either as a `Missing` instance or a default value
        :param callbacks: TODO: document me
        """
        self._missing = missing
        self._callbacks = callbacks or {}
        self._root = self

        if isinstance(self._missing, Missing):
            self._missing = {
                Missing.SILENT: NOT_CONFIGURED,
                Missing.ERROR: NO_DEFAULT,
            }[missing]

        self._source: MutableMapping[str, Any] = {}
        for source in sources:
            if source:
                # merge values from source into self._source, overwriting any corresponding keys
                # unwrap the source to make sure we're dealing with simple types
                merge_into(
                    self._source,
                    split_keys(unwrap(source), colliding=_COLLIDING_KEYS),
                    conflict=Conflict.OVERWRITE,
                )

    def _wrap(self, value: Mapping[str, Any]) -> 'Configuration':
        # create an instance of our current type, copying 'configured' properties / policies
        namespace = type(self)(missing=self._missing)
        namespace._source = value  # type: ignore  # mutability isn't needed after init
        # carry the root object from namespace to namespace, references are always resolved from root
        namespace._root = self._root
        return namespace

    def _resolve(self, value: str) -> Any:
        match = self._reference_pattern.search(value)
        references = set()
        try:
            # keep resolving references until we're at a non-str value or a str-value without references
            while isinstance(value, str) and (match := self._reference_pattern.search(value)):
                match match.groupdict():
                    case {'path': path, 'callback': None}:
                        # avoid resolving references recursively (breaks reference tracking)
                        if path in references:
                            raise ConfiguredReferenceError(f'cannot resolve recursive reference {path}', key=path)

                        resolved = self._root.get(path, default=NO_DEFAULT, resolve_references=False)

                        if match.span(0) != (0, len(value)):
                            # matched a reference inside of another value (template)
                            if isinstance(resolved, Configuration):
                                raise ConfiguredReferenceError(
                                    f'cannot insert namespace at {path} into referring value',
                                    key=path,
                                )

                            # reformat the value with the reference path replaced with the resolved value
                            value = f'{value[: match.start(0)]}{resolved}{value[match.end(0) :]}'
                        else:
                            # value is only a reference, avoid rendering a template (keep referenced value type)
                            value = resolved

                        # track that we've seen path
                        references.add(path)
                    case {'callback': callback, 'arguments': arguments, 'path': None}:
                        if function := self._callbacks.get(callback):
                            # split the arguments by : (allow it to be escaped with a \)
                            arguments = re.split(r'(?<!\\):', arguments)
                            arguments = (argument.replace(r'\:', ':') for argument in arguments)
                            # call the resolved function with the prepped arguments
                            value = function(*arguments)
                        else:
                            raise ConfiguredReferenceError(f'no such callback function: {callback}', key=callback)
                    case _:
                        # TODO: better error / message
                        raise ConfigurationError

            return value
        except NotConfiguredError as e:
            missing_key = match.group('path')  # type: ignore
            raise ConfiguredReferenceError(f'unable to resolve referenced key {missing_key}', key=e.key) from e

    def get(
        self,
        path: str,
        default: Any = None,
        *,
        as_type: Callable | None = None,
        resolve_references: bool = True,
    ) -> Any:
        """
        Gets a value for the specified path.

        :param path: the configuration key to fetch a value for, steps
            separated by a dot (``.``)
        :param default: a value to return if no value is found for the
            supplied path (defaults to ``None``, use ``NO_DEFAULT`` to trigger a
            ``KeyError`` for a non-existing)
        :param as_type: an optional callable to apply to the value found for
            the supplied path (possibly raising exceptions of its own if the
            value can not be coerced to the expected type)
        :param resolve_references: whether to resolve references in values
        :returns: the value associated with the supplied configuration key, if
            available, or a supplied default value if the key was not found
        :raises NotConfiguredError: when no value was found for *path* and
            *default* was ``NO_DEFAULT``
        :raises ConfiguredReferenceError: when a reference could not be resolved
        """
        value = self._source
        steps_taken = []
        try:
            # walk through the values dictionary
            for step in path.split('.'):
                steps_taken.append(step)
                value = value[step]

            if as_type:
                # explicit type conversion requested
                return as_type(value)

            match value:
                case {}:
                    # wrap value in a Configuration
                    return self._wrap(value)
                case [*_]:
                    # wrap value in a sequence that retains Configuration functionality
                    return ConfigurationSequence(value, self._root)
                case str() if resolve_references:
                    # only resolve references in str-type values (the only way they can be expressed)
                    return self._resolve(value)
                case _:
                    # a 'simple' value, nothing to do
                    return value
        except ConfiguredReferenceError:
            # also a KeyError, but this one should bubble to caller
            raise
        except KeyError as e:
            if default is not NO_DEFAULT:
                return default
            else:
                missing_key = '.'.join(steps_taken)
                raise NotConfiguredError(f'no configuration for key {missing_key}', key=missing_key) from e

    def __getattr__(self, attr: str) -> Any:
        """
        Gets a 'single step value', as either a configured value or a
        namespace-like object in the form of a `Configuration` instance. An
        unconfigured value will return `NotConfigured`, a 'silent' sentinel
        value.

        :param attr: the 'step' (key, attribute, …) to take
        :returns: a value, as either an actual value or a `Configuration`
            instance (`NotConfigured` in case of an unconfigured 'step')
        :raises AttributeError: when *attr* is not available and *missing* is
            set to error
        """
        try:
            return self.get(attr, default=self._missing)
        except NotConfiguredError as e:
            raise AttributeError(attr) from e

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Attempts to set a named attribute to this `Configuration` instance.
        Only protected / private style attribute names are accepted, anything
        not starting with an underscore will raise an `AttributeError`.

        :param name: name of the attribute to set
        :param value: value to be associated to *name*
        :raises AttributeError: when attempting to set a non-protected attribute
        """
        if not name.startswith('_'):
            raise AttributeError(f'assignment not supported ({name})')
        else:
            super().__setattr__(name, value)

    def __len__(self) -> int:
        return len(self._source)

    def __getitem__(self, item: str) -> Any:
        # emulate the way dict would handle this: explicitly pass NO_DEFAULT to trigger a KeyError when item is not
        # available
        return self.get(item, default=NO_DEFAULT)

    def __iter__(self) -> Iterator[str]:
        return iter(self._source)

    def __or__(self, other: Mapping[str, Any]) -> 'Configuration':
        match other:
            case {}:
                return merge(self, other)
            case _:
                # operation not supported for these types (let the interpreter handle the reverse or type error)
                return NotImplemented

    def __ror__(self, other: Mapping[str, Any]) -> 'Configuration':
        match other:
            case {}:
                return merge(other, self)
            case _:
                # operation not supported for these types (let the interpreter handle the reverse or type error)
                return NotImplemented

    def __dir__(self) -> Iterable[str]:
        return sorted(set(chain(super().__dir__(), self.keys())))

    def __repr__(self) -> str:
        keys = ', '.join(_repr_value(key) for key in self.keys())
        return f'{self.__class__.__module__}.{self.__class__.__name__}(keys=[{keys}])'

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()

        # NB: both 'magic missing values' are required to be the same specific instances at runtime, encode them as
        #     their corresponding Missing instances for pickling (but leave them as-is otherwise)
        if state['_missing'] is NOT_CONFIGURED:
            state['_missing'] = Missing.SILENT
        elif state['_missing'] is NO_DEFAULT:
            state['_missing'] = Missing.ERROR

        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__ = state

        if isinstance(self._missing, Missing):
            # reverse the Missing encoding done in __getstate__
            self._missing = {Missing.SILENT: NOT_CONFIGURED, Missing.ERROR: NO_DEFAULT}[self._missing]


class _NotConfigured(Configuration):
    _instance: Self | None = None

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self) -> None:
        super().__init__(missing=self)

    def __bool__(self) -> bool:
        return False

    def __str__(self) -> str:
        return '(not configured)'

    def __repr__(self) -> str:
        return '(not configured)'

    def __hash__(self) -> int:
        return hash((self.__class__, None))


# set NOT_CONFIGURED as the singleton instance of _NotConfigured
NOT_CONFIGURED = _NotConfigured()
# retain old name for backwards compatibility
NotConfigured = NOT_CONFIGURED


# collect the names of all defined members of a Configuration instance to be used to warn for configured keys that
# collide with defined members (making them unavailable through attribute access)
_COLLIDING_KEYS = frozenset(dir(Configuration()))


class ConfigurationSequence(Sequence):
    """
    A sequence of configured values, retrievable as if this were a `list`.
    """

    def __init__(self, source: Sequence, root: Configuration):
        """
        Create a new `.ConfigurationSequence`, based on a single source
        sequence, pointing back to 'root' `Configuration` for reference
        handling

        :param source: a `Sequence` to wrap
        :param root: a `.Configuration` that acts as the root for wrapping and
            resolving of references
        """
        self._source = source
        self._root = root

    def __getitem__(self, item: int | slice, *, resolve_references: bool = True) -> Any:
        # NB: item can be a slice, but we'll let _source take care of that
        match value := self._source[item]:
            case {}:
                # let root wrap the value
                return self._root._wrap(value)  # type: ignore
            case [*_]:
                # wrap a sequence value with an 'instance of self'
                return type(self)(value, self._root)
            case str() if resolve_references:
                # let root resolve references in str-type values
                return self._root._resolve(value)
            case _:
                # a 'simple' value, nothing to do
                return value

    def __len__(self) -> int:
        # emulating a simple sequence, delegate length to _source
        return len(self._source)

    def __add__(self, other: Sequence[Any]) -> 'ConfigurationSequence':
        match other:
            case [*_]:
                # left-hand operand is self, expect return value to be the same as left-hand operand
                # create a new sequence with extended source, assuming self's type will retain the 'magic'
                return type(self)(list(self._source) + list(other), root=self._root)
            case _:
                # operation not supported for these types (let the interpreter handle the reverse or type error)
                return NotImplemented

    def __radd__(self, other: Sequence) -> Sequence:
        match other:
            case [*_]:
                # left-hand operand is other, expect return value to be the same as left-hand operand
                # list(self) ensures all mapping type values in self._source are wrapped by factory, retaining the
                # 'magic'
                # NB: assumes other's type will have a single-argument __init__ accepting a list
                return type(other)(list(other) + list(self))  # type: ignore
            case _:
                # operation not supported for these types (let the interpreter handle the reverse or type error)
                return NotImplemented

    def __repr__(self) -> str:
        # use _source to avoid wrapping and resolving values
        values = ', '.join(_repr_value(value) for value in self._source)
        return f'{self.__class__.__module__}.{self.__class__.__name__}([{values}])'


def _repr_value(value: Any) -> str:
    """
    Create a `repr` for value, customizing mapping and sequence types.

    :param value: an object to represent
    :return: a string-representation of *value*
    """
    match value:
        case {}:
            keys = ', '.join(_repr_value(key) for key in value)
            return f'mapping(keys=[{keys}])'
        case [*_]:
            return 'sequence([...])'
        case _:
            # fall back to builtin repr
            return repr(value)


__all__: Sequence[str] = sorted(
    {
        'Configuration',
        'ConfigurationSequence',
        'Missing',
        'NO_DEFAULT',
        'NOT_CONFIGURED',
        'merge',
        'unwrap',
    }
)
