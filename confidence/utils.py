import logging
import typing
import warnings
from collections.abc import Mapping
from enum import IntEnum

from confidence.exceptions import MergeConflictError


LOG = logging.getLogger(__name__)


class Conflict(IntEnum):
    OVERWRITE = 0
    ERROR = 1


def merge_into(
    left: typing.MutableMapping[str, typing.Any],
    right: typing.Mapping[str, typing.Any],
    path: list[str] | None = None,
    conflict: Conflict = Conflict.ERROR,
) -> typing.Mapping[str, typing.Any]:
    """
    Merges values in place from *right* into *left*.

    :param left: mapping to merge into
    :param right: mapping to merge from
    :param path: `list` of keys processed before (used for error reporting
        only, should only need to be provided by recursive calls)
    :param conflict: action to be taken on merge conflict, raising an error
        or overwriting an existing value
    :returns: *left*, for convenience
    :raises MergeConflictError: when *left* and *right* both haves values for a
        key that cannot be merged into one
    """
    path = path or []
    conflict = Conflict(conflict)

    for key in right:
        if key in left:
            if isinstance(left[key], Mapping) and isinstance(right[key], Mapping):
                # recurse, merge left and right dict values, update path for current 'step'
                merge_into(left[key], right[key], path + [key], conflict=conflict)
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


def split_keys(
    mapping: typing.Mapping[str, typing.Any],
    colliding: typing.Container | None = None,
) -> typing.Mapping[str, typing.Any]:
    """
    Recursively walks *mapping* to split keys that contain a dot into nested
    mappings.

    .. note::

        Keys not of type `str` are not supported and will raise errors.

    :param mapping: the mapping to process
    :param colliding: a container of keys (names) that should be triggering a
        warning that they collide with other functionality
    :returns: a mapping where keys containing a dot are split into nested
        mappings
    :raises ValueError: when a non-str type key is encountered
    """
    result: typing.MutableMapping[str, typing.Any] = {}

    for key, value in mapping.items():
        if isinstance(value, Mapping):
            # recursively split key(s) in value
            value = split_keys(value)

        # reject non-str keys, avoid complicating access patterns
        if not isinstance(key, str):
            raise ValueError(
                f'non-str type keys ({key}, {key.__class__.__module__}.{key.__class__.__name__}) not supported',
            )

        if '.' in key:
            # update key to be the first part before the dot separator
            key, rest = key.split('.', 1)
            # use rest as the new key of value, recursively split that and update value
            value = split_keys({rest: value})

        if colliding and key in colliding:
            # warn about configured keys colliding with Configuration members
            LOG.warning('key "%s" collides with a named member, use the get() method to retrieve its value', key)

        # merge the result so far with the (possibly updated / fixed / split) current key and value
        merge_into(result, {key: value})

    return result


# retained to compatibility only (warn about the rename, though)
def merge(
    left: typing.MutableMapping[str, typing.Any],
    right: typing.Mapping[str, typing.Any],
    path: list[str] | None = None,
    conflict: Conflict = Conflict.ERROR,
) -> typing.Mapping[str, typing.Any]:
    warnings.warn(
        'confidence.utils.merge has been renamed to confidence.utils.merge_into '
        'and will be removed in a future version',
        DeprecationWarning,
        stacklevel=2,
    )
    return merge_into(left, right, path, conflict)
