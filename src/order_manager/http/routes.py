import re

from flask import Blueprint, Response, g, jsonify

from ..allocation.service import AllocationService
from ..models import OrderItem
from ..repositories.catalog import CatalogRepository
from ..repositories.orders import OrderRepository
from .errors import ApiError


def parse_items(body: object, catalog: CatalogRepository) -> list[OrderItem]:
    lines = body.get("items") if isinstance(body, dict) else None
    if not isinstance(lines, list) or not 1 <= len(lines) <= 50:
        raise ApiError(400, "items must contain between 1 and 50 order lines")

    items: list[OrderItem] = []
    seen: set[str] = set()
    for line in lines:
        sku = line.get("sku") if isinstance(line, dict) else None
        quantity = line.get("quantity") if isinstance(line, dict) else None
        if (not isinstance(sku, str) or not re.fullmatch(r"[A-Z0-9-]{1,40}", sku)
                or isinstance(quantity, bool) or not isinstance(quantity, (int, float))
                or not 1 <= quantity <= 10000 or int(quantity) != quantity):
            raise ApiError(400, "Each item needs a valid sku and an integer quantity between 1 and 10000")
        if sku in seen:
            raise ApiError(400, "Duplicate product lines are not allowed")
        if not catalog.has_product(sku):
            raise ApiError(400, f"Unknown product: {sku}")
        seen.add(sku)
        items.append(OrderItem(sku=sku, quantity=int(quantity)))
    return items


def create_routes(
    orders: OrderRepository, catalog: CatalogRepository, allocation: AllocationService,
) -> Blueprint:
    routes = Blueprint("orders", __name__)

    @routes.get("/products")
    def products() -> Response:
        return jsonify(catalog.products())

    @routes.get("/warehouses")
    def warehouses() -> Response:
        return jsonify(catalog.warehouses())

    @routes.get("/warehouses/<warehouse_id>/stock")
    def stock(warehouse_id: str) -> Response:
        if not any(row["id"] == warehouse_id for row in catalog.warehouses()):
            raise ApiError(404, "Warehouse not found")
        return jsonify(catalog.stock(warehouse_id))

    @routes.get("/orders")
    def list_orders() -> Response:
        return jsonify(orders.list_orders())

    @routes.get("/orders/<order_id>")
    def get_order(order_id: str) -> Response:
        order = orders.find(order_id)
        if order is None:
            raise ApiError(404, "Order not found")
        return jsonify(order)

    @routes.post("/orders")
    def create_order() -> Response:
        order = orders.create(parse_items(g.json_body, catalog))
        response = jsonify(order)
        response.status_code = 201
        response.headers["Location"] = f"/orders/{order['id']}"
        return response

    @routes.post("/orders/<order_id>/allocate")
    def allocate_order(order_id: str) -> tuple[Response, int]:
        if orders.find(order_id) is None:
            raise ApiError(404, "Order not found")
        result = allocation.allocate(order_id)
        return jsonify(result.body), result.status_code

    return routes
