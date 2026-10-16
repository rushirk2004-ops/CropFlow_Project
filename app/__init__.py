"""CropFlow Flask application factory.

Configures application settings, registers database teardown handlers,
registers blueprint routes, and seeds default demonstration data.
"""

import os
from flask import Flask, render_template
from config import config_by_name
from database.db import close_db, init_db, seed_sample_data


def create_app(config_name: str = None) -> Flask:
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    config_class = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_class)

    # Register database teardown
    app.teardown_appcontext(close_db)

    # Initialize database tables and initial sample data if not testing
    with app.app_context():
        try:
            init_db()
            if not app.config.get("TESTING"):
                seed_sample_data()
        except Exception as exc:
            app.logger.warning(f"Database auto-initialization notice: {exc}")

    # Register blueprints
    from app.routes.dashboard import dashboard_bp
    from app.routes.farms import farms_bp
    from app.routes.optimization import optimization_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(farms_bp)
    app.register_blueprint(optimization_bp)
    app.register_blueprint(reports_bp)

    from app.services.i18n import get_translation, get_all_translations
    from flask import request, redirect, jsonify, make_response

    # Context processors for templates
    @app.context_processor
    def inject_app_metadata():
        lang = request.cookies.get("cropflow_lang", "en")
        if lang not in ("en", "mr", "zh"):
            lang = "en"
        from markupsafe import Markup
        return {
            "app_name": "CropFlow",
            "app_version": "1.0.0",
            "app_tagline": get_translation("app_title", lang),
            "current_lang": lang,
            "currency_symbol": "₹",
            "t": lambda k: Markup(get_translation(k, lang)),
        }

    @app.route("/set-language/<lang_code>")
    def set_language(lang_code: str):
        if lang_code not in ("en", "mr", "zh"):
            lang_code = "en"
        target = request.referrer or "/dashboard"
        resp = make_response(redirect(target))
        resp.set_cookie("cropflow_lang", lang_code, max_age=30 * 24 * 3600, path="/")
        return resp

    @app.route("/api/translations")
    def api_translations():
        lang = request.args.get("lang") or request.cookies.get("cropflow_lang", "en")
        return jsonify(get_all_translations(lang))

    # Custom error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template(
            "index.html",
            error_message="The requested page was not found.",
        ), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template(
            "index.html",
            error_message="An internal server error occurred.",
        ), 500

    return app
