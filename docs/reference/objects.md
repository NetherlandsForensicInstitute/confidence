# Configuration objects

!!! info

    Note that [`Configuration`][confidence.Configuration] objects are designed to be immutable.
    Setting attributes is actively discouraged, create a new instance or use [`merge`][confidence.merge] 
    or the union operator to create a new [`Configuration`][confidence.Configuration] with the overridden changes.

::: confidence.Configuration
    options:
      members:
        - __init__
        - __getattr__
        - get
