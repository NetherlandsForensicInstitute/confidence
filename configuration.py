class Configuration:
    separator = '.'

    def __init__(self, values):
        self.values = values

    def get(self, path, default=None, as_type=None):
        """
        Gets a value for the specified path.
        """
        value = self.values
        try:
            # walk through the values dictionary
            for step in path.split(self.separator):
                value = value[step]

            return as_type(value) if as_type else value
        except KeyError:
            return default
            # TODO: allow some sort of failure method that includes the step that went wrong
        except TypeError:
            return default
            # TODO: raise some kind of warning?


class NamespaceConfiguration(Configuration):
    def __getattr__(self, item):
        value = self.get(item)
        if type(value) == dict:
            # deeper levels are treated as NamespaceConfiguration objects as well
            return NamespaceConfiguration(value)
        else:
            # an actual value should just be retrieved
            return value
            # TODO:
