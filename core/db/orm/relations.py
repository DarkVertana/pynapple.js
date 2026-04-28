"""
core/db/orm/relations.py — relation loading for pynaple ORM

Supports two modes:
  - Eager loading via `include={"items": True}` on queries (batch-optimized)
  - Lazy loading via attribute access on model instances (on-demand)
"""

from __future__ import annotations

from core.db.orm import registry
from core.db.orm.fields import HasMany, HasOne, BelongsTo


# ── Eager loading (used by Client.find_many / find_unique with include) ──────

def load_relations(instances: list, model_cls, include: dict, conn_fn):
    """Eagerly load relations onto model instances.

    Uses batch queries (IN) to prevent N+1 problems.

    Args:
        instances: list of model instances to attach relations to
        model_cls: the model class (e.g. Order)
        include: dict of relation_name → True (e.g. {"items": True, "user": True})
        conn_fn: callable returning a sqlite3.Connection
    """
    if not instances or not include:
        return

    conn = conn_fn()

    for rel_name, should_load in include.items():
        if not should_load:
            continue

        # Find the relation descriptor on the model
        rel = None
        for r in model_cls._relations:
            if r.name == rel_name:
                rel = r
                break

        if rel is None:
            raise ValueError(
                f"No relation '{rel_name}' on {model_cls.__name__}. "
                f"Available: {', '.join(r.name for r in model_cls._relations)}"
            )

        target_cls = registry.get(rel.target)
        target_table = target_cls.__tablename__

        if isinstance(rel, BelongsTo):
            _load_belongs_to(instances, rel, target_cls, target_table, conn, conn_fn)
        elif isinstance(rel, (HasMany, HasOne)):
            _load_has_many(instances, rel, target_cls, target_table, conn, conn_fn, is_one=isinstance(rel, HasOne))


def _load_belongs_to(instances, rel, target_cls, target_table, conn, conn_fn):
    """Load parent records for a BelongsTo relation (batch IN query)."""
    fk_name = rel.foreign_key
    fk_values = list({getattr(inst, fk_name) for inst in instances if getattr(inst, fk_name) is not None})

    if not fk_values:
        for inst in instances:
            inst._rel_cache[rel.name] = None
            setattr(inst, rel.name, None)
        return

    pk = target_cls.get_primary_key()
    pk_name = pk.name if pk else "id"

    placeholders = ", ".join("?" for _ in fk_values)
    sql = f"SELECT * FROM {target_table} WHERE {pk_name} IN ({placeholders})"
    rows = conn.execute(sql, fk_values).fetchall()

    lookup = {}
    for row in rows:
        target_inst = target_cls.from_row(row, conn_fn=conn_fn)
        lookup[getattr(target_inst, pk_name)] = target_inst

    for inst in instances:
        fk_val = getattr(inst, fk_name)
        related = lookup.get(fk_val)
        inst._rel_cache[rel.name] = related
        setattr(inst, rel.name, related)


def _load_has_many(instances, rel, target_cls, target_table, conn, conn_fn, is_one=False):
    """Load child records for a HasMany/HasOne relation (batch IN query)."""
    pk = instances[0].__class__.get_primary_key()
    pk_name = pk.name if pk else "id"
    fk_name = rel.foreign_key

    pk_values = list({getattr(inst, pk_name) for inst in instances if getattr(inst, pk_name) is not None})

    if not pk_values:
        for inst in instances:
            inst._rel_cache[rel.name] = None if is_one else []
            setattr(inst, rel.name, None if is_one else [])
        return

    placeholders = ", ".join("?" for _ in pk_values)
    sql = f"SELECT * FROM {target_table} WHERE {fk_name} IN ({placeholders})"
    rows = conn.execute(sql, pk_values).fetchall()

    # Group results by FK value
    groups: dict[object, list] = {pk_val: [] for pk_val in pk_values}
    for row in rows:
        target_inst = target_cls.from_row(row, conn_fn=conn_fn)
        fk_val = getattr(target_inst, fk_name)
        if fk_val in groups:
            groups[fk_val].append(target_inst)

    for inst in instances:
        pk_val = getattr(inst, pk_name)
        related = groups.get(pk_val, [])
        if is_one:
            result = related[0] if related else None
        else:
            result = related
        inst._rel_cache[rel.name] = result
        setattr(inst, rel.name, result)


# ── Lazy loading (on attribute access) ───────────────────────────────────────

def lazy_load(instance, rel_name: str):
    """Load a single relation on demand when accessing an attribute.

    Called from Model.__getattr__ when the relation hasn't been eagerly loaded.
    """
    # Check cache first
    if rel_name in instance._rel_cache:
        return instance._rel_cache[rel_name]

    if instance._conn_fn is None:
        return None

    model_cls = instance.__class__
    rel = None
    for r in model_cls._relations:
        if r.name == rel_name:
            rel = r
            break

    if rel is None:
        raise AttributeError(f"No relation '{rel_name}' on {model_cls.__name__}")

    conn = instance._conn_fn()
    target_cls = registry.get(rel.target)
    target_table = target_cls.__tablename__

    if isinstance(rel, BelongsTo):
        fk_val = getattr(instance, rel.foreign_key, None)
        if fk_val is None:
            result = None
        else:
            pk = target_cls.get_primary_key()
            pk_name = pk.name if pk else "id"
            row = conn.execute(
                f"SELECT * FROM {target_table} WHERE {pk_name} = ? LIMIT 1",
                (fk_val,),
            ).fetchone()
            result = target_cls.from_row(row, conn_fn=instance._conn_fn) if row else None

    elif isinstance(rel, HasOne):
        pk = model_cls.get_primary_key()
        pk_val = getattr(instance, pk.name if pk else "id", None)
        if pk_val is None:
            result = None
        else:
            row = conn.execute(
                f"SELECT * FROM {target_table} WHERE {rel.foreign_key} = ? LIMIT 1",
                (pk_val,),
            ).fetchone()
            result = target_cls.from_row(row, conn_fn=instance._conn_fn) if row else None

    elif isinstance(rel, HasMany):
        pk = model_cls.get_primary_key()
        pk_val = getattr(instance, pk.name if pk else "id", None)
        if pk_val is None:
            result = []
        else:
            rows = conn.execute(
                f"SELECT * FROM {target_table} WHERE {rel.foreign_key} = ?",
                (pk_val,),
            ).fetchall()
            result = [target_cls.from_row(r, conn_fn=instance._conn_fn) for r in rows]

    else:
        return None

    instance._rel_cache[rel_name] = result
    setattr(instance, rel_name, result)
    return result
