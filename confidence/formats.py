import json
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from os import PathLike
from pathlib import Path

import tomlkit
import yaml

from confidence.models import unwrap


@dataclass(frozen=True)
class Format(ABC):
    """
    Base class for implementing various configuration file formats.

    Configuration I/O will expect methods for reading and writing `TextIO`,
    pathlike values and plain `str`s, the former of these delegating to using
    either `loads` or `dumps` by default. Note that a `Format` data class will
    also contain at least `suffix` and `encoding` attributes used by the same
    I/O mechanisms.
    """

    suffix: str = ''  #: the default file path suffix for a configuration file of this Format
    encoding: str = 'utf-8'  #: the default text encoding for reading from binary I/O

    def load(self, fp: typing.TextIO) -> typing.Any:
        return self.loads(fp.read())

    @abstractmethod
    def loads(self, string: str) -> typing.Any:
        raise NotImplementedError

    def loadf(self, fpath: str | PathLike, encoding: str | None = None) -> typing.Any:
        with Path(fpath).open('rt', encoding=encoding or self.encoding) as fp:
            return self.load(fp)

    def dump(self, value: typing.Any, fp: typing.TextIO) -> None:
        fp.write(self.dumps(value))

    @abstractmethod
    def dumps(self, value: typing.Any) -> str:
        raise NotImplementedError

    def dumpf(self, value: typing.Any, fname: str | PathLike, encoding: str | None = None) -> None:
        with Path(fname).open('wt', encoding=encoding or self.encoding) as fp:
            return self.dump(value, fp)

    def __call__(self, **kwargs: typing.Any) -> 'Format':  # TODO: replace with typing.Self for Python 3.11+
        """
        Create a new `Format` instance similar to this one, with the
        parameters in `kwargs` set to their new values.

        :param kwargs: the parameters to be updated, e.g. `encoding='ascii'`
        :return: an updated `Format`
        """
        # delegate all the heavy lifting to dataclasses.replace()
        return replace(self, **kwargs)


@dataclass(frozen=True)
class _JSONFormat(Format):
    suffix: str = '.json'  #: the default file suffix for the JSON format: .json

    def loads(self, string: str) -> typing.Any:
        return json.loads(string)

    def dumps(self, value: typing.Any) -> str:
        return json.dumps(unwrap(value))


@dataclass(frozen=True)
class _TOMLFormat(Format):
    suffix = '.toml'

    def loads(self, string: str) -> typing.Any:
        try:
            # attempt to load the string as a TOML document
            return tomlkit.loads(string)
        except ValueError:
            # fall back to loading it as a single value
            return tomlkit.value(string)

    def dumps(self, value: typing.Any) -> str:
        try:
            # attempt to dump the value as TOML document
            return tomlkit.dumps(value)
        except TypeError:
            # fall back to stringifying it as a single value / item
            return tomlkit.item(value).as_string()


@dataclass(frozen=True)
class _YAMLFormat(Format):
    suffix: str = '.yaml'  #: the default file suffix for the YAML format: .yaml

    def loads(self, string: str) -> typing.Any:
        return yaml.safe_load(string)

    def dumps(self, value: typing.Any) -> str:
        # use block style output for nested collections (flow style dumps nested dicts inline)
        # omit explicit document end (...) included with simple values
        return yaml.safe_dump(unwrap(value), default_flow_style=False).removesuffix('\n...\n')


# expose *instances* of the formats defined here for users to interact with, editable by calling them (see __call__)
JSON: Format = _JSONFormat(suffix='.json', encoding='utf-8')
TOML: Format = _TOMLFormat(suffix='.toml', encoding='utf-8')
YAML: Format = _YAMLFormat(suffix='.yaml', encoding='utf-8')


__all__ = (
    'Format',
    'JSON',
    'TOML',
    'YAML',
)
