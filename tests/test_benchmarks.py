import string

from confidence import Configuration


def _items_dict(items):
    return {item: {item: 42} for item in items}


def _matrix_dict(items):
    matrix = dict.fromkeys(items, 42)
    for _ in range(len(matrix) - 1):
        matrix = dict.fromkeys(items, matrix)

    return matrix


def test_benchmark_init_no_overlap(benchmark):
    a = _items_dict(string.ascii_lowercase)
    b = _items_dict(string.ascii_uppercase)

    assert benchmark(Configuration, a, b) == a | b


def test_benchmark_init_partial_overlap(benchmark):
    a = _items_dict(string.ascii_letters)
    b = _items_dict(string.ascii_lowercase)

    assert benchmark(Configuration, a, b) == a


def test_benchmark_init_full_overlap(benchmark):
    a = _items_dict(string.ascii_letters)
    b = _items_dict(string.ascii_letters)

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
