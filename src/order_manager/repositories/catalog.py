from ..database import Database
from ..models import Product, Stock, Warehouse


class CatalogRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def products(self) -> list[Product]:
        rows = self.db.all("SELECT sku, name FROM products ORDER BY sku")
        return [Product(sku=row["sku"], name=row["name"]) for row in rows]

    def has_product(self, sku: str) -> bool:
        return self.db.get("SELECT 1 FROM products WHERE sku = ?", sku) is not None

    def warehouses(self) -> list[Warehouse]:
        rows = self.db.all("SELECT * FROM warehouses ORDER BY priority, id")
        return [Warehouse(id=row["id"], name=row["name"], priority=row["priority"]) for row in rows]

    def stock(self, warehouse_id: str) -> list[Stock]:
        rows = self.db.all(
            """SELECT warehouse_id, sku, on_hand, reserved, on_hand - reserved AS available
               FROM stock WHERE warehouse_id = ? ORDER BY sku""",
            warehouse_id,
        )
        return [
            Stock(warehouseId=row["warehouse_id"], sku=row["sku"], onHand=row["on_hand"],
                  reserved=row["reserved"], available=row["available"])
            for row in rows
        ]
