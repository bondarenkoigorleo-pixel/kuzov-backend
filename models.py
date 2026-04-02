"""Pydantic-модели для сельского магазина."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Категории товаров ──────────────────────────────────────────────
class Category(str, Enum):
    BREAD = "bread"
    DAIRY = "dairy"
    GROCERY = "grocery"
    MEAT = "meat"
    VEGETABLES = "vegetables"
    DRINKS = "drinks"
    HOUSEHOLD = "household"
    OTHER = "other"


# ── Товар ──────────────────────────────────────────────────────────
class Product(BaseModel):
    id: str
    name: str
    category: Category
    price: float = Field(ge=0)
    unit: str = "шт"
    image: str = ""
    in_stock: bool = True
    description: str = ""


# ── Позиция в корзине ─────────────────────────────────────────────
class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)


# ── Статус заказа ─────────────────────────────────────────────────
class OrderStatus(str, Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    COLLECTING = "collecting"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# ── Заказ (запрос) ────────────────────────────────────────────────
class OrderCreate(BaseModel):
    items: list[CartItem]
    customer_name: str
    phone: str
    village: str
    address: str
    comment: str = ""


# ── Заказ (ответ) ─────────────────────────────────────────────────
class Order(BaseModel):
    id: str
    items: list[CartItem]
    customer_name: str
    phone: str
    village: str
    address: str
    comment: str
    status: OrderStatus = OrderStatus.NEW
    total: float = 0
    created_at: str = ""
    estimated_delivery: str = ""
