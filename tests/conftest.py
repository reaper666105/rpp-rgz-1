import os

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture()
def app(tmp_path):
    """
    Test app factory.

    - If TEST_DATABASE_URL is set, tests will run against that DB (e.g. Postgres in CI).
    - Otherwise, uses a temporary SQLite file.
    """

    test_db_url = os.getenv("TEST_DATABASE_URL")
    if test_db_url:
        db_uri = test_db_url
    else:
        db_uri = f"sqlite:///{tmp_path / 'test.db'}"

    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": db_uri,
        }
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()

