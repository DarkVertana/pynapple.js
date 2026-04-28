"""
core/db/orm/fields.py — field types and relation descriptors

Column fields generate DDL fragments. Relation descriptors (HasMany, HasOne,
BelongsTo) are not columns — they wire up lazy/eager loading at query time.
"""


# ── Column Fields ────────────────────────────────────────────────────────────

class Field:
    """Base column field. Subclasses set `column_type`."""

    column_type: str = ""
    _creation_order: int = 0
    _counter: int = 0

    def __init__(
        self,
        *,
        primary_key: bool = False,
        autoincrement: bool = False,
        nullable: bool = True,
        unique: bool = False,
        default=None,
        default_sql: str | None = None,
        check: str | None = None,
    ):
        self.primary_key = primary_key
        self.autoincrement = autoincrement
        self.nullable = nullable
        self.unique = unique
        self.default = default
        self.default_sql = default_sql
        self.check = check
        self.name: str = ""  # set by ModelMeta

        # preserve declaration order
        Field._counter += 1
        self._creation_order = Field._counter

    @property
    def is_column(self) -> bool:
        return True

    def to_ddl(self) -> str:
        """Generate the column DDL fragment, e.g. 'email TEXT NOT NULL UNIQUE'."""
        parts = [self.name, self.column_type]

        if self.primary_key:
            parts.append("PRIMARY KEY")
            if self.autoincrement:
                parts.append("AUTOINCREMENT")

        if not self.nullable and not self.primary_key:
            parts.append("NOT NULL")

        if self.unique and not self.primary_key:
            parts.append("UNIQUE")

        if self.default_sql is not None:
            parts.append(f"DEFAULT ({self.default_sql})")
        elif self.default is not None:
            if isinstance(self.default, str):
                parts.append(f"DEFAULT '{self.default}'")
            elif isinstance(self.default, (int, float)):
                parts.append(f"DEFAULT {self.default}")

        if self.check:
            parts.append(f"CHECK ({self.check})")

        return " ".join(parts)


class Integer(Field):
    column_type = "INTEGER"


class Text(Field):
    column_type = "TEXT"


class Real(Field):
    column_type = "REAL"


class Blob(Field):
    column_type = "BLOB"


class ForeignKey(Field):
    """Integer column that references another model's primary key."""

    column_type = "INTEGER"

    def __init__(
        self,
        references: str,
        *,
        on_delete: str = "NO ACTION",
        on_update: str = "NO ACTION",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.references = references  # model class name, e.g. "User"
        self.on_delete = on_delete.upper()
        self.on_update = on_update.upper()

    def to_ddl(self) -> str:
        base = super().to_ddl()
        # The REFERENCES clause is appended as a column-level constraint.
        # The target table name is resolved later by the model metaclass,
        # but we store enough info to generate it in model.py's table DDL.
        return base

    def references_clause(self, target_table: str) -> str:
        """Generate the REFERENCES portion (called during full table DDL)."""
        clause = f"REFERENCES {target_table}(id)"
        if self.on_delete != "NO ACTION":
            clause += f" ON DELETE {self.on_delete}"
        if self.on_update != "NO ACTION":
            clause += f" ON UPDATE {self.on_update}"
        return clause


# ── Relation Descriptors (not columns) ───────────────────────────────────────

class _Relation:
    """Base for relation descriptors. These are NOT database columns."""

    def __init__(self, target: str, *, foreign_key: str):
        self.target = target        # model class name, e.g. "Order"
        self.foreign_key = foreign_key
        self.name: str = ""         # set by ModelMeta
        self._creation_order: int = 0

        Field._counter += 1
        self._creation_order = Field._counter

    @property
    def is_column(self) -> bool:
        return False


class HasMany(_Relation):
    """One-to-many: User.orders → [Order, Order, ...]"""
    pass


class HasOne(_Relation):
    """One-to-one: User.cart → Cart"""
    pass


class BelongsTo(_Relation):
    """Inverse of HasMany/HasOne: Order.user → User"""
    pass
