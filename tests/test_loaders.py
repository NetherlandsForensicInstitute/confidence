from itertools import chain, groupby

from confidence import DEFAULT_LOAD_ORDER, loaders, Locality
from confidence.io import _LOADERS


def test_default_load_order_all_loaders():
    all_loaders = set(chain.from_iterable(_LOADERS.values()))
    assert len(all_loaders) == len(DEFAULT_LOAD_ORDER)
    assert all(loader in DEFAULT_LOAD_ORDER for loader in all_loaders)


def test_default_load_order_locality():
    localities = {loader: locality for locality, local_loaders in _LOADERS.items() for loader in local_loaders}
    localities = map(localities.get, DEFAULT_LOAD_ORDER)

    assert tuple(key for key, _ in groupby(localities)) == tuple(sorted(Locality))


def test_no_loaders():
    assert tuple(*loaders()) == ()


def test_locality_loaders():
    assert tuple(loaders(Locality.USER)) == _LOADERS[Locality.USER]
    assert tuple(loaders(Locality.SYSTEM, Locality.APPLICATION)) == tuple(chain(_LOADERS[Locality.SYSTEM], _LOADERS[Locality.APPLICATION]))
    assert tuple(loaders(Locality.ENVIRONMENT, Locality.ENVIRONMENT)) == tuple(chain(_LOADERS[Locality.ENVIRONMENT], _LOADERS[Locality.ENVIRONMENT]))


def test_loaders_mixed():
    def function():
        pass

    assert tuple(loaders('just a string')) == ('just a string',)
    assert tuple(loaders('just a string', function)) == ('just a string', function)
    assert tuple(loaders(function, Locality.ENVIRONMENT, '{name}.{extension}')) == tuple(chain([function], _LOADERS[Locality.ENVIRONMENT], ['{name}.{extension}']))
