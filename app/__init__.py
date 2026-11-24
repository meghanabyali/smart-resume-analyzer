"""Flask application factory."""
import logging
import os

from flask import Flask, jsonify, render_template, request

from .config import Config
from .models import db


def create_app(config_object=None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_object or Config)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    if app.config.get("CORS_ORIGINS"):
        from flask_cors import CORS

        origins = [o.strip() for o in app.config["CORS_ORIGINS"].split(",") if o.strip()]
        CORS(app, resources={r"/api/*": {"origins": origins}})

    from .routes.analysis_routes import analysis_bp
    from .routes.main_routes import main_bp
    from .routes.report_routes import report_bp
    from .routes.upload_routes import upload_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(report_bp)

    _register_error_handlers(app)
    _register_security_headers(app)

    with app.app_context():
        db.create_all()
        from .services.retention import purge_expired

        purge_expired()

    return app


def _wants_json() -> bool:
    return request.path.startswith("/api/") or request.accept_mimetypes.best == "application/json"


def _register_error_handlers(app: Flask) -> None:
    def respond(status: int, message: str):
        if _wants_json():
            return jsonify({"success": False, "error": message}), status
        return render_template("error.html", status=status, message=message), status

    @app.errorhandler(400)
    def bad_request(_e):
        return respond(400, "The request could not be processed.")

    @app.errorhandler(404)
    def not_found(_e):
        return respond(404, "The requested resource was not found. It may have been deleted or expired.")

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return respond(405, "This method is not allowed for the requested URL.")

    @app.errorhandler(413)
    def too_large(_e):
        limit = app.config["MAX_UPLOAD_MB"]
        return respond(413, f"The file is too large. The maximum allowed size is {limit:g} MB.")

    @app.errorhandler(500)
    def server_error(_e):
        # Never leak stack traces or internal details to the client.
        return respond(500, "An unexpected error occurred while processing your request.")


def _register_security_headers(app: Flask) -> None:
    csp = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
    )

    @app.after_request
    def add_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        # Access tokens live in URLs, so never leak them through the Referer header.
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Content-Security-Policy", csp)
        return response
