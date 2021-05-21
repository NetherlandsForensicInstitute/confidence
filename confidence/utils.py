from collections.abc import Mapping
from enum import IntEnum
import typing
import warnings

from confidence.exceptions import MergeConflictError


class Conflict(IntEnum):
    OVERWRITE = 0
    ERROR = 1


def merge(left: typing.MutableMapping[str, typing.Any],
          right: typing.Mapping[str, typing.Any],
          path: typing.Optional[typing.List[str]] = None,
          conflict: Conflict = Conflict.ERROR) -> typing.Mapping[str, typing.Any]:
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
    conflict = Conflict(conflict)

    for key in right:
        if key in left:
            if isinstance(left[key], Mapping) and isinstance(right[key], Mapping):
                # recurse, merge left and right dict values, update path for current 'step'
                merge(left[key], right[key], path + [key], conflict=conflict)
            elif left[key] != right[key]:
                if conflict is Conflict.ERROR:
                    # not both dicts we could merge, but also not the same, this doesn't work
                    conflict_path = '.'.join(path + [key])
                    raise MergeConflictError(f'merge conflict at {conflict_path}', key=conflict_path)
                else:
                    # overwrite left value with right value
                    left[key] = right[key]
            # else: left[key] is already equal to right[key], no action needed
        else:
            # key not yet in left or not considering conflicts, simple addition of right's mapping to left
            left[key] = right[key]

    return left


def split_keys(mapping: typing.Mapping[str, typing.Any],
               colliding: typing.Optional[typing.Container] = None) -> typing.Mapping[str, typing.Any]:
    """
    Recursively walks *mapping* to split keys that contain a dot into nested
    mappings.

    .. note::

        Keys not of type `str` are not supported and will raise errors.

    :param mapping: the mapping to process
    :param colliding: a container of keys (names) that should be triggering a
        warning that they collide with other functionality
    :return: a mapping where keys containing a dot are split into nested
        mappings
    """
    result: typing.MutableMapping[str, typing.Any] = {}

    for key, value in mapping.items():
        if isinstance(value, Mapping):
            # recursively split key(s) in value
            value = split_keys(value)

        # reject non-str keys, avoid complicating access patterns
        if not isinstance(key, str):
            raise ValueError(f'non-str type keys ({key}, {key.__class__.__module__}.{key.__class__.__name__}) '
                             'not supported')

        if '.' in key:
            # update key to be the first part before the dot separator
            key, rest = key.split('.', 1)
            # use rest as the new key of value, recursively split that and update value
            value = split_keys({rest: value})

        if colliding and key in colliding:
            # warn about configured keys colliding with Configuration members
            warnings.warn(f'key {key} collides with a named member, use get() method to retrieve the value for {key}',
                          UserWarning)

        # merge the result so far with the (possibly updated / fixed / split) current key and value
        merge(result, {key: value})

    return result
