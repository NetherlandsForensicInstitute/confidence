from itertools import pairwise
from pathlib import Path
from unittest.mock import call

from confidence import NOT_CONFIGURED, YAML


def equivalent(a, b, *more):
    if more:
        # use pairwise reduction of binary comparisons
        return all(equivalent(left, right) for left, right in pairwise((a, b, *more)))

    match a, b:
        case {}, {}:
            return dict(a.items()) == dict(b.items())
        case [*items_a], [*items_b]:
            return all(equivalent(item_a, item_b) for item_a, item_b in zip(items_a, items_b, strict=True))
        case _:
            return a == b


def assert_loadf_paths(loadf, paths, **repeated):
    def to_path_args(p):
        match p:
            case [*ps]:
                # multiple paths for a single call, Path() 'm all
                return [Path(p) for p in ps]
            case str() | Path():
                # single path for a single call, wrap the single path into a list for use with *args
                return [Path(p)]
            case _:
                raise TypeError

    # use the declared defaults for load_name unless explicitly supplied
    repeated.setdefault('format', YAML)
    repeated.setdefault('default', NOT_CONFIGURED)

    # construct mock call objects as they're expected to be called according to our own args
    calls = [call(*to_path_args(path), **repeated) for path in paths]
    loadf.assert_has_calls(calls, any_order=False)
