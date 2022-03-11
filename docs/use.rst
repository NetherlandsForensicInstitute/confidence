How to use confidence
=====================

- loading files
- loading by name
- creating `.Configuration` objects manually
- fail-fast: missing

Logging
-------

``confidence`` uses the logging module in the standard library for its logging needs, but the loggers are silenced by default.
See logging's documentation to configure the logging mechanism for your needs.
Loggers are named after the module they're defined in, e.g. ``confidence.io``.
