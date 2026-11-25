from flask import Flask, Response, jsonify
from werkzeug.exceptions import MethodNotAllowed, NotFound, RequestEntityTooLarge


class ApiError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def api_error(error: ApiError) -> tuple[Response, int]:
        return jsonify(error=str(error)), error.status

    @app.errorhandler(NotFound)
    @app.errorhandler(MethodNotAllowed)
    def missing_route(error: Exception) -> tuple[Response, int]:
        return jsonify(error="Route not found"), 404

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(error: RequestEntityTooLarge) -> tuple[Response, int]:
        return jsonify(error="Request body too large"), 413

    @app.errorhandler(Exception)
    def unexpected(error: Exception) -> tuple[Response, int]:
        app.logger.exception("Unhandled request error")
        return jsonify(error="Internal server error"), 500
