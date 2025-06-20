import json
import typing
from dataclasses import dataclass, replace
from os import PathLike
from pathlib import Path

import yaml


@dataclass
class Format(typing.Protocol):
    suffix: str = ''

    def load(self, fp: typing.TextIO) -> typing.Any:
        return self.loads(fp.read())

    def loads(self, string: str) -> typing.Any:
        raise NotImplementedError

    def loadf(self, fpath: typing.Union[str, PathLike], encoding: str = 'utf-8') -> typing.Any:
        with Path(fpath).expanduser().open('rt', encoding=encoding) as fp:
            return self.load(fp)

    def __call__(self, suffix: str) -> 'Format':  # TODO: replace with typing.Self for Python 3.11+
        return replace(self, suffix=suffix)


@dataclass
class _JSONFormat(Format):
    suffix: str = '.json'

    def loads(self, string: str) -> typing.Any:
        return json.loads(string)


@dataclass
class _YAMLFormat(Format):
    suffix: str = '.yaml'

    def loads(self, string: str) -> typing.Any:
        return yaml.safe_load(string)


JSON = _JSONFormat('.json')
YAML = _YAMLFormat('.yaml')


__all__ = (
    'Format',
    'JSON',
    'YAML',
)
