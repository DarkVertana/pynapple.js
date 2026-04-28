"""
core/db/orm/model.py — Model base class with metaclass

The metaclass collects Field instances, separates columns from relations,
sets field names, and registers the model in the global registry.
"""

from core.db.orm import registry
from core.db.orm.fields import Field, ForeignKey, _Relation


class _ModelMeta(type):
    """Metaclass that processes field declarations on Model subclasses."""

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        # Skip the base Model class itself
        if name == "Model" and not bases:
            return cls

        # Collect columns and relations
        columns: list[Field] = []
        relations: list[_Relation] = []

        for attr_name, attr_val in list(namespace.items()):
            if isinstance(attr_val, Field):
                attr_val.name = attr_name
                columns.append(attr_val)
            elif isinstance(attr_val, _Relation):
                attr_val.name = attr_name
                relations.append(attr_val)

        # Also pick up fields from parent classes (for inheritance)
        for base in bases:
            if hasattr(base, "_columns"):
                for col in base._columns:
                    if col.name not in {c.name for c in columns}:
                        columns.append(col)
            if hasattr(base, "_relations"):
                for rel in base._relations:
                    if rel.name not in {r.name for r in relations}:
                        relations.append(rel)

        # Sort by declaration order
        columns.sort(key=lambda f: f._creation_order)
        relations.sort(key=lambda r: r._creation_order)

        cls._columns = columns
        cls._relations = relations
        cls._column_names = [c.name for c in columns]

        # Ensure __tablename__ exists
        if not hasattr(cls, "__tablename__"):
            cls.__tablename__ = name.lower() + "s"

        # Composite unique constraints
        if not hasattr(cls, "__unique_together__"):
            cls.__unique_together__ = []

        # Remove relation descriptors from class dict so __getattr__ can
        # intercept them for lazy loading (otherwise class attr shadows instance)
        for rel in relations:
            if rel.name in cls.__dict__:
                delattr(cls, rel.name)

        # Register
        registry.register(cls)

        return cls


class Model(metaclass=_ModelMeta):
    """Base class for all ORM models.

    Subclasses declare fields as class attributes:

        class User(Model):
            __tablename__ = "users"
            id    = fields.Integer(primary_key=True, autoincrement=True)
            email = fields.Text(nullable=False, unique=True)
    """

    __tablename__: str
    __unique_together__: list[tuple[str, ...]]

    _columns: list[Field]
    _relations: list[_Relation]
    _column_names: list[str]

    def __init__(self, _conn_fn=None, **kwargs):
        self._conn_fn = _conn_fn
        self._rel_cache: dict[str, object] = {}
        for col_name in self._column_names:
            setattr(self, col_name, kwargs.get(col_name))

    @classmethod
    def from_row(cls, row, conn_fn=None):
        """Create a model instance from a sqlite3.Row or dict."""
        if row is None:
            return None
        data = dict(row) if not isinstance(row, dict) else row
        instance = cls(_conn_fn=conn_fn, **data)
        return instance

    def to_dict(self) -> dict:
        """Return a dict of column name → value."""
        return {name: getattr(self, name, None) for name in self._column_names}

    @classmethod
    def get_primary_key(cls) -> Field | None:
        """Return the primary key field, or None."""
        for col in cls._columns:
            if col.primary_key:
                return col
        return None

    @classmethod
    def get_foreign_keys(cls) -> list[ForeignKey]:
        """Return all ForeignKey columns."""
        return [c for c in cls._columns if isinstance(c, ForeignKey)]

    @classmethod
    def table_ddl(cls) -> str:
        """Generate the full CREATE TABLE statement."""
        lines = []
        for col in cls._columns:
            ddl = col.to_ddl()
            if isinstance(col, ForeignKey):
                target_cls = registry.get(col.references)
                ddl += " " + col.references_clause(target_cls.__tablename__)
            lines.append(f"    {ddl}")

        # Composite unique constraints
        for cols in cls.__unique_together__:
            col_list = ", ".join(cols)
            lines.append(f"    UNIQUE ({col_list})")

        body = ",\n".join(lines)
        return f"CREATE TABLE IF NOT EXISTS {cls.__tablename__} (\n{body}\n)"

    @classmethod
    def index_ddls(cls) -> list[str]:
        """Generate CREATE INDEX statements for all ForeignKey columns."""
        indexes = []
        for col in cls._columns:
            if isinstance(col, ForeignKey):
                idx_name = f"idx_{cls.__tablename__}_{col.name}"
                indexes.append(
                    f"CREATE INDEX IF NOT EXISTS {idx_name} "
                    f"ON {cls.__tablename__}({col.name})"
                )
        return indexes

    def __getattr__(self, name: str):
        # Only intercept relation names — avoid recursion on internal attrs
        if name.startswith("_"):
            raise AttributeError(name)
        rel_names = {r.name for r in self.__class__._relations}
        if name in rel_names:
            from core.db.orm.relations import lazy_load
            return lazy_load(self, name)
        raise AttributeError(
            f"'{self.__class__.__name__}' has no attribute '{name}'"
        )

    def __repr__(self):
        pk = self.get_primary_key()
        pk_val = getattr(self, pk.name, "?") if pk else "?"
        return f"<{self.__class__.__name__} {pk.name if pk else 'id'}={pk_val}>"
