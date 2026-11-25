from typing import Literal, TypedDict


class Product(TypedDict):
    sku: str
    name: str


class Warehouse(TypedDict):
    id: str
    name: str
    priority: int


class Stock(TypedDict):
    warehouseId: str
    sku: str
    onHand: int
    reserved: int
    available: int


class OrderItem(TypedDict):
    sku: str
    quantity: int


class Order(TypedDict):
    id: str
    status: Literal["pending", "assigned"]
    warehouseId: str | None
    items: list[OrderItem]
