import json
import threading
import unittest
from dataclasses import dataclass
from email.message import Message
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from werkzeug.serving import make_server

from order_manager.app import create_app
from order_manager.database import open_database
from order_manager.seed import seed_database


@dataclass
class Reply:
    status: int
    headers: Message
    body: Any


class ApiCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = open_database(":memory:")
        self.addCleanup(self.db.close)
        seed_database(self.db)
        server = make_server("127.0.0.1", 0, create_app(self.db), threaded=True)
        self.addCleanup(server.server_close)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02})
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        self.base_url = f"http://127.0.0.1:{server.server_port}"

    def request(self, path: str, *, method: str = "GET", data: bytes | None = None) -> Reply:
        req = Request(self.base_url + path, method=method, data=data)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            response = urlopen(req, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            return Reply(response.status, response.headers, json.load(response))

    def post_order(self, items: list[dict] | None = None) -> Reply:
        if items is None:
            items = [{"sku": "BOLT-M8", "quantity": 4}, {"sku": "WASHER-M8", "quantity": 3}]
        return self.request("/orders", method="POST", data=json.dumps({"items": items}).encode())
