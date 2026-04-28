"""
core/db/orm/registry.py — global model registry

All Model subclasses auto-register here at class creation time.
The registry is used by the migration engine, query client, and relation
resolver to look up models by name.
"""

_models: dict[str, type] = {}


def register(cls):
    """Register a model class by its name."""
    _models[cls.__name__] = cls


def get(name: str):
    """Look up a model class by name. Raises KeyError if not found."""
    return _models[name]


def all_models() -> list[type]:
    """Return all registered model classes in registration order."""
    return list(_models.values())


def clear():
    """Clear the registry (useful for testing)."""
    _models.clear()
