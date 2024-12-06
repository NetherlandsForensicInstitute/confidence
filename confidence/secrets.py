import typing


@typing.runtime_checkable
class Secrets(typing.Protocol):
    def matches(self, value: typing.Mapping[str, typing.Any]) -> bool:
        ...

    def resolve(self, value: typing.Mapping[str, typing.Any]) -> typing.Any:
        ...


@typing.runtime_checkable
class SecretCallback(typing.Protocol):
    def __call__(self, *args: str) -> str | None:
        ...
