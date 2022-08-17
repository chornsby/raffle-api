import functools

from fastapi import Depends, HTTPException, Request
from psycopg import Connection
from psycopg_pool import ConnectionPool

from .config import Settings, load_settings
from .db import create_pool


@functools.cache
def get_settings() -> Settings:
    return load_settings()


@functools.cache
def get_pool(settings: Settings = Depends(get_settings)) -> ConnectionPool:
    return create_pool(settings)


def get_conn(pool: ConnectionPool = Depends(get_pool)) -> Connection:
    with pool.connection() as conn:
        yield conn


def get_ip_address(request: Request) -> str:
    return request.client.host


def is_manager(
    ip_address: str = Depends(get_ip_address),
    settings: Settings = Depends(get_settings),
):
    if ip_address not in settings.manager_ip_addresses:
        raise HTTPException(403, "Unauthorized")
