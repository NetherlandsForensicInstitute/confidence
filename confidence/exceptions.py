import typing


class ConfigurationError(KeyError):
    pass


class MergeConflictError(ConfigurationError):
    """
    Error raised during loading configuration sources that conflict internally.
    """
    def __init__(self, *args: typing.Any, key: str):
        super().__init__(*args)
        self.conflict = key


class NotConfiguredError(ConfigurationError):
    """
    Error raised when a requested configuration key is unavailable and no
    default / fallback value is provided.
    """
    def __init__(self, *args: typing.Any, key: str):
        super().__init__(*args)
        self.key = key


class ConfiguredReferenceError(ConfigurationError):
    """
    Error raised a referenced configuration key is unavailable.
    """
    def __init__(self, *args: typing.Any, key: str):
        super().__init__(*args)
        self.key = key
