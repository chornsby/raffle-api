import uuid

import pytest


def test_list_winners_success_response(client, raffle, override_ip, manager_ip):
    with override_ip("127.0.0.1"):
        client.post(f"/raffles/{raffle['raffle_id']}/participate/")

    with override_ip(manager_ip):
        client.post(f"/raffles/{raffle['raffle_id']}/winners/")

    response = client.get(f"/raffles/{raffle['raffle_id']}/winners/")

    assert response.status_code == 200
    assert response.json() == [{"ticket_number": 1, "prize": "prize"}]


def test_list_winners_raffle_not_found(client):
    response = client.get(f"/raffles/{uuid.uuid4()}/winners/")

    assert response.status_code == 404


def test_list_winners_raffle_winners_not_drawn(client, raffle):
    response = client.get(f"/raffles/{raffle['raffle_id']}/winners/")

    assert response.status_code == 400
