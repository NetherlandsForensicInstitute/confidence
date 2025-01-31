# Loading configurations

Although confidence is internally divided in a number of modules, all of the functions and types intended for use are available to import from the confidence module.

```python
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
```

## Reading configuration from a file

Wrapping a `dict` with a [`Configuration`][confidence.Configuration] is nice, but configuration is more often found in files.
Confidence loads configuration from file in the YAML format:

```yaml
# suppose we'd save this as path/to/file.yaml
service:
  host: example.com
  port: 443
# note that we could also have expressed the two properties as
# service.host: ...
# service.port: ...
# dotted names are equivalent to nested ones
```

A single file like this can easily be loaded by [`loadf`][confidence.loadf]:

```python
# loadf simply takes a path or path-like to load configuration from
config = confidence.loadf('path/to/file.yaml')
# the result is the same as the example above, we can use config.service like we would a dict
connection = connect(**config.service)
```

## Reading from multiple files

If you split your configuration over multiple files as they contain configuration for different things, 
like a service to connect to and some local paths to store data, confidence can load them both as if they were one:

```yaml
# some system-wide configuration in /etc/paths.yaml
paths:
  data: /storage/data
  backup: /mnt/backup/data
```

```yaml
# service configuration as before, stored in path/to/service.yaml
service.host: example.com
service.port: 443
```

```python
# loadf can take multiple files, the contents of which are combined into a
# single Configuration object
config = confidence.loadf('/etc/paths.yaml', 'path/to/service.yaml')
# there's still something to connect to the service
connection = connect(**config.service)
# and some extra things that configure the place to backup to
connection.backup_to(config.paths.backup)
```
