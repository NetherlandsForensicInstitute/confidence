# Configure with `confidence` 😎

Confidence does two things: it helps loading configuration options from file(s) and presents those options as a user-friendly object at runtime.
Inspired by the way Python's own `pip` reads its configuration (try `pip config debug` if you're not familiar with `pip`'s configuration),
confidence uses a similarly flexible, but deterministic approach to combining information from multiple configuration files.
If that sounds awfully complicated, there's no requirement that you need to use anything that feels complicated.

As a quick overview, confidence contains the following features:

- a dict-like [`Configuration`][confidence.Configuration] object supporting attribute access to configured values;
- customizable loading of multiple sources (files, environment variables, …) into a single object with deterministic precedence of those sources;
- the ability to make and resolve references to values or entire namespaces.

Want to jump right in?
Check out [`confidence.load_name`][confidence.load_name] to get yourself a [`Configuration`][confidence.Configuration] as simple as this:

```python
# reading any files containing configuration for "myapp"
config = confidence.load_name('myapp')
# suppose myapp expects a dict… 
# that's fine, a Configuration quacks just like it 😎
myapp.run(config)
```
