.. _examples:

Examples
========

Although confidence is internally divided in a number of modules, all of the functions and types intended for use are available to import from the confidence module.

.. code-block:: python

   # manually creating a Configuration object from a dict of values is about as
   # simple as it sounds:
   config = confidence.Configuration({
       'service.host': 'example.com',
       'service.port': 443,
   })

   # suppose there's a function connect that takes two arguments
   # we can connect to the configured host and port as such:
   connection = connect(config.service.host, config.service.port)
   # should the argument names align with the configuration (host and port),
   # we could treat the configured namespace "service" as a dict and pass it as such:
   connection = connect(**config.service)

Reading configuration from a file
---------------------------------

Wrapping a `dict` with a `Configuration` is nice, but configuration is more often found in files.
Confidence loads configuration from file in the YAML format:

.. code-block:: yaml

   # suppose we'd save this as path/to/file.yaml
   service:
     host: example.com
     port: 443
   # note that we could also have expressed the two properties as
   # service.host: ...
   # service.port: ...
   # dotted names are equivalent to nested ones

.. code-block:: python

   # loadf simply takes a path or path-like to load configuration from
   config = confidence.loadf('path/to/file.yaml')
   # the result is the same as the example above, we can use config.service like we would a dict
   connection = connect(**config.service)

Reading from multiple files
---------------------------

If you split your configuration over multiple files as they contain configuration for different things, like a service to connect to and some local paths to store data, confidence can load them both as if they were one:

.. code-block:: yaml

   # some system-wide configuration in /etc/paths.yaml
   paths:
     data: /storage/data
     backup: /mnt/backup/data

.. code-block:: yaml

   # service configuration as before, stored in path/to/service.yaml
   service.host: example.com
   service.port: 443

.. code-block:: python

   # loadf can take multiple files, the contents of which are combined into a
   # single Configuration object
   config = confidence.loadf('/etc/paths.yaml', 'path/to/service.yaml')

   # there's still something to connect to the service
   connection = connect(**config.service)
   # and some extra things that configure the place to backup to
   connection.backup_to(config.paths.backup)

Overriding defaults from one file to the next
---------------------------------------------

If values from multiple files overlap (like if ``/etc/paths.yaml`` would contain ``service.port: 80``), things become slightly more complicated.
Confidence uses a predictable :term:`precedence` of content here: the value that gets loaded last has the highest precedence (or 'wins').
`loadf` will load content in the order of the arguments that get passed, so ``service.port`` would be 443, as defined in ``path/to/service.yaml``.
You can use this behaviour to define defaults somewhere, that get overridden later:

.. code-block:: yaml

   # some system-wide configuration in /etc/paths.yaml
   service.port: 80

   paths:
     data: /storage/data
     backup: /mnt/backup/data

.. code-block:: yaml

   service:
     host: example.com
     port: 443

.. todo::

   - Configuration from a name
   - Configuration from multiple names
   - Configuration from reordered loaders
   - Configuration from mixed / custom loaders
