class ConfigurationError(KeyError):
    """
    TODO: Document me.
    """
    pass


def _merge(left, right, _path=None):
    """
    TODO: Document me.
    """
    _path = _path or []

    for key in right:
        if key in left:
            if isinstance(left[key], dict) and isinstance(right[key], dict):
                # recurs, merge left and right dict values, update _path for current 'step'
                _merge(left[key], right[key], _path + [key])
            elif left[key] != right[key]:
                # not both dicts we could merge, but also not the same, this doesn't work
                raise ConfigurationError('merge conflict at {}'.format('.'.join(_path + [key])))
            # else: left[key] is already equal to right[key], no action needed
        else:
            # key not yet in left, simple addition of right's mapping to left
            left[key] = right[key]

    return left


def _split_keys(values, separator='.'):
    """
    TODO: Document me.
    """
    result = {}

    for key, value in values.items():
        if isinstance(value, dict):
            # recursively split key(s) in value
            value = _split_keys(value, separator)

        if separator in key:
            # update key to be the first part before the separator
            key, rest = key.split(separator, 1)
            # use rest as the new key of value, recursively split that and update value
            value = _split_keys({rest: value}, separator)

        # merge the result so far with the (possibly updated / fixed / split) current key and value
        _merge(result, {key: value})

    return result


# sentinel value to indicate no default is specified, allowing a default of
# None for Configuration.get()
_NoDefault = object()


class Configuration:
    """
    TODO: Document me.
    """

    def __init__(self, values=None, separator='.'):
        """
        TODO: Document me.
        """
        self.values = _split_keys(values or {})
        self.separator = separator

    def get(self, path, default=_NoDefault, as_type=None):
        """
        Gets a value for the specified path.

        Args:
            path: The configuration key to fetch a value for, steps separated
                by the separator supplied to the constructor (default ".").
            default: The value to return if no value is found for the supplied
                path (None is allowed).
            as_type: An optional callable to apply to the value found for the
                supplied path (possibly raising exceptions of its own if the
                value can not be coerced to the expected type).

        Returns:
            The value associated with the supplied configuration key, if
            available or a supplied default value if the key was not found.

        Raises:
            ConfigurationError: When no default was provided and no value was
            found on the supplied path.
        """
        value = self.values
        steps_taken = []
        try:
            # walk through the values dictionary
            for step in path.split(self.separator):
                steps_taken.append(step)
                value = value[step]

            return as_type(value) if as_type else value
        except KeyError:
            if default is not _NoDefault:
                return default
            else:
                raise ConfigurationError('no configuration for key {}'.format(self.separator.join(steps_taken)))

    def __getattr__(self, item):
        """
        TODO: Document me.
        """
        value = self.get(item, default=NotConfigured)
        if type(value) == dict:
            # deeper levels are treated as Configuration objects as well
            return Configuration(value)
        else:
            # value is not a dict, so it will either be an actual value or NotConfigured
            # in either case, it should be returned as provided
            return value


NotConfigured = Configuration()
# TODO: provide documentation for NotConfigured
# TODO: create some __str__-like thing on NotConfigured (monkey patching doesn't seem to work)
