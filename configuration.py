class ConfigurationError(KeyError):
    """
    TODO: Document me.
    """
    pass


# sentinel value to indicate no default is specified, allowing a default of
# None for Configuration.get()
_NoDefault = object()


class Configuration:
    """
    TODO: Document me.
    """

    def __init__(self, values=None, separator="."):
        self.values = values or {}
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


class NamespaceConfiguration(Configuration):
    """
    TODO: Document me.
    """

    def __getattr__(self, item):
        value = self.get(item, default=NotConfigured)
        if type(value) == dict:
            # deeper levels are treated as NamespaceConfiguration objects as well
            return NamespaceConfiguration(value)
        else:
            # value is not a dict, so it will either be an actual value or NotConfigured
            # in either case, it should be returned as provided
            return value


NotConfigured = NamespaceConfiguration()
# TODO: provide documentation for NotConfigured
# TODO: create some __str__-like thing on NotConfigured (monkey patching doesn't seem to work)
