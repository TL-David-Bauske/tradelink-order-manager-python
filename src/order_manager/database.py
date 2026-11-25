import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from threading import Lock


SCHEMA = """
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
CREATE TABLE IF NOT EXISTS products (
  sku TEXT PRIMARY KEY,
  name TEXT NOT NULL
) STRICT;
CREATE TABLE IF NOT EXISTS warehouses (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  priority INTEGER NOT NULL CHECK (priority >= 0)
) STRICT;
CREATE TABLE IF NOT EXISTS stock (
  warehouse_id TEXT NOT NULL REFERENCES warehouses(id),
  sku TEXT NOT NULL REFERENCES products(sku),
  on_hand INTEGER NOT NULL CHECK (on_hand >= 0),
  reserved INTEGER NOT NULL DEFAULT 0 CHECK (reserved >= 0 AND reserved <= on_hand),
  PRIMARY KEY (warehouse_id, sku)
) STRICT;
CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'assigned')),
  warehouse_id TEXT REFERENCES warehouses(id),
  CHECK ((status = 'pending' AND warehouse_id IS NULL)
    OR (status = 'assigned' AND warehouse_id IS NOT NULL))
) STRICT;
CREATE TABLE IF NOT EXISTS order_items (
  order_id TEXT NOT NULL REFERENCES orders(id),
  sku TEXT NOT NULL REFERENCES products(sku),
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  PRIMARY KEY (order_id, sku)
) STRICT;
"""


class Database:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._lock = Lock()

    def get(self, sql: str, *parameters: str | int) -> sqlite3.Row | None:
        with self._lock:
            row: sqlite3.Row | None = self._connection.execute(sql, parameters).fetchone()
            return row

    def all(self, sql: str, *parameters: str | int) -> list[sqlite3.Row]:
        with self._lock:
            return self._connection.execute(sql, parameters).fetchall()

    def run(self, sql: str, *parameters: str | int) -> None:
        with self._lock:
            self._connection.execute(sql, parameters)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        # Hold the connection for the entire transaction, including rollback.
        with self._lock, self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            yield self._connection

    def close(self) -> None:
        with self._lock:
            self._connection.close()


def open_database(path: str | None = None) -> Database:
    if path is None:
        path = os.environ.get("DATABASE_PATH", "data/orders.sqlite")
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    try:
        connection.executescript(SCHEMA)
        return Database(connection)
    except sqlite3.Error:
        connection.close()
        raise
