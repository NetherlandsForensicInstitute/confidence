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

.. todo::

   - Configuration from a single file
   - Configuration from multiple files
   - Configuration from a name
   - Configuration from multiple names
   - Configuration from reordered loaders
   - Configuration from mixed / custom loaders
