"""
core/db/models.py — all model definitions for the pynaple js e-commerce schema

This file replaces schema.sql as the single source of truth for the database
structure. The migration engine reads these models to generate DDL.
"""

from core.db.orm import Model, fields


# ── Users ────────────────────────────────────────────────────────────────────

class User(Model):
    __tablename__ = "users"

    id            = fields.Integer(primary_key=True, autoincrement=True)
    name          = fields.Text(nullable=False)
    email         = fields.Text(nullable=False, unique=True)
    password_hash = fields.Text(nullable=False)
    role          = fields.Text(nullable=False, default="customer")
    created_at    = fields.Text(nullable=False, default_sql="datetime('now')")

    sessions = fields.HasMany("Session", foreign_key="user_id")
    cart     = fields.HasOne("Cart", foreign_key="user_id")
    orders   = fields.HasMany("Order", foreign_key="user_id")


# ── Sessions ─────────────────────────────────────────────────────────────────

class Session(Model):
    __tablename__ = "sessions"

    token      = fields.Text(primary_key=True)
    user_id    = fields.ForeignKey("User", nullable=False, on_delete="CASCADE")
    expires_at = fields.Text(nullable=False)

    user = fields.BelongsTo("User", foreign_key="user_id")


# ── Categories ───────────────────────────────────────────────────────────────

class Category(Model):
    __tablename__ = "categories"

    id   = fields.Integer(primary_key=True, autoincrement=True)
    name = fields.Text(nullable=False, unique=True)
    slug = fields.Text(nullable=False, unique=True)

    products = fields.HasMany("Product", foreign_key="category_id")


# ── Products ─────────────────────────────────────────────────────────────────

class Product(Model):
    __tablename__ = "products"

    id          = fields.Integer(primary_key=True, autoincrement=True)
    name        = fields.Text(nullable=False)
    description = fields.Text(nullable=False, default="")
    price       = fields.Real(nullable=False, check="price >= 0")
    stock       = fields.Integer(nullable=False, default=0, check="stock >= 0")
    image_url   = fields.Text(nullable=False, default="")
    category_id = fields.ForeignKey("Category", nullable=True, on_delete="SET NULL")
    created_at  = fields.Text(nullable=False, default_sql="datetime('now')")

    category = fields.BelongsTo("Category", foreign_key="category_id")


# ── Carts ────────────────────────────────────────────────────────────────────

class Cart(Model):
    __tablename__ = "carts"

    id          = fields.Integer(primary_key=True, autoincrement=True)
    user_id     = fields.ForeignKey("User", nullable=True, unique=True, on_delete="CASCADE")
    guest_token = fields.Text(nullable=True, unique=True)
    created_at  = fields.Text(nullable=False, default_sql="datetime('now')")

    user  = fields.BelongsTo("User", foreign_key="user_id")
    items = fields.HasMany("CartItem", foreign_key="cart_id")


# ── Cart Items ───────────────────────────────────────────────────────────────

class CartItem(Model):
    __tablename__ = "cart_items"
    __unique_together__ = [("cart_id", "product_id")]

    id         = fields.Integer(primary_key=True, autoincrement=True)
    cart_id    = fields.ForeignKey("Cart", nullable=False, on_delete="CASCADE")
    product_id = fields.ForeignKey("Product", nullable=False, on_delete="CASCADE")
    quantity   = fields.Integer(nullable=False, default=1, check="quantity > 0")

    cart    = fields.BelongsTo("Cart", foreign_key="cart_id")
    product = fields.BelongsTo("Product", foreign_key="product_id")


# ── Orders ───────────────────────────────────────────────────────────────────

class Order(Model):
    __tablename__ = "orders"

    id               = fields.Integer(primary_key=True, autoincrement=True)
    user_id          = fields.ForeignKey("User", nullable=True, on_delete="SET NULL")
    status           = fields.Text(nullable=False, default="pending")
    total            = fields.Real(nullable=False, check="total >= 0")
    shipping_name    = fields.Text(nullable=False, default="")
    shipping_address = fields.Text(nullable=False, default="")
    shipping_city    = fields.Text(nullable=False, default="")
    shipping_zip     = fields.Text(nullable=False, default="")
    created_at       = fields.Text(nullable=False, default_sql="datetime('now')")

    user  = fields.BelongsTo("User", foreign_key="user_id")
    items = fields.HasMany("OrderItem", foreign_key="order_id")


# ── Order Items ──────────────────────────────────────────────────────────────

class OrderItem(Model):
    __tablename__ = "order_items"

    id           = fields.Integer(primary_key=True, autoincrement=True)
    order_id     = fields.ForeignKey("Order", nullable=False, on_delete="CASCADE")
    product_id   = fields.ForeignKey("Product", nullable=True, on_delete="SET NULL")
    product_name = fields.Text(nullable=False)
    price        = fields.Real(nullable=False)
    quantity     = fields.Integer(nullable=False, check="quantity > 0")

    order   = fields.BelongsTo("Order", foreign_key="order_id")
    product = fields.BelongsTo("Product", foreign_key="product_id")


# ── Blog Posts ──────────────────────────────────────────────────────────────

class Post(Model):
    __tablename__ = "posts"

    id          = fields.Integer(primary_key=True, autoincrement=True)
    title       = fields.Text(nullable=False)
    slug        = fields.Text(nullable=False, unique=True)
    excerpt     = fields.Text(nullable=False, default="")
    body        = fields.Text(nullable=False, default="")
    cover_image = fields.Text(nullable=False, default="")
    published   = fields.Integer(nullable=False, default=0)
    author_id   = fields.ForeignKey("User", nullable=True, on_delete="SET NULL")
    created_at  = fields.Text(nullable=False, default_sql="datetime('now')")
    updated_at  = fields.Text(nullable=False, default_sql="datetime('now')")

    author = fields.BelongsTo("User", foreign_key="author_id")
