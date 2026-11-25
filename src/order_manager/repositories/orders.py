from uuid import uuid4

from ..database import Database
from ..models import Order, OrderItem


class OrderRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def find(self, order_id: str) -> Order | None:
        row = self.db.get("SELECT * FROM orders WHERE id = ?", order_id)
        if row is None:
            return None
        items = self.db.all(
            "SELECT sku, quantity FROM order_items WHERE order_id = ? ORDER BY sku", order_id
        )
        return Order(
            id=row["id"], status=row["status"], warehouseId=row["warehouse_id"],
            items=[OrderItem(sku=item["sku"], quantity=item["quantity"]) for item in items],
        )

    def list_orders(self) -> list[Order]:
        result = []
        for row in self.db.all("SELECT id FROM orders ORDER BY id"):
            order = self.find(row["id"])
            assert order is not None
            result.append(order)
        return result

    def create(self, items: list[OrderItem]) -> Order:
        order_id = str(uuid4())
        with self.db.transaction() as connection:
            connection.execute("INSERT INTO orders (id) VALUES (?)", (order_id,))
            connection.executemany(
                "INSERT INTO order_items (order_id, sku, quantity) VALUES (?, ?, ?)",
                [(order_id, item["sku"], item["quantity"]) for item in items],
            )
        order = self.find(order_id)
        assert order is not None
        return order
