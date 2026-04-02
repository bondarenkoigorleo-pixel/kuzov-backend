"""API-роутер: каталог, корзина, заказы сельского магазина."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from models import (
    CartItem,
    Category,
    Order,
    OrderCreate,
    OrderStatus,
    Product,
)

router = APIRouter(prefix="/api/store", tags=["store"])

# ── Демо-каталог ──────────────────────────────────────────────────
PRODUCTS: dict[str, Product] = {}
ORDERS: dict[str, Order] = {}

DEMO_PRODUCTS = [
    Product(id="p1",  name="Хлеб белый",         category=Category.BREAD,      price=45,   unit="шт",  image="🍞", description="Свежий белый хлеб, 500 г"),
    Product(id="p2",  name="Хлеб ржаной",        category=Category.BREAD,      price=55,   unit="шт",  image="🍞", description="Ржаной хлеб, 600 г"),
    Product(id="p3",  name="Молоко 3.2%",         category=Category.DAIRY,      price=89,   unit="л",   image="🥛", description="Молоко пастеризованное, 1 л"),
    Product(id="p4",  name="Сметана 20%",         category=Category.DAIRY,      price=75,   unit="шт",  image="🥛", description="Сметана, 300 г"),
    Product(id="p5",  name="Творог 9%",           category=Category.DAIRY,      price=120,  unit="шт",  image="🧀", description="Творог домашний, 400 г"),
    Product(id="p6",  name="Масло сливочное",     category=Category.DAIRY,      price=160,  unit="шт",  image="🧈", description="Масло 82.5%, 200 г"),
    Product(id="p7",  name="Сахар",               category=Category.GROCERY,    price=65,   unit="кг",  image="🍬", description="Сахар-песок, 1 кг"),
    Product(id="p8",  name="Мука пшеничная",      category=Category.GROCERY,    price=70,   unit="кг",  image="🌾", description="Мука в/с, 2 кг"),
    Product(id="p9",  name="Масло подсолнечное",  category=Category.GROCERY,    price=140,  unit="л",   image="🫒", description="Масло рафинированное, 1 л"),
    Product(id="p10", name="Крупа гречневая",     category=Category.GROCERY,    price=95,   unit="кг",  image="🌾", description="Гречка, 900 г"),
    Product(id="p11", name="Рис",                 category=Category.GROCERY,    price=85,   unit="кг",  image="🍚", description="Рис круглозёрный, 900 г"),
    Product(id="p12", name="Макароны",            category=Category.GROCERY,    price=60,   unit="шт",  image="🍝", description="Макароны перья, 450 г"),
    Product(id="p13", name="Курица (бедро)",      category=Category.MEAT,       price=250,  unit="кг",  image="🍗", description="Бедро куриное, охлаждённое"),
    Product(id="p14", name="Фарш свино-говяжий",  category=Category.MEAT,       price=380,  unit="кг",  image="🥩", description="Фарш домашний"),
    Product(id="p15", name="Сосиски молочные",    category=Category.MEAT,       price=220,  unit="кг",  image="🌭", description="Сосиски, 500 г"),
    Product(id="p16", name="Картофель",           category=Category.VEGETABLES, price=35,   unit="кг",  image="🥔", description="Картофель свежий"),
    Product(id="p17", name="Морковь",             category=Category.VEGETABLES, price=40,   unit="кг",  image="🥕", description="Морковь мытая"),
    Product(id="p18", name="Лук репчатый",        category=Category.VEGETABLES, price=30,   unit="кг",  image="🧅", description="Лук жёлтый"),
    Product(id="p19", name="Капуста белокочанная", category=Category.VEGETABLES, price=28,  unit="кг",  image="🥬", description="Капуста свежая"),
    Product(id="p20", name="Чай чёрный",          category=Category.DRINKS,     price=110,  unit="шт",  image="🍵", description="Чай пакетированный, 100 шт"),
    Product(id="p21", name="Вода питьевая",       category=Category.DRINKS,     price=50,   unit="л",   image="💧", description="Вода негазированная, 5 л"),
    Product(id="p22", name="Средство для посуды", category=Category.HOUSEHOLD,  price=95,   unit="шт",  image="🧴", description="Средство для мытья посуды, 500 мл"),
    Product(id="p23", name="Стиральный порошок",  category=Category.HOUSEHOLD,  price=250,  unit="шт",  image="🧹", description="Порошок автомат, 3 кг"),
    Product(id="p24", name="Спички",              category=Category.HOUSEHOLD,  price=10,   unit="шт",  image="🔥", description="Спички бытовые, 10 коробков"),
]


def _seed() -> None:
    if not PRODUCTS:
        for p in DEMO_PRODUCTS:
            PRODUCTS[p.id] = p


_seed()


# ── Каталог ────────────────────────────────────────────────────────
@router.get("/products", response_model=list[Product])
def list_products(category: Category | None = Query(None)):
    items = list(PRODUCTS.values())
    if category:
        items = [p for p in items if p.category == category]
    return items


@router.get("/products/{product_id}", response_model=Product)
def get_product(product_id: str):
    if product_id not in PRODUCTS:
        raise HTTPException(404, "Товар не найден")
    return PRODUCTS[product_id]


@router.get("/categories")
def list_categories():
    return [{"value": c.value, "label": _cat_label(c)} for c in Category]


# ── Заказы ─────────────────────────────────────────────────────────
@router.post("/orders", response_model=Order)
def create_order(data: OrderCreate):
    if not data.items:
        raise HTTPException(400, "Корзина пуста")

    total = 0.0
    for item in data.items:
        product = PRODUCTS.get(item.product_id)
        if not product:
            raise HTTPException(400, f"Товар {item.product_id} не найден")
        total += product.price * item.quantity

    now = datetime.now()
    order = Order(
        id=uuid.uuid4().hex[:8],
        items=data.items,
        customer_name=data.customer_name,
        phone=data.phone,
        village=data.village,
        address=data.address,
        comment=data.comment,
        total=round(total, 2),
        created_at=now.isoformat(),
        estimated_delivery=(now + timedelta(hours=3)).strftime("%d.%m.%Y %H:%M"),
    )
    ORDERS[order.id] = order
    return order


@router.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    if order_id not in ORDERS:
        raise HTTPException(404, "Заказ не найден")
    return ORDERS[order_id]


@router.get("/orders", response_model=list[Order])
def list_orders():
    return list(ORDERS.values())


@router.patch("/orders/{order_id}/status")
def update_order_status(order_id: str, status: OrderStatus):
    if order_id not in ORDERS:
        raise HTTPException(404, "Заказ не найден")
    ORDERS[order_id].status = status
    return ORDERS[order_id]


# ── Helpers ────────────────────────────────────────────────────────
_CAT_LABELS = {
    Category.BREAD: "Хлеб",
    Category.DAIRY: "Молочные",
    Category.GROCERY: "Бакалея",
    Category.MEAT: "Мясо",
    Category.VEGETABLES: "Овощи",
    Category.DRINKS: "Напитки",
    Category.HOUSEHOLD: "Хозтовары",
    Category.OTHER: "Прочее",
}


def _cat_label(c: Category) -> str:
    return _CAT_LABELS.get(c, c.value)
