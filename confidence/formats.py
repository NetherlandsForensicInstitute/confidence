import typing
from os import PathLike
from pathlib import Path

import yaml


class Format(typing.Protocol):
    extension: typing.Optional[str] = None

    def load(self, fp: typing.TextIO) -> typing.Any:
        return self.loads(fp.read())

    def loads(self, string: str) -> typing.Any:
        raise NotImplementedError

    def loadf(self, fpath: typing.Union[str, PathLike], encoding: str = 'utf-8') -> typing.Any:
        with Path(fpath).expanduser().open('rt', encoding=encoding) as fp:
            return self.load(fp)


class YAML(Format):
    extension: typing.Optional[str] = '.yaml'

    def __init__(self, extension: str = '.yaml'):
        self.extension = extension

    def loads(self, string: str) -> typing.Any:
        return yaml.safe_load(string)
