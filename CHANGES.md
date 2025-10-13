Changes
=======

development (main)
------------------

- Avoid crashing on template loaders containing `{extension}`, issue a deprecation warning when this is used.

0.17 (2025-10-08)
-----------------

- Drop support for Python 3.9.
- Introduce `confidence.Format` with three concrete implementations: `confidence.JSON`, `confidence.TOML` and `confidence.YAML`, which can be customized before use (e.g. `format = YAML(suffix='.yml')`).
- **Deprecate** the use of `extension` argument to loading functions and `encoding` argument to dumping functions, both can be controlled with a `confidence.Format`.

0.16.1 (2025-08-26)
-------------------

- Let `Configuration.get()` mimic the behaviour of `dict.get()`, returning `None` by default for missing keys.

0.16 (2025-04-18)
-----------------

- Drop support for Python 3.8.
- Add `merge` function to combine multiple mappings into a single `Configuration`.
- Enable the use of the binary or / union operator on `Configuration` instances, analogous to a builtin `dict` (e.g. `config = defaults | overrides`).

0.15 (2023-06-26)
-----------------

- Add `unwrap` function to the public API, unwrapping a `Configuration` object into a plain `dict` (note that references are not resolved and will remain references in the result).
- Change string-representations (result of `repr()`) of `Configuration` and `ConfigurationSequence` to be more like builtin types.

0.14 (2023-02-28)
-----------------

- Add system-wide `.../name/name.yaml` paths to the default load order, aiding in the use configuration *directories* (e.g. in containerized setups).
- Ensure non-confidence values can be dumped, enabling dumping of arbitrary bits of configuration.

0.13 (2023-01-02)
-----------------

- Avoid checking for existence of files, try to open them instead.
- Fix dumping / serialization issues by unwrapping complex wrapper types to their simple counterparts during initialization of `Configuration`.

0.12 (2022-03-01)
-----------------

- Use named loggers, default `confidence.*` library loggers to silence as [described in the docs](https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library).
- Resolve references in sequences.

0.11 (2021-11-25)
-----------------

- Parse values of environment variables as YAML values (e.g. `NAME_KEY=yes` will result in `key` being `True`).
- Add INFO-level logging of files and environment variables being used to load configuration.

0.10 (2021-08-04)
-----------------

- Remove configurable key separator, hardcode the default.
- Rename enumeration values (like `Locality.USER`) to be upper case.
- Add `dump`, `dumpf` and `dumps` functions to dump `Configuration` instances to YAML format.

0.9 (2021-02-01)
----------------

- Add type hints to confidence.

0.8 (2020-12-14)
----------------

- Add human-readable `repr`s to `Configuration` and `ConfigurationSequence`.
- Make `ConfigurationSequence` more list-like by enabling addition operator (`configured_sequence + [1, 2, 3]` or `(1, 2, 3) + configured_sequence`).

0.7 (2020-07-10)
----------------

- Auto-wrap configured sequences to enable 'list-of-dicts' style configuration while retaining `Configuration` functionality.

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

- Add `Missing` policy to control what to do with unconfigured keys on attribute access.
- Split single-file module into multi-module package (user-facing names importable from `confidence` package).
- Raise errors when merging / splitting non-`str` type keys, avoiding issues with confusing and broken access patterns.

0.5 (2019-02-01)
----------------

- Enable referencing keys from values.
- Enable customizing load order for `load_name` through `loaders` and `Locality` (default behaviour remains unchanged).

0.4.1 (2018-11-26)
------------------

- Warn about attribute access to configuration keys that collide with `Configuration` members.

0.4 (2018-07-09)
----------------

- Enable escaping underscores in environment variables (`NAME_FOO__BAR` results in `config.foo_bar`).
- Use `yaml.safe_load` to avoid security issues with `yaml.load`.
- Raise `AttributeError` when attempting to set a non-protected attribute on a `Configuration` instance.

0.3 (2018-05-24)
----------------

- Enable ignoring missing files in `loadf`.
- Fix crashes when reading empty or comment-only yaml files.

0.2 (2018-03-06)
----------------

- Read files from [XDG-specified](https://specifications.freedesktop.org/basedir-spec/latest/) directories.
- Read files form system-wide and user-local directories specified in environment variables `PROGRAMDATA`, `APPDATA` and `LOCALAPPDATA` (in that order).
- Read files from `/Library/Preferences` and `~/Library/Preferences`.

0.1.1 (2018-01-12)
------------------

- Expand user dirs for arguments to `loadf`, including values for `EXAMPLE_CONFIG_FILE` environment variables.

0.1 (2017-12-18)
----------------

- Initial release.
