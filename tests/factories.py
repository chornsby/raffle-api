from typing import Iterable

import pytest


@pytest.fixture()
def raffle_factory(client, manager_ip, override_ip):
    """Allow automatic creation of valid raffles."""

    def inner(
        *,
        name: str = "raffle",
        total_tickets: int = 1,
        prizes: Iterable[dict] = ({"name": "prize", "amount": 1},),
    ) -> dict:
        with override_ip(manager_ip):
            response = client.post(
                "/raffles/",
                json={
                    "name": name,
                    "total_tickets": total_tickets,
                    "prizes": list(prizes),
                },
            )
        return response.json()

    return inner


@pytest.fixture()
def raffle(client, raffle_factory) -> dict:
    """Create a default raffle for when no special values are required."""
    return raffle_factory()
