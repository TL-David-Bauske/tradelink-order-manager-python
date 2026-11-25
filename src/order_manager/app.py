import json
from typing import Never

from flask import Flask, g, request

from .database import Database
from .http.errors import ApiError, register_error_handlers
from .http.routes import create_routes
from .repositories.catalog import CatalogRepository
from .repositories.orders import OrderRepository


def reject_json_constant(value: str) -> Never:
    raise ValueError(f"Invalid JSON constant {value}")


def create_app(db: Database) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    app.url_map.strict_slashes = False

    @app.before_request
    def parse_json_body() -> None:
        g.json_body = None
        if request.mimetype == "application/json" and (data := request.get_data()):
            try:
                g.json_body = json.loads(data, parse_constant=reject_json_constant)
            except ValueError as error:
                raise ApiError(400, "Invalid JSON body") from error
            if not isinstance(g.json_body, (list, dict)):
                raise ApiError(400, "Invalid JSON body")

    app.register_blueprint(create_routes(OrderRepository(db), CatalogRepository(db)))
    register_error_handlers(app)
    return app
