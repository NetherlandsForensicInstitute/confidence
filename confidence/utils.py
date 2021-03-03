from collections.abc import Mapping
from enum import IntEnum
import typing
import warnings

from confidence.exceptions import MergeConflictError


class _Conflict(IntEnum):
    overwrite = 0
    error = 1


def _origin_of(origins: typing.Mapping[str, typing.Optional[str]], path: str) -> typing.Optional[str]:
    if origins:
        for key, origin in reversed(origins.items()):
            if path == key:
                # direct match
                return origin
            if path.startswith(key):
                # TODO: namespace matching for key "test", path "test.key" where "test.key2" is also available,
                #       simple substring match isn't good enough
                return origin

    # nothing pointing to any origin
    return None


def _key_origins(value: typing.Any, origins: typing.Optional[typing.Mapping[typing.Tuple[str, ...], typing.Optional[str]]], path: typing.Tuple[str, ...]) -> typing.Iterator[typing.Tuple[typing.Tuple[str, ...], typing.Optional[str]]]:
    if isinstance(value, Mapping):
        for key, value in value.items():
            yield from _key_origins(value, origins, path + (key,))
    else:
        yield path, _origin_of_path(origins, path)


def _merge(left: typing.MutableMapping[str, typing.Any],
           right: typing.Mapping[str, typing.Any],
           separator: str = '.',
           path: typing.Optional[typing.List[str]] = None,
           conflict: _Conflict = _Conflict.error,
           origins: typing.Mapping[str, typing.Optional[str]] = None) -> typing.Iterator[typing.Tuple[str, typing.Optional[str]]]:
    """
    Merges values in place from *right* into *left*.

    :param left: mapping to merge into
    :param right: mapping to merge from
    :param path: `list` of keys processed before (used for error reporting
        only, should only need to be provided by recursive calls)
    :param conflict: action to be taken on merge conflict, raising an error
        or overwriting an existing value
    :return: *left*, for convenience
    """
    path = path or []
    conflict = _Conflict(conflict)

    for key in right:
        merge_path = path + [key]
        if key in left:
            if isinstance(left[key], Mapping) and isinstance(right[key], Mapping):
                # recurse, merge left and right dict values
                yield from _merge(left[key], right[key],
                                  separator=separator, path=merge_path, conflict=conflict, origins=origins)
            elif left[key] != right[key]:
                if conflict is _Conflict.error:
                    # not both dicts we could merge, but also not the same, this doesn't work
                    conflict_path = separator.join(merge_path)
                    raise MergeConflictError(f'merge conflict at {conflict_path}', key=conflict_path)
                else:
                    # key not yet in left or not considering conflicts, simple addition of right's mapping to left
                    left[key] = right[key]
                    # TODO: document me
                    yield separator.join(merge_path), _origin_of(origins, separator.join(merge_path))
            # else: left[key] is already equal to right[key], no action needed
        else:
            left[key] = right[key]
            # TODO: document me
            yield separator.join(merge_path), _origin_of(origins, separator.join(merge_path))


def _split_keys(mapping: typing.Mapping[str, typing.Any],
                separator: str = '.',
                colliding: typing.Optional[typing.Container] = None) -> typing.Mapping[str, typing.Any]:
    """
    Recursively walks *mapping* to split keys that contain the separator into
    nested mappings.

    .. note::

        Keys not of type `str` are not supported and will raise errors.

    :param mapping: the mapping to process
    :param separator: the character (sequence) to use as the separator between
        keys
    :return: a mapping where keys containing *separator* are split into nested
        mappings
    """
    result: typing.MutableMapping[str, typing.Any] = {}

    for key, value in mapping.items():
        if isinstance(value, Mapping):
            # recursively split key(s) in value
            value = _split_keys(value, separator)

        # reject non-str keys, avoid complicating access patterns
        if not isinstance(key, str):
            raise ValueError(f'non-str type keys ({key}, {key.__class__.__module__}.{key.__class__.__name__}) '
                             'not supported')

        if separator in key:
            # update key to be the first part before the separator
            key, rest = key.split(separator, 1)
            # use rest as the new key of value, recursively split that and update value
            value = _split_keys({rest: value}, separator)

        if colliding and key in colliding:
            # warn about configured keys colliding with Configuration members
            warnings.warn(f'key {key} collides with a named member, use get() method to retrieve the value for {key}',
                          UserWarning)

        # merge the result so far with the (possibly updated / fixed / split) current key and value
        # ignore all of the generated origins, we're only interested in the mere here
        for _ in _merge(result, {key: value}):
            pass

    return result
