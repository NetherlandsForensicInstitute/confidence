from itertools import pairwise


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
