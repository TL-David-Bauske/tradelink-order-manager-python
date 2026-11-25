from .database import Database


def seed_database(db: Database) -> None:
    with db.transaction() as connection:
        connection.executemany(
            "INSERT INTO products (sku, name) VALUES (?, ?)",
            [("BOLT-M8", "M8 bolt"), ("WASHER-M8", "M8 washer"), ("PACKING-TAPE", "Packing tape")],
        )
        connection.executemany(
            "INSERT INTO warehouses (id, name, priority) VALUES (?, ?, ?)",
            [("berlin", "Berlin", 10), ("hamburg", "Hamburg", 20), ("munich", "Munich", 30)],
        )
        connection.executemany(
            "INSERT INTO stock (warehouse_id, sku, on_hand) VALUES (?, ?, ?)",
            [
                ("berlin", "BOLT-M8", 10), ("berlin", "WASHER-M8", 10),
                ("hamburg", "BOLT-M8", 20), ("hamburg", "WASHER-M8", 20),
                ("hamburg", "PACKING-TAPE", 5),
                ("munich", "BOLT-M8", 50), ("munich", "WASHER-M8", 50),
                ("munich", "PACKING-TAPE", 10),
            ],
        )
