"""
core/db/orm/query.py — QueryBuilder for pynaple ORM

Builds and executes SQL from a Prisma-style dict API:

    where={"role": "admin"}                        → role = ?
    where={"price": {"gt": 50, "lt": 200}}        → price > ? AND price < ?
    where={"name": {"like": "%head%"}}             → name LIKE ?
    where={"id": {"in": [1, 2, 3]}}               → id IN (?, ?, ?)
    order_by={"created_at": "desc"}                → ORDER BY created_at DESC
"""

from __future__ import annotations
import sqlite3


# ── Operator mapping ─────────────────────────────────────────────────────────

_OPS = {
    "gt":     ">",
    "gte":    ">=",
    "lt":     "<",
    "lte":    "<=",
    "not":    "!=",
    "like":   "LIKE",
    "not_in": "NOT IN",
    "in":     "IN",
    "is_null": "IS",
}


# ── Where clause parser ─────────────────────────────────────────────────────

def parse_where(where: dict | None) -> tuple[str, list]:
    """Convert a Prisma-style where dict into SQL fragments + params.

    Returns (sql_fragment, params) where sql_fragment is like
    "role = ? AND price > ?" and params is [value1, value2].
    """
    if not where:
        return "", []

    clauses: list[str] = []
    params: list = []

    for field, value in where.items():
        if isinstance(value, dict):
            # Operator dict: {"gt": 50, "lt": 200}
            for op_key, op_val in value.items():
                if op_key == "is_null":
                    if op_val:
                        clauses.append(f"{field} IS NULL")
                    else:
                        clauses.append(f"{field} IS NOT NULL")
                elif op_key in ("in", "not_in"):
                    if not op_val:
                        # empty list — always false for IN, always true for NOT IN
                        clauses.append("1 = 0" if op_key == "in" else "1 = 1")
                    else:
                        placeholders = ", ".join("?" for _ in op_val)
                        sql_op = _OPS[op_key]
                        clauses.append(f"{field} {sql_op} ({placeholders})")
                        params.extend(op_val)
                elif op_key in _OPS:
                    clauses.append(f"{field} {_OPS[op_key]} ?")
                    params.append(op_val)
                else:
                    raise ValueError(f"Unknown operator: {op_key}")
        else:
            # Simple equality
            if value is None:
                clauses.append(f"{field} IS NULL")
            else:
                clauses.append(f"{field} = ?")
                params.append(value)

    return " AND ".join(clauses), params


# ── QueryBuilder ─────────────────────────────────────────────────────────────

class QueryBuilder:
    """Builds and executes SQL queries for a single model."""

    def __init__(self, model_cls, conn_fn):
        self._model = model_cls
        self._conn_fn = conn_fn
        self._table = model_cls.__tablename__

    @property
    def _conn(self) -> sqlite3.Connection:
        return self._conn_fn()

    def _wrap(self, row) -> object:
        """Wrap a sqlite3.Row into a model instance."""
        return self._model.from_row(row, conn_fn=self._conn_fn)

    def _wrap_many(self, rows) -> list:
        return [self._wrap(r) for r in rows]

    # ── SELECT ───────────────────────────────────────────────────────────────

    def find_many(
        self,
        where: dict | None = None,
        order_by: dict | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list:
        sql = f"SELECT * FROM {self._table}"
        params: list = []

        where_sql, where_params = parse_where(where)
        if where_sql:
            sql += f" WHERE {where_sql}"
            params.extend(where_params)

        if order_by:
            order_parts = []
            for col, direction in order_by.items():
                d = direction.upper()
                if d not in ("ASC", "DESC"):
                    raise ValueError(f"Invalid order direction: {direction}")
                order_parts.append(f"{col} {d}")
            sql += " ORDER BY " + ", ".join(order_parts)

        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        if offset is not None:
            sql += f" OFFSET {int(offset)}"

        rows = self._conn.execute(sql, params).fetchall()
        return self._wrap_many(rows)

    def find_unique(self, where: dict) -> object | None:
        sql = f"SELECT * FROM {self._table}"
        where_sql, params = parse_where(where)
        if where_sql:
            sql += f" WHERE {where_sql}"
        sql += " LIMIT 1"
        row = self._conn.execute(sql, params).fetchone()
        return self._wrap(row) if row else None

    def find_first(self, where: dict | None = None, order_by: dict | None = None) -> object | None:
        results = self.find_many(where=where, order_by=order_by, limit=1)
        return results[0] if results else None

    # ── INSERT ───────────────────────────────────────────────────────────────

    def create(self, data: dict) -> object:
        cols = list(data.keys())
        vals = list(data.values())
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(cols)

        sql = f"INSERT INTO {self._table} ({col_names}) VALUES ({placeholders})"
        conn = self._conn
        cur = conn.execute(sql, vals)
        conn.commit()

        # Fetch the newly created row
        pk = self._model.get_primary_key()
        if pk and pk.autoincrement:
            return self.find_unique(where={pk.name: cur.lastrowid})
        else:
            # For non-autoincrement PKs, use the provided data
            pk_val = data.get(pk.name) if pk else None
            if pk_val is not None:
                return self.find_unique(where={pk.name: pk_val})
            return self.find_unique(where=data)

    def create_many(self, data: list[dict]) -> int:
        """Bulk insert. Returns the number of rows inserted."""
        if not data:
            return 0
        cols = list(data[0].keys())
        placeholders = ", ".join("?" for _ in cols)
        col_names = ", ".join(cols)
        sql = f"INSERT INTO {self._table} ({col_names}) VALUES ({placeholders})"

        rows = [tuple(d[c] for c in cols) for d in data]
        conn = self._conn
        conn.executemany(sql, rows)
        conn.commit()
        return len(rows)

    # ── UPDATE ───────────────────────────────────────────────────────────────

    def update(self, where: dict, data: dict) -> object | None:
        set_cols = list(data.keys())
        set_vals = list(data.values())
        set_clause = ", ".join(f"{c} = ?" for c in set_cols)

        where_sql, where_params = parse_where(where)
        sql = f"UPDATE {self._table} SET {set_clause}"
        if where_sql:
            sql += f" WHERE {where_sql}"

        conn = self._conn
        conn.execute(sql, set_vals + where_params)
        conn.commit()
        return self.find_unique(where=where)

    def update_many(self, where: dict, data: dict) -> int:
        """Update multiple rows. Returns affected row count."""
        set_cols = list(data.keys())
        set_vals = list(data.values())
        set_clause = ", ".join(f"{c} = ?" for c in set_cols)

        where_sql, where_params = parse_where(where)
        sql = f"UPDATE {self._table} SET {set_clause}"
        if where_sql:
            sql += f" WHERE {where_sql}"

        conn = self._conn
        cur = conn.execute(sql, set_vals + where_params)
        conn.commit()
        return cur.rowcount

    # ── DELETE ───────────────────────────────────────────────────────────────

    def delete(self, where: dict) -> bool:
        where_sql, params = parse_where(where)
        sql = f"DELETE FROM {self._table}"
        if where_sql:
            sql += f" WHERE {where_sql}"
        sql += " LIMIT 1"  # SQLite supports LIMIT on DELETE when compiled with ENABLE_UPDATE_DELETE_LIMIT

        conn = self._conn
        # Fallback: if LIMIT not supported, use subquery
        try:
            cur = conn.execute(sql, params)
        except sqlite3.OperationalError:
            pk = self._model.get_primary_key()
            pk_name = pk.name if pk else "rowid"
            sql = (
                f"DELETE FROM {self._table} WHERE {pk_name} IN "
                f"(SELECT {pk_name} FROM {self._table}"
            )
            if where_sql:
                sql += f" WHERE {where_sql}"
            sql += " LIMIT 1)"
            cur = conn.execute(sql, params)

        conn.commit()
        return cur.rowcount > 0

    def delete_many(self, where: dict | None = None) -> int:
        where_sql, params = parse_where(where)
        sql = f"DELETE FROM {self._table}"
        if where_sql:
            sql += f" WHERE {where_sql}"

        conn = self._conn
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.rowcount

    # ── COUNT ────────────────────────────────────────────────────────────────

    def count(self, where: dict | None = None) -> int:
        sql = f"SELECT COUNT(*) FROM {self._table}"
        params: list = []
        where_sql, where_params = parse_where(where)
        if where_sql:
            sql += f" WHERE {where_sql}"
            params.extend(where_params)

        row = self._conn.execute(sql, params).fetchone()
        return row[0]
