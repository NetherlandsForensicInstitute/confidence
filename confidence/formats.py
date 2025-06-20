import json
import typing
from dataclasses import dataclass, replace
from os import PathLike
from pathlib import Path

import yaml

from confidence.models import unwrap


@dataclass(frozen=True)
class Format(typing.Protocol):
    suffix: str = ''
    encoding: str = 'utf-8'

    def load(self, fp: typing.TextIO) -> typing.Any:
        return self.loads(fp.read())

    def loads(self, string: str) -> typing.Any:
        raise NotImplementedError

    def loadf(self, fpath: typing.Union[str, PathLike], encoding: typing.Optional[str] = None) -> typing.Any:
        with Path(fpath).expanduser().open('rt', encoding=encoding or self.encoding) as fp:
            return self.load(fp)

    def dump(self, value: typing.Any, fp: typing.TextIO) -> None:
        fp.write(self.dumps(value))

    def dumps(self, value: typing.Any) -> str:
        raise NotImplementedError

    def dumpf(
        self, value: typing.Any, fname: typing.Union[str, PathLike], encoding: typing.Optional[str] = None
    ) -> None:
        with Path(fname).open('wt', encoding=encoding or self.encoding) as fp:
            return self.dump(value, fp)

    def __call__(self, **kwargs: typing.Any) -> 'Format':  # TODO: replace with typing.Self for Python 3.11+
        return replace(self, **kwargs)


@dataclass(frozen=True)
class _JSONFormat(Format):
    suffix: str = '.json'

    def loads(self, string: str) -> typing.Any:
        return json.loads(string)

    def dumps(self, value: typing.Any) -> str:
        return json.dumps(unwrap(value))


@dataclass(frozen=True)
class _YAMLFormat(Format):
    suffix: str = '.yaml'

    def loads(self, string: str) -> typing.Any:
        return yaml.safe_load(string)

    def dumps(self, value: typing.Any) -> str:
        # use block style output for nested collections (flow style dumps nested dicts inline)
        # omit explicit document end (...) included with simple values
        return yaml.safe_dump(unwrap(value), default_flow_style=False).removesuffix('\n...\n')


JSON: Format = _JSONFormat(suffix='.json', encoding='utf-8')
YAML: Format = _YAMLFormat(suffix='.yaml', encoding='utf-8')


__all__ = (
    'Format',
    'JSON',
    'YAML',
)
