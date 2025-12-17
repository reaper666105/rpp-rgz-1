import os

from dotenv import load_dotenv
from flask import Flask

from .api import api_bp
from .extensions import db


def create_app(test_config: dict | None = None) -> Flask:
    """
    Flask application factory.

    By default the app uses DATABASE_URL from environment (recommended: PostgreSQL).
    For convenience, if DATABASE_URL is not set, it falls back to a local SQLite file.
    """

    # Load local environment variables from .env if present (not committed to git).
    load_dotenv(override=False)

    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///inventory.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(api_bp)

    # Auto-create tables for convenience in educational project.
    if not app.testing:
        with app.app_context():
            db.create_all()

    return app

