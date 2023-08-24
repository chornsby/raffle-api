import contextlib

import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from raffle import db, deps
from raffle.api import app
from raffle.config import Settings, load_settings

pytest_plugins = ["factories"]


@pytest.fixture(scope="session")
def manager_ip() -> str:
    """Specify a unique ip address for test requests from a manager."""
    return "192.168.1.1"


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Access the local environment settings (needed to set up test database)."""
    return load_settings()


@pytest.fixture(scope="session")
def test_settings(manager_ip) -> Settings:
    """Override the local environment settings for testing."""
    return load_settings(
        PGDATABASE="test",
        manager_ip_addresses=[manager_ip],
        verification_code_crypt_algorithm="md5",
    )


@pytest.fixture(scope="session")
def test_db(settings, test_settings):
    """Create a test database if one does not already exist."""
    with db.create_connection(settings) as conn:
        try:
            conn.execute(f"create database {test_settings.db_database};")
        except psycopg.errors.DuplicateDatabase:
            pass


@pytest.fixture()
def test_db_conn(test_db, test_settings) -> psycopg.Connection:
    """Connect to the test database."""
    with db.create_connection(test_settings) as conn:
        yield conn


@pytest.fixture()
def reset_db(test_db_conn, test_settings):
    """Clean the test database by dropping and recreating the tables."""
    db.migrations.delete_schema(test_db_conn)
    db.migrations.create_schema(test_db_conn)


@pytest.fixture()
def test_app(reset_db, test_settings) -> FastAPI:
    """Create a test instance of the FastAPI app using test settings."""
    app.dependency_overrides = {deps.get_settings: lambda: test_settings}

    yield app

    app.dependency_overrides = {}


@pytest.fixture()
def client(test_app) -> TestClient:
    """Create a test client to make requests against the test FastAPI app."""
    return TestClient(test_app)


@pytest.fixture()
def override_ip(client):
    """Return a context manager to temporarily override the request ip address."""

    @contextlib.contextmanager
    def inner(ip_address: str):
        client.app.dependency_overrides[deps.get_ip_address] = lambda: ip_address
        yield
        client.app.dependency_overrides.pop(deps.get_ip_address)

    return inner
