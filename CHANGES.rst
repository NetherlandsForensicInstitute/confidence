Changes
=======

0.3 (2018-05-24)
----------------

- Enable ignoring missing files in ``loadf``.
- Fix crashes when reading empty or comment-only yaml files.

0.2 (2018-03-06)
----------------

- Read files from `XDG-specified <https://specifications.freedesktop.org/basedir-spec/latest/>`_ directories.
- Read files form system-wide and user-local directories specified in environment variables ``PROGRAMDATA``, ``APPDATA`` and ``LOCALAPPDATA`` (in that order).
- Read files from ``/Library/Preferences`` and ``~/Library/Preferences``.

0.1.1 (2018-01-12)
------------------

- Expand user dirs for arguments to ``loadf``, including values for ``EXAMPLE_CONFIG_FILE`` environment variables.

0.1 (2017-12-18)
----------------

- Initial release.
