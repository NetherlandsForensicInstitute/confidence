import json
import typing
from os import PathLike
from pathlib import Path

import yaml


class Format(typing.Protocol):
    extension: str = ''

    def load(self, fp: typing.TextIO) -> typing.Any:
        return self.loads(fp.read())

    def loads(self, string: str) -> typing.Any:
        raise NotImplementedError

    def loadf(self, fpath: typing.Union[str, PathLike], encoding: str = 'utf-8') -> typing.Any:
        with Path(fpath).expanduser().open('rt', encoding=encoding) as fp:
            return self.load(fp)


class _JSONFormat(Format):
    extension: str = '.json'

    def __init__(self, extension: typing.Optional[str] = '.json'):
        self.extension = extension or ''

    def loads(self, string: str) -> typing.Any:
        return json.loads(string)


class _YAMLFormat(Format):
    extension: str = '.yaml'

    def __init__(self, extension: typing.Optional[str] = '.yaml'):
        self.extension = extension or ''

    def loads(self, string: str) -> typing.Any:
        return yaml.safe_load(string)


JSON = _JSONFormat('.json')
YAML = _YAMLFormat('.yaml')
DEFAULT_FORMAT = YAML
