# Written by Chiw the Neko <chiwtheneko@gmail.com>


def get_fqn(obj):
  cls = obj.__class__
  module = cls.__module__
  if module == 'builtins':
    return cls.__qualname__
  return f"{module}.{cls.__qualname__}"
