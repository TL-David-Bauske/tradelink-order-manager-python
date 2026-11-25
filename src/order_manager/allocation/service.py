from dataclasses import dataclass

from ..database import Database
from ..models import Order, Warehouse
from ..repositories.catalog import CatalogRepository
from ..repositories.orders import OrderRepository
from .ranked_selector import RankedSelector


@dataclass
class AllocationResponse:
    status_code: int
    body: Order | dict[str, str]


class AllocationService:
    def __init__(self, db: Database, orders: OrderRepository, catalog: CatalogRepository) -> None:
        self.db = db
        self.orders = orders
        self.catalog = catalog

    def allocate(self, order_id: str) -> AllocationResponse:
        order = self.orders.find(order_id)
        if order is None:
            return AllocationResponse(404, {"error": "Order not found"})

        def qualifies(warehouse: Warehouse) -> bool:
            stock = self.catalog.stock(warehouse["id"])
            for item in order["items"]:
                product_stock = next((row for row in stock if row["sku"] == item["sku"]), None)
                if product_stock is None or product_stock["onHand"] < item["quantity"]:
                    return False
            return True

        selector = RankedSelector[Warehouse, tuple[int, str]](
            rank=lambda warehouse: (warehouse["priority"], warehouse["id"]),
            qualifies=qualifies,
        )
        warehouse = selector.select(self.catalog.warehouses())
        if warehouse is None:
            return AllocationResponse(409, {"error": "No warehouse can fulfill this order"})

        for item in order["items"]:
            self.db.run(
                "UPDATE stock SET reserved = reserved + ? WHERE warehouse_id = ? AND sku = ?",
                item["quantity"], warehouse["id"], item["sku"],
            )
        self.db.run(
            "UPDATE orders SET status = 'assigned', warehouse_id = ? WHERE id = ?",
            warehouse["id"], order_id,
        )
        assigned = self.orders.find(order_id)
        assert assigned is not None
        return AllocationResponse(200, assigned)
