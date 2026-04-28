"""
core/db/orm/client.py — Prisma-style database client

Usage:
    from core.db.orm.client import Client
    db = Client()

    users = db.user.find_many(where={"role": "admin"})
    product = db.product.create(data={"name": "Widget", "price": 9.99})
"""

from __future__ import annotations

from core.db.database import get_conn
from core.db.orm import registry
from core.db.orm.query import QueryBuilder
from core.db.orm.relations import load_relations


class ModelProxy:
    """Proxy for a single model — provides the Prisma-like CRUD API.

    Accessed as db.user, db.product, etc.
    """

    def __init__(self, model_cls, conn_fn):
        self._model = model_cls
        self._qb = QueryBuilder(model_cls, conn_fn)
        self._conn_fn = conn_fn

    def find_many(
        self,
        where: dict | None = None,
        order_by: dict | None = None,
        limit: int | None = None,
        offset: int | None = None,
        include: dict | None = None,
    ) -> list:
        results = self._qb.find_many(where=where, order_by=order_by, limit=limit, offset=offset)
        if include:
            load_relations(results, self._model, include, self._conn_fn)
        return results

    def find_unique(self, where: dict, include: dict | None = None):
        result = self._qb.find_unique(where=where)
        if result and include:
            load_relations([result], self._model, include, self._conn_fn)
        return result

    def find_first(self, where: dict | None = None, order_by: dict | None = None, include: dict | None = None):
        result = self._qb.find_first(where=where, order_by=order_by)
        if result and include:
            load_relations([result], self._model, include, self._conn_fn)
        return result

    def create(self, data: dict):
        return self._qb.create(data)

    def create_many(self, data: list[dict]) -> int:
        return self._qb.create_many(data)

    def update(self, where: dict, data: dict):
        return self._qb.update(where=where, data=data)

    def update_many(self, where: dict, data: dict) -> int:
        return self._qb.update_many(where=where, data=data)

    def delete(self, where: dict) -> bool:
        return self._qb.delete(where=where)

    def delete_many(self, where: dict | None = None) -> int:
        return self._qb.delete_many(where=where)

    def count(self, where: dict | None = None) -> int:
        return self._qb.count(where=where)


class Client:
    """The main ORM client — instantiate once, access models as attributes.

        db = Client()
        db.user.find_many(...)
        db.product.create(...)

    Model proxies are created lazily and cached.
    """

    def __init__(self, conn_fn=None):
        self._conn_fn = conn_fn or get_conn
        self._proxies: dict[str, ModelProxy] = {}

    def __getattr__(self, name: str) -> ModelProxy:
        if name.startswith("_"):
            raise AttributeError(name)

        if name in self._proxies:
            return self._proxies[name]

        # Look up by lowercase model name
        for model_cls in registry.all_models():
            if model_cls.__name__.lower() == name:
                proxy = ModelProxy(model_cls, self._conn_fn)
                self._proxies[name] = proxy
                return proxy

        raise AttributeError(
            f"No model found for '{name}'. "
            f"Available: {', '.join(m.__name__.lower() for m in registry.all_models())}"
        )

    def raw(self, sql: str, params: tuple = ()) -> list:
        """Execute raw SQL and return list of Row objects."""
        return self._conn_fn().execute(sql, params).fetchall()

    def raw_execute(self, sql: str, params: tuple = ()) -> int:
        """Execute raw SQL (INSERT/UPDATE/DELETE) and return lastrowid."""
        conn = self._conn_fn()
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
