class ConfigurationError(KeyError):
    pass


# sentinel value to indicate no default is specified, allowing a default of
# None for Configuration.get()
_NoDefault = object()


class Configuration:
    separator = '.'

    def __init__(self, values):
        self.values = values

    def get(self, path, default=_NoDefault, as_type=None):
        """
        Gets a value for the specified path.
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
    def __getattr__(self, item):
        value = self.get(item, default=NotConfigured)
        if type(value) == dict:
            # deeper levels are treated as NamespaceConfiguration objects as well
            return NamespaceConfiguration(value)
        else:
            # value is not a dict, so it will either be an actual value or NotConfigured
            # in either case, it should be returned as provided
            return value


NotConfigured = NamespaceConfiguration(values={})
# TODO: create some __str__-like thing on NotConfigured (monkey patching doesn't seem to work)
