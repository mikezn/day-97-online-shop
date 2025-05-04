from . import db
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, ForeignKey, Numeric, Boolean, Nullable


class User(UserMixin, db.Model):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    # relationships
    orders = relationship("Order", back_populates="user")
    role = relationship("Role", back_populates="users")


class Role(db.Model):
    __tablename__ = "roles"
    role_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_admin: Mapped[bool] = mapped_column(Boolean)
    # relationships
    users = relationship("User", back_populates="role")


class Product(db.Model):
    __tablename__ = "products"
    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    # relationships
    order_products = relationship("OrderProduct", back_populates="product")


class Order(db.Model):
    __tablename__ = "orders"
    order_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    is_cart: Mapped[bool] = mapped_column(Boolean)
    # relationships
    user = relationship("User", back_populates="orders")
    order_products = relationship("OrderProduct", back_populates="order")


class OrderProduct(db.Model):
    __tablename__ = "order_products"
    order_product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    # relationships
    order = relationship("Order", back_populates="order_products")
    product = relationship("Product", back_populates="order_products")