import uuid


def test_draw_winners_success_response(client, raffle, override_ip, manager_ip):
    with override_ip("127.0.0.1"):
        client.post(f"/raffles/{raffle['raffle_id']}/participate/")

    with override_ip(manager_ip):
        response = client.post(f"/raffles/{raffle['raffle_id']}/winners/")

    assert response.status_code == 200
    assert response.json() == [{"ticket_number": 1, "prize": "prize"}]


def test_draw_winners_unauthorized(client, raffle, override_ip):
    with override_ip("127.0.0.1"):
        response = client.post(f"/raffles/{raffle['raffle_id']}/winners/")

    assert response.status_code == 403
    assert response.json()["detail"] == "Unauthorized"


def test_draw_winners_raffle_not_found(client, override_ip, manager_ip):
    with override_ip(manager_ip):
        response = client.post(f"/raffles/{uuid.uuid4()}/winners/")

    assert response.status_code == 404
    assert response.json()["detail"] == "Raffle not found"


def test_draw_winners_tickets_available(client, raffle, override_ip, manager_ip):
    with override_ip(manager_ip):
        response = client.post(f"/raffles/{raffle['raffle_id']}/winners/")

    assert response.status_code == 400
    assert response.json()["detail"] == "Tickets remaining"


def test_draw_winners_winners_already_drawn(client, raffle, override_ip, manager_ip):
    with override_ip("127.0.0.1"):
        client.post(f"/raffles/{raffle['raffle_id']}/participate/")

    with override_ip(manager_ip):
        response = client.post(f"/raffles/{raffle['raffle_id']}/winners/")

    assert response.status_code == 200

    with override_ip(manager_ip):
        response = client.post(f"/raffles/{raffle['raffle_id']}/winners/")

    assert response.status_code == 400
    assert response.json()["detail"] == "Winners already drawn"
