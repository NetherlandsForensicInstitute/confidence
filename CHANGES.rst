Changes
=======

development (master)
--------------------



0.6.3 (2020-01-14)
------------------

- Restrict reference pattern to make a nested pattern work.

0.6.2 (2019-11-25)
------------------

- Make `Configuration` instances picklable.

0.6.1 (2019-04-12)
------------------

- Fix resolving references during loading when sources passed to `Configuration` are `Configuration` instances themselves.

0.6 (2019-04-05)
----------------

- Add `Missing` policy to control what to do with unconfigured keys on attribute access
- Split single-file module into multi-module package (user-facing names importable from `confidence` package)
- Raise errors when merging / splitting non-`str` type keys, avoiding issues with confusing and broken access patterns

0.5 (2019-02-01)
----------------

- Enable referencing keys from values
- Enable customizing load order for `load_name` through `loaders` and `Locality` (default behaviour remains unchanged)

0.4.1 (2018-11-26)
------------------

- Warn about attribute access to configuration keys that collide with `Configuration` members.

0.4 (2018-07-09)
----------------

- Enable escaping underscores in environment variables (``NAME_FOO__BAR`` results in ``config.foo_bar``).
- Use ``yaml.safe_load`` to avoid security issues with ``yaml.load``.
- Raise ``AttributeError`` when attempting to set a non-protected attribute on a `Configuration` instance.

0.3 (2018-05-24)
----------------

- Enable ignoring missing files in `loadf`.
- Fix crashes when reading empty or comment-only yaml files.

0.2 (2018-03-06)
----------------

- Read files from `XDG-specified <https://specifications.freedesktop.org/basedir-spec/latest/>`_ directories.
- Read files form system-wide and user-local directories specified in environment variables ``PROGRAMDATA``, ``APPDATA`` and ``LOCALAPPDATA`` (in that order).
- Read files from ``/Library/Preferences`` and ``~/Library/Preferences``.

0.1.1 (2018-01-12)
------------------

- Expand user dirs for arguments to `loadf`, including values for ``EXAMPLE_CONFIG_FILE`` environment variables.

0.1 (2017-12-18)
----------------

- Initial release.
