import typing


# expected type for a source of a Configuration object (typically a dict in practise)
ConfigurationSource = typing.MutableMapping[str, typing.Any]


# the key under which the origin of a configured value is tracked, a tuple with strings ('path steps')
Key = typing.Tuple[str, ...]
# an optional origin of a configured value
Origin = typing.Optional[str]
# a collection of origins for configured values, mapping Keys to Origins
KeyOrigins = typing.MutableMapping[Key, Origin]
