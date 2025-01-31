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
