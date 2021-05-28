from collections.abc import Mapping, Sequence
from enum import Enum
from itertools import chain
import re
import typing

from confidence.exceptions import ConfiguredReferenceError, NotConfiguredError
from confidence.utils import Conflict, merge, split_keys


class Missing(Enum):
    SILENT = 'silent'  #: return `.NotConfigured` for unconfigured keys, avoiding errors
    ERROR = 'error'  #: raise an `AttributeError` for unconfigured keys


# define a sentinel value to indicate there is no default value specified (None would be a valid default value)
# as this is used as an argument default to indicate that an error should be raised when a value is not found, make
# sure that the repr-value of NoDefault shows up as '(raise)' in documentation
NoDefault = type('NoDefault', (object,), {
    '__repr__': lambda self: '(raise)',
    '__str__': lambda self: '(raise)'
})()  # create instance of that new type to assign to NoDefault


class Configuration(Mapping):
    """
    A collection of configured values, retrievable as either `dict`-like items
    or attributes.
    """

    # match a reference as ${key.to.be.resolved}
    _reference_pattern = re.compile(r'\${(?P<path>[^${}]+?)}')

    def __init__(self,
                 *sources: typing.Mapping[str, typing.Any],
                 missing: typing.Any = Missing.SILENT):
        """
        Create a new `.Configuration`, based on one or multiple source mappings.

        :param sources: source mappings to base this `.Configuration` on,
            ordered from least to most significant
        :param missing: policy to be used when a configured key is missing,
            either as a `.Missing` instance or a default value
        """
        self._missing = missing
        self._root = self

        if isinstance(self._missing, Missing):
            self._missing = {Missing.SILENT: NotConfigured,
                             Missing.ERROR: NoDefault}[missing]

        self._source: typing.MutableMapping[str, typing.Any] = {}
        for source in sources:
            if source:
                while isinstance(source, Configuration):
                    # _merge will walk source.items(), using source.get(), avoid resolving references now
                    source = source._source

                # merge values from source into self._source, overwriting any corresponding keys
                merge(self._source, split_keys(source, colliding=_COLLIDING_KEYS), conflict=Conflict.OVERWRITE)

    def _wrap(self, value: typing.MutableMapping[str, typing.Any]) -> 'Configuration':
        # create an instance of our current type, copying 'configured' properties / policies
        namespace = type(self)(missing=self._missing)
        namespace._source = value
        # carry the root object from namespace to namespace, references are always resolved from root
        namespace._root = self._root
        return namespace

    def _resolve(self, value: str) -> typing.Any:
        match = self._reference_pattern.search(value)
        references = set()
        try:
            while match:
                path = match.group('path')
                if path in references:
                    raise ConfiguredReferenceError(f'cannot resolve recursive reference {path}', key=path)

                # avoid resolving references recursively (breaks reference tracking)
                reference = self._root.get(path, resolve_references=False)

                if match.span(0) != (0, len(value)):
                    # matched a reference inside of another value (template)
                    if isinstance(reference, Configuration):
                        raise ConfiguredReferenceError(f'cannot insert namespace at {path} into referring value',
                                                       key=path)

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
            missing_key = match.group('path')  # type: ignore
            raise ConfiguredReferenceError(f'unable to resolve referenced key {missing_key}', key=e.key) from e

    def get(self,
            path: str,
            default: typing.Any = NoDefault,
            as_type: typing.Optional[typing.Callable] = None,
            resolve_references: bool = True) -> typing.Any:
        """
        Gets a value for the specified path.

        :param path: the configuration key to fetch a value for, steps
            separated by a dot (``.``)
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
            for step in path.split('.'):
                steps_taken.append(step)
                value = value[step]

            if as_type:
                # explicit type conversion requested
                return as_type(value)
            elif isinstance(value, Mapping):
                # wrap value in a Configuration
                return self._wrap(value)
            elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                # wrap value in a sequence that retains Configuration functionality
                return ConfigurationSequence(value, self._wrap)
            elif resolve_references and isinstance(value, str):
                # only resolve references in str-type values (the only way they can be expressed)
                return self._resolve(value)
            else:
                # a 'simple' value, nothing to do
                return value
        except ConfiguredReferenceError:
            # also a KeyError, but this one should bubble to caller
            raise
        except KeyError as e:
            if default is not NoDefault:
                return default
            else:
                missing_key = '.'.join(steps_taken)
                raise NotConfiguredError(f'no configuration for key {missing_key}', key=missing_key) from e

    def __getattr__(self, attr: str) -> typing.Any:
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

    def __setattr__(self, name: str, value: typing.Any) -> None:
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
            raise AttributeError(f'assignment not supported ({name})')

    def __len__(self) -> int:
        return len(self._source)

    def __getitem__(self, item: str) -> typing.Any:
        return self.get(item)

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self._source)

    def __dir__(self) -> typing.Iterable[str]:
        return sorted(set(chain(super().__dir__(), self.keys())))

    def __repr__(self) -> str:
        # even though keys should always be str, no need to crash on repr() in edge cases
        keys = ', '.join(str(key) for key in self.keys())
        return f'<{self.__class__.__module__}.{self.__class__.__name__} keys={{{keys}}}>'

    def __getstate__(self) -> typing.Dict[str, typing.Any]:
        state = self.__dict__.copy()

        # NB: both 'magic missing values' are required to be the same specific instances at runtime, encode them as
        #     their corresponding Missing instances for pickling (but leave them as-is otherwise)
        if state['_missing'] is NotConfigured:
            state['_missing'] = Missing.SILENT
        elif state['_missing'] is NoDefault:
            state['_missing'] = Missing.ERROR

        return state

    def __setstate__(self, state: typing.Dict[str, typing.Any]) -> None:
        self.__dict__ = state

        if isinstance(self._missing, Missing):
            # reverse the Missing encoding done in __getstate__
            self._missing = {Missing.SILENT: NotConfigured,
                             Missing.ERROR: NoDefault}[self._missing]


# define NotConfigured as a class first (using type() to keep the type checker happy)
NotConfigured = type('NotConfigured', (Configuration,), {
    '__bool__': lambda self: False,
    '__repr__': lambda self: '(not configured)',
    '__str__': lambda self: '(not configured)',
    '__doc__': 'Sentinel value to signal there is no value for a requested key.'
})
# overwrite the NotConfigured type as an instance of itself, serving as a sentinel value that some requested key was
# not configured, while still acting like a Configuration object
NotConfigured = NotConfigured()
# NotConfigured._missing refers to the NotConfigured *type* at this point, overwrite it with the sentinel value
NotConfigured._missing = NotConfigured  # type: ignore


# collect the names of all defined members of a Configuration instance to be used to warn for configured keys that
# collide with defined members (making them unavailable through attribute access)
_COLLIDING_KEYS = frozenset(dir(Configuration()))


class ConfigurationSequence(Sequence):
    """
    A sequence of configured values, retrievable as if this were a `list`.
    """

    def __init__(self,
                 source: typing.Sequence,
                 factory: typing.Callable):
        """
        Create a new `._ConfigurationSequence`, based on a single source
        sequence, pointing back to 'root' `Configuration` through *factory*.

        :param source: a `Sequence` to wrap
        :param factory: a `callable` to wrap `Mapping` values with
        """
        self._source = source
        self._factory = factory

    def __getitem__(self, item: typing.Union[int, slice]) -> typing.Any:
        # retrieve value of interest (NB: item can be a slice, but we'll let _source take care of that)
        value = self._source[item]
        if isinstance(value, Mapping):
            # invoke the factory function (provided by Configuration) for a Mapping value
            return self._factory(value)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            # wrap a sequence value with an 'instance of self'
            return type(self)(value, self._factory)
        else:
            # a 'simple' value, nothing to do
            return value

    def __len__(self) -> int:
        # emulating a simple sequence, delegate length to _source
        return len(self._source)

    def __add__(self, other: typing.Sequence[typing.Any]) -> 'ConfigurationSequence':
        if not isinstance(other, Sequence) or isinstance(other, (str, bytes)):
            # incompatible types, let Python resolve an action for this, like calling other.__radd__ or raising a
            # TypeError
            return NotImplemented

        # left-hand operand is self, expect return value to be the same as left-hand operand
        # create a new sequence with extended source, assuming self's type will retain the 'magic'
        return type(self)(list(self._source) + list(other), factory=self._factory)

    def __radd__(self, other: typing.Sequence) -> typing.Sequence:
        if not isinstance(other, Sequence) or isinstance(other, (str, bytes)):
            # incompatible types, let Python resolve an action for this
            return NotImplemented

        # left-hand operand is other, expect return value to be the same as left-hand operand
        # list(self) ensures all mapping type values in self._source are wrapped by factory, retaining the 'magic'
        # NB: assumes other's type will have a single-argument __init__ accepting a list
        return type(other)(list(other) + list(self))  # type: ignore

    def __repr__(self) -> str:
        values = ', '.join(repr(value) for value in self)
        return f'<{self.__class__.__module__}.{self.__class__.__name__} [{values}]>'
