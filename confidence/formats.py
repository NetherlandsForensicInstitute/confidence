import json
import typing
from os import PathLike
from pathlib import Path

import yaml


class Format(typing.Protocol):
    suffix: str = ''

    def load(self, fp: typing.TextIO) -> typing.Any:
        return self.loads(fp.read())

    def loads(self, string: str) -> typing.Any:
        raise NotImplementedError

    def loadf(self, fpath: typing.Union[str, PathLike], encoding: str = 'utf-8') -> typing.Any:
        with Path(fpath).expanduser().open('rt', encoding=encoding) as fp:
            return self.load(fp)


class _JSONFormat(Format):
    suffix: str = '.json'

    def __init__(self, suffix: typing.Optional[str] = '.json'):
        self.suffix = suffix or ''

    def __call__(self, suffix: str) -> Format:
        return type(self)(suffix)

    def loads(self, string: str) -> typing.Any:
        return json.loads(string)


class _YAMLFormat(Format):
    suffix: str = '.yaml'

    def __init__(self, suffix: typing.Optional[str] = '.yaml'):
        self.suffix = suffix or ''

    def __call__(self, suffix: str) -> Format:
        return type(self)(suffix)

    def loads(self, string: str) -> typing.Any:
        return yaml.safe_load(string)


JSON = _JSONFormat('.json')
YAML = _YAMLFormat('.yaml')


__all__ = (
    'Format',
    'JSON',
    'YAML',
)
