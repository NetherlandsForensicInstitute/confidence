from functools import partial
import logging
import typing


LOG = logging.getLogger(__name__)


# default key for a mapping with a single key that signals being a secret
DEFAULT_SINGLE_KEY_IDENTIFIER = '$secret'
# default keys within a secret mapping to be passed to a callback
# (this deliberately mimics keyring's get_password function)
DEFAULT_SINGLE_KEY_ARGS = ('service', 'username')


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


def to_secrets(secrets: Secrets | SecretCallback | None) -> Secrets | None:
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
                                  args: typing.Iterable[str]) -> str | None:
    try:
        mapping = value[single_key]
        LOG.debug(f'getting values for ({", ".join(args)}) to use as secret retrieval parameters')
        parameters = tuple(mapping[arg] for arg in args)
        # logging parameters' *values* might still leak things a user would rather not log
        LOG.info(f'passing {len(parameters)} to secret callback {callback}')
        return callback(*parameters)
    except KeyError as e:
        if missing_key := e.args[0] if e.args[0] == single_key else f'{single_key}.{e.args[0]}':
            LOG.warning(f'resolving secret failed, missing key {missing_key}')
        else:
            LOG.warning(f'resolving secret failed')
        # logging out of the way, there's not actually anything we can do to fix the error here
        # if the caller was Configuration.get(), it will handle the KeyError according to it's policies
        raise


class SingleKeyCallback:
    def __init__(self,
                 callback: SecretCallback,
                 single_key: str = DEFAULT_SINGLE_KEY_IDENTIFIER,
                 args: typing.Iterable[str] = DEFAULT_SINGLE_KEY_ARGS):
        # use is_single_key_secret and resolve_n_key_secret_callback to turn the callback we've been handed here into
        # something that will implement the Secrets protocol
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
