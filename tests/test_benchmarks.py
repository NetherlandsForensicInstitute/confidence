import string
from itertools import pairwise

from confidence import Configuration


def _two_layer_dict(items):
    return {item: {item: 42} for item in items}


def _matrix_dict(items):
    matrix = dict.fromkeys(items, 42)
    for _ in range(len(matrix) - 1):
        matrix = dict.fromkeys(items, matrix)

    return matrix


def test_benchmark_init_no_overlap(benchmark):
    a = _two_layer_dict(string.ascii_lowercase)
    b = _two_layer_dict(string.ascii_uppercase)

    assert benchmark(Configuration, a, b) == a | b


def test_benchmark_init_partial_overlap(benchmark):
    a = _two_layer_dict(string.ascii_letters)
    b = _two_layer_dict(string.ascii_lowercase)

    assert benchmark(Configuration, a, b) == a


def test_benchmark_init_full_overlap(benchmark):
    a = _two_layer_dict(string.ascii_letters)
    b = _two_layer_dict(string.ascii_letters)

    assert benchmark(Configuration, a, b) == a == b


def test_benchmark_get(benchmark):
    def get_diagonals(config, steps):
        a = b = config
        for step in steps:
            a = a.get(step)
        for step in reversed(steps):
            b = b.get(step)

        return a, b

    letters = 'abcdef'
    assert benchmark(get_diagonals, Configuration(_matrix_dict(letters)), letters) == (42, 42)


def test_benchmark_get_dotted(benchmark):
    def get_diagonals(config, steps):
        return config.get('.'.join(steps)), config.get('.'.join(reversed(steps)))

    letters = 'abcdef'
    assert benchmark(get_diagonals, Configuration(_matrix_dict(letters)), letters) == (42, 42)


def test_benchmark_getitem(benchmark):
    def get_diagonals(config, steps):
        a = b = config
        for step in steps:
            a = a[step]
        for step in reversed(steps):
            b = b[step]

        return a, b

    letters = 'abcdef'
    assert benchmark(get_diagonals, Configuration(_matrix_dict(letters)), letters) == (42, 42)


def test_benchmark_getitem_dotted(benchmark):
    def get_diagonals(config, steps):
        return config['.'.join(steps)], config['.'.join(reversed(steps))]

    letters = 'abcdef'
    assert benchmark(get_diagonals, Configuration(_matrix_dict(letters)), letters) == (42, 42)


def test_benchmark_getattr(benchmark):
    def get_diagonals(config):
        return config.a.b.c.d.e.f, config.f.e.d.c.b.a

    letters = 'abcdef'
    assert benchmark(get_diagonals, Configuration(_matrix_dict(letters))) == (42, 42)


def test_benchmark_unpack_kwargs(benchmark):
    def sum_ab(a, b, **_):
        return a + b

    def unpack_kwargs(config):
        return sum_ab(**config)

    assert benchmark(unpack_kwargs, Configuration({'a': 21, 'b': 21, 'c': 21, 'd': 21})) == 42


def test_benchmark_unpack_args(benchmark):
    def sum_ab(a, b, *_):
        return a + b

    def unpack_args(config):
        return sum_ab(*config.sequence)

    assert benchmark(unpack_args, Configuration({'sequence': [21, 21, 21, -21]})) == 42


def test_benchmark_unpack_tuple(benchmark):
    def sum_sequence(config):
        a, b, c, d = config.sequence
        return a + b + c + d

    assert benchmark(sum_sequence, Configuration({'sequence': [21, 21, 21, -21]})) == 42


def test_benchmark_reference_chain(benchmark):
    def resolve_reference(config):
        return config.reference

    # create a reference chain from a → f, add f: 42 at the end
    source = {left: f'${{{right}}}' for left, right in pairwise('abcdef')} | {'f': 42}
    assert benchmark(resolve_reference, Configuration(source, {'reference': '${a}'})) == 42
