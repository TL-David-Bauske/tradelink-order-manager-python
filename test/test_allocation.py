from helpers import ApiCase


class TestAllocation(ApiCase):
    def test_assigns_highest_priority_warehouse_and_reserves_every_line(self):
        created = self.post_order()
        self.assertEqual(created.status, 201)
        path = f"/orders/{created.body['id']}"
        response = self.request(f"{path}/allocate", method="POST")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body["status"], "assigned")
        self.assertEqual(response.body["warehouseId"], "berlin")
        self.assertEqual(self.request(path).body, response.body)
        stock = self.request("/warehouses/berlin/stock").body
        self.assertEqual(
            [(row["sku"], row["onHand"], row["reserved"], row["available"]) for row in stock],
            [("BOLT-M8", 10, 4, 6), ("WASHER-M8", 10, 3, 7)],
        )

    def test_skips_higher_priority_warehouse_missing_a_product(self):
        order = self.post_order([
            {"sku": "BOLT-M8", "quantity": 2}, {"sku": "PACKING-TAPE", "quantity": 1},
        ]).body
        response = self.request(f"/orders/{order['id']}/allocate", method="POST")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body["warehouseId"], "hamburg")

    def test_unfulfillable_order_stays_pending_without_splitting_stock(self):
        self.db.run("DELETE FROM stock WHERE sku = 'WASHER-M8' AND warehouse_id != 'berlin'")
        order = self.post_order([
            {"sku": "BOLT-M8", "quantity": 15}, {"sku": "WASHER-M8", "quantity": 3},
        ]).body
        path = f"/orders/{order['id']}"
        response = self.request(f"{path}/allocate", method="POST")
        self.assertEqual(response.status, 409)
        self.assertEqual(self.request(path).body, order)
        self.assertEqual(self.db.get("SELECT sum(reserved) FROM stock")[0], 0)

    def test_unknown_order_returns_404(self):
        response = self.request("/orders/missing/allocate", method="POST")
        self.assertEqual(response.status, 404)
        self.assertEqual(response.body, {"error": "Order not found"})
