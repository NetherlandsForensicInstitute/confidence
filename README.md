confidence 😎
=============

Confidence makes it easy to load one or multiple sources of
configuration values and exposes them as a simple to use Python object.
Given the following YAML file:

~~~~ yaml
foo:
  bar: 42

foo.baz: '21 is only half the answer'

foobar: the answer is ${foo.bar}…
~~~~

Use it with confidence:

~~~~ python
# load configuration from a YAML file
configuration = confidence.loadf('path/to/configuration.yaml')

# a Configuration object is like a read-only dict, but better
value = configuration.get('foo.bar')
value = configuration.get('foo.bar', default=42)
# or even kwargs, should you want to
# (passing bar=42 and baz='21 is only half the answer')
function(**configuration.foo)

# namespaces are one honking great idea -- let's do more of those!
value = configuration.foo.bar
# they're even safe when values might be missing
value = configuration.foo.whoopsie
if value is NotConfigured:
    value = 42
# or, similar
value = configuration.foo.whoopsie or 42

# even references to other configured values will work
value = configuration.foobar  # 'the answer is 42…'
~~~~

Often, combining multiple sources of configuration can be useful when
defining defaults or reading from multiple files:

~~~~ python
configuration = confidence.loadf('/etc/system-wide-defaults.yaml',
                                 './local-overrides.yaml')

# confidence provides a convenient way of using this kind of precedence,
# letting 'more local' files take precedence over system-wide sources
# load_name will attempt to load multiple files, skipping ones that
# don't exist (using typical *nix paths, XDG-specified locations, some
# Windows environment variables and typical OSX paths):
# - /etc/xdg/app.yaml
# - /etc/app.yaml
# - /Library/Preferences/app.yaml
# - C:/ProgramData/app.yaml
# - ~/.config/app.yaml
# - ~/Library/Preferences/app.yaml
# - ~/AppData/Roaming/app.yaml
# - ~/.app.yaml
# - ./app.yaml

configuration = confidence.load_name('app')

# if set, load_name will take a look at environment variables like
# APP_FOO_BAR and APP_FOO_BAZ, mixing those in as foo.bar and foo.baz

# the default load order can be overridden if necessary:

configuration = confidence.load_name('app', load_order=confidence.loaders(
    # loading system after user makes system locations take precedence
    confidence.Locality.USER, confidence.Locality.SYSTEM
))

# prefer using .yml file names instead? tweak the format:

configuration = confidence.load_name('app', format=YAML('.yml'))

# it doesn't even need to be YAML, JSON is included:

configuration = confidence.load('app', format=JSON('.conf'))
~~~~

While powerful, no set of convenience functions will ever satisfy
everyone's use case. To be able to serve as wide an audience as
possible, confidence doesn't hide away its flexible internal API.

~~~~ python
# let's say application defaults are available as a dict in source
app_defaults = {'foo': {'bar': 42},
                'foo.baz': '21 is only half the answer'}

# and we've already created a way to read a dict from somewhere
def read_from_source(name):
    ...
    return read_values

# all of this can be combined to turn it into a single glorious Configuration instance
# precedence rules apply here, values from read_from_source will overwrite both
# app_defaults and values read from files (the latter of which will use some 
# user-supplied Format to read the file)
configuration = confidence.Configuration(
    app_defaults,
    # yeah, these would be a Configuration instances
    # remember it's just like a dict?
    confidence.loadf('path/to/app.yaml'),
    confidence.loadf('another/file/somewhere.ini', format=MyINIFormat),
    read_from_source('app'),
)

# make it so, no. 1
run_app(configuration)
~~~~
