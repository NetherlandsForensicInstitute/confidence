from collections.abc import Mapping
from enum import IntEnum
import warnings

from confidence.exceptions import MergeConflictError


class _Conflict(IntEnum):
    overwrite = 0
    error = 1


def _merge(left, right, path=None, conflict=_Conflict.error):
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
        if key in left:
            if isinstance(left[key], Mapping) and isinstance(right[key], Mapping):
                # recurse, merge left and right dict values, update path for current 'step'
                _merge(left[key], right[key], path + [key], conflict=conflict)
            elif left[key] != right[key]:
                if conflict is _Conflict.error:
                    # not both dicts we could merge, but also not the same, this doesn't work
                    conflict_path = '.'.join(path + [key])
                    raise MergeConflictError('merge conflict at {}'.format(conflict_path), key=conflict_path)
                else:
                    # overwrite left value with right value
                    left[key] = right[key]
            # else: left[key] is already equal to right[key], no action needed
        else:
            # key not yet in left or not considering conflicts, simple addition of right's mapping to left
            left[key] = right[key]

    return left


def _split_keys(mapping, separator='.', colliding=None):
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
    result = {}

    for key, value in mapping.items():
        if isinstance(value, Mapping):
            # recursively split key(s) in value
            value = _split_keys(value, separator)

        # reject non-str keys, avoid complicating access patterns
        if not isinstance(key, str):
            raise ValueError('non-str type keys ({0}, {0.__class__.__module__}.{0.__class__.__name__}) '
                             'not supported'.format(key))

        if separator in key:
            # update key to be the first part before the separator
            key, rest = key.split(separator, 1)
            # use rest as the new key of value, recursively split that and update value
            value = _split_keys({rest: value}, separator)

        if colliding and key in colliding:
            # warn about configured keys colliding with Configuration members
            warnings.warn('key {key} collides with a named member, use get() method to retrieve the '
                          'value for {key}'.format(key=key),
                          UserWarning)

        # merge the result so far with the (possibly updated / fixed / split) current key and value
        _merge(result, {key: value})

    return result
