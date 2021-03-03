import typing


ConfigurationSource = typing.MutableMapping[str, typing.Any]

Key = typing.Tuple[str, ...]
Origin = typing.Optional[str]
KeyOrigins = typing.MutableMapping[Key, Origin]
