from functools import partial
import logging
import typing


LOG = logging.getLogger(__name__)


DEFAULT_SINGLE_KEY_IDENTIFIER = '$secret'
DEFAULT_SINGLE_KEY_ARGS = ('service', 'username')


@typing.runtime_checkable
class Secrets(typing.Protocol):
    def matches(self, value: typing.Mapping[str, typing.Any]) -> bool:
        ...

    def resolve(self, value: typing.Mapping[str, typing.Any]) -> typing.Any:
        ...


@typing.runtime_checkable
class SecretCallback(typing.Protocol):
    def __call__(self, *args: str) -> typing.Optional[str]:
        ...


def to_secrets(secrets: typing.Optional[Secrets | SecretCallback]) -> typing.Optional[Secrets]:
    if not secrets:
        return None
    elif isinstance(secrets, SecretCallback):
        return SingleKeyCallback(secrets)
    else:
        return secrets


def is_single_key_secret(value: typing.Mapping[str, typing.Any],
                         *,
                         key: str) -> bool:
    return len(value) == 1 and key in value


def resolve_n_key_secret_callback(value: typing.Mapping[str, typing.Any],
                                  *,
                                  callback: SecretCallback,
                                  single_key: str,
                                  args: typing.Iterable[str]) -> typing.Optional[str]:
    try:
        secret = value[single_key]
        return callback(*(secret[arg] for arg in args))
    except KeyError as e:
        missing_key = e.args[0] if e.args[0] == single_key else f'{single_key}.{e.args[0]}'
        LOG.warning(f'resolving secret failed, missing key {missing_key}')
        raise


class SingleKeyCallback:
    def __init__(self,
                 callback: SecretCallback,
                 single_key: str = DEFAULT_SINGLE_KEY_IDENTIFIER,
                 args: typing.Iterable[str] = DEFAULT_SINGLE_KEY_ARGS):
        self.matches = partial(
            is_single_key_secret,
            key=single_key,
        )
        self.resolve = partial(
            resolve_n_key_secret_callback,
            callback=callback,
            single_key=single_key,
            args=args,
        )
