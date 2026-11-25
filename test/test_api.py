import sqlite3
from concurrent.futures import ThreadPoolExecutor

from order_manager.repositories.orders import OrderRepository

from helpers import ApiCase


class TestOrdersApi(ApiCase):
    def test_creates_a_pending_order_and_reads_it_back(self):
        response = self.post_order()
        self.assertEqual(response.status, 201)
        order = response.body
        path = f"/orders/{order['id']}"
        self.assertEqual(response.headers["Location"], path)
        self.assertEqual(order["status"], "pending")
        self.assertIsNone(order["warehouseId"])
        self.assertEqual(order["items"], [
            {"sku": "BOLT-M8", "quantity": 4}, {"sku": "WASHER-M8", "quantity": 3},
        ])
        self.assertEqual(self.request(path).body, order)

    def test_rejects_invalid_quantities_unknown_products_duplicates_and_empty_orders(self):
        for items in [
            [], [{"sku": "BOLT-M8", "quantity": 0}], [{"sku": "BOLT-M8", "quantity": 1.5}],
            [{"sku": "UNKNOWN", "quantity": 1}],
            [{"sku": "BOLT-M8", "quantity": 1}, {"sku": "BOLT-M8", "quantity": 2}],
        ]:
            with self.subTest(items=items):
                self.assertEqual(self.post_order(items).status, 400)
        self.assertEqual(self.request("/orders").body, [])

    def test_catalog_stock_missing_resources_and_malformed_json(self):
        self.assertEqual(len(self.request("/products").body), 3)
        self.assertEqual(len(self.request("/warehouses").body), 3)
        self.assertEqual(self.request("/warehouses/berlin/stock").body[0]["available"], 10)
        for path in ["/orders/missing", "/warehouses/missing/stock", "/missing"]:
            response = self.request(path)
            self.assertEqual(response.status, 404)
            self.assertIsInstance(response.body["error"], str)
        self.assertEqual(self.request("/orders", method="POST", data=b"{").status, 400)

    def test_order_creation_rolls_back_all_writes_if_a_line_fails(self):
        orders = OrderRepository(self.db)
        with self.assertRaises(sqlite3.IntegrityError):
            orders.create([{"sku": "BOLT-M8", "quantity": 1}, {"sku": "UNKNOWN", "quantity": 1}])
        self.assertEqual(orders.list_orders(), [])
        self.assertEqual(self.db.get("SELECT count(*) FROM order_items")[0], 0)

    def test_database_prevents_invalid_stock_and_inconsistent_order_states(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.run("UPDATE stock SET reserved = 11 WHERE warehouse_id = ? AND sku = ?",
                        "berlin", "BOLT-M8")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.run("INSERT INTO orders (id, status) VALUES (?, ?)", "bad", "assigned")

    def test_concurrent_order_requests_persist_their_own_complete_orders(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(self.post_order) for _ in range(8)]
            responses = [future.result() for future in futures]
        self.assertTrue(all(response.status == 201 for response in responses))
        self.assertEqual(len({response.body["id"] for response in responses}), 8)
        self.assertTrue(all(len(response.body["items"]) == 2 for response in responses))
        self.assertEqual(len(self.request("/orders").body), 8)

    def test_failing_transaction_does_not_roll_back_another_concurrent_order(self):
        orders = OrderRepository(self.db)
        with ThreadPoolExecutor(max_workers=2) as pool:
            failed = pool.submit(orders.create, [
                {"sku": "BOLT-M8", "quantity": 1}, {"sku": "UNKNOWN", "quantity": 1},
            ])
            successful = pool.submit(orders.create, [{"sku": "BOLT-M8", "quantity": 2}])
            with self.assertRaises(sqlite3.IntegrityError):
                failed.result()
            successful.result()
        persisted = orders.list_orders()
        self.assertEqual(len(persisted), 1)
        self.assertEqual(persisted[0]["items"], [{"sku": "BOLT-M8", "quantity": 2}])
