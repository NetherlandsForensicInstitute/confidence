# Using a `Configuration`

## Configured values as attributes

```python
config = confidence.load_name('myapp')

myapp.run(config.host, config.port, config.debug)
```

## Keyword arguments

```python
config = confidence.load_name('myapp')

myapp.run(**config)
```

## Passing along subtrees

```python
config = confidence.load_name('myapp')

myapp.setup_database(**config.database)
myapp.run(config.myapp)
```
