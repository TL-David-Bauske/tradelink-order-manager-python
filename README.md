# Order manager

A small internal logistics API built with Python, Flask and SQLite.
It models products, warehouse stock and customer orders. There is no frontend.

## Run locally

Use Python 3.12 with SQLite 3.37 or newer. The application uses Python's
built-in SQLite driver. Run these commands from the repository root.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install --no-build-isolation -e .
python -m order_manager.scripts.seed
python -m order_manager.server
```

The API listens on port 3000. Override `PORT` or `DATABASE_PATH` with environment
variables. The default database is `data/orders.sqlite`. Seeding is explicit and
only works on an empty catalog; it never overwrites existing data. To start fresh,
stop the server, remove `data/orders.sqlite`, then seed again.

```sh
python -m unittest discover -s test
python -m mypy
python -m build --no-isolation
```

Tests use isolated, seeded in-memory databases and a threaded HTTP server on a
random local port. Requests share a SQLite connection. An explicit transaction
holds that connection until commit or rollback. The build writes a source
distribution and a wheel to `dist/`.

## Data model

- A product is identified by its SKU.
- A warehouse has a numeric priority used to order the warehouse listing.
- Stock tracks physical units (`onHand`) and units held for orders (`reserved`).
  Available stock is `onHand - reserved`; missing stock rows mean zero stock.
- An order has one or more unique product lines with positive integer quantities.
  It starts `pending`, with no warehouse. Creating an order does not reserve stock.

This is a trusted internal API; authentication, tenancy,
pagination and deployment infrastructure are outside the exercise.

## Endpoints

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/products` | List product SKUs and names |
| GET | `/warehouses` | List warehouses in priority order |
| GET | `/warehouses/:id/stock` | List stock, including reserved and available quantities |
| POST | `/orders` | Create an order, return 201 with a Location header |
| GET | `/orders` | List orders |
| GET | `/orders/:id` | Read an order |

```sh
curl -i http://localhost:3000/orders \
  -H 'Content-Type: application/json' \
  -d '{"items":[{"sku":"BOLT-M8","quantity":4},{"sku":"WASHER-M8","quantity":3}]}'
```

Responses use camelCase JSON. Errors have the shape `{ "error": "message" }`.
Invalid order input returns 400; missing resources return 404. Order bodies have
1–50 lines, quantities between 1 and 10,000 and a maximum body size of 16 KB.

Seed data contains Berlin (priority 10), Hamburg (20) and Munich (30).
Berlin holds bolts and washers; Hamburg and Munich also hold packing tape.
