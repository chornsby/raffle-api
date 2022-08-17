import uuid


def test_verify_ticket_success_response(client, raffle, manager_ip, override_ip):
    with override_ip("127.0.0.1"):
        response = client.post(f"/raffles/{raffle['raffle_id']}/participate/")

    payload = response.json()

    with override_ip(manager_ip):
        client.post(f"/raffles/{raffle['raffle_id']}/winners/")

    response = client.post(
        f"/raffles/{raffle['raffle_id']}/verify-ticket/",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json() == {"has_won": True, "prize": "prize"}


def test_verify_ticket_raffle_not_found(client):
    response = client.post(
        f"/raffles/{uuid.uuid4()}/verify-ticket/",
        json={
            "ticket_number": 1,
            "verification_code": "asdf",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Raffle not found"


def test_verify_ticket_raffle_winners_not_drawn(client, raffle):
    response = client.post(
        f"/raffles/{raffle['raffle_id']}/verify-ticket/",
        json={
            "ticket_number": 1,
            "verification_code": "asdf",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Winners not drawn"


def test_verify_ticket_ticket_not_found(client, raffle, manager_ip, override_ip):
    with override_ip("127.0.0.1"):
        client.post(f"/raffles/{raffle['raffle_id']}/participate/")

    with override_ip(manager_ip):
        client.post(f"/raffles/{raffle['raffle_id']}/winners/")

    response = client.post(
        f"/raffles/{raffle['raffle_id']}/verify-ticket/",
        json={
            "ticket_number": 2,
            "verification_code": "asdf",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Ticket not found"


def test_verify_ticket_verification_code_error(client, raffle, manager_ip, override_ip):
    with override_ip("127.0.0.1"):
        client.post(f"/raffles/{raffle['raffle_id']}/participate/")

    with override_ip(manager_ip):
        client.post(f"/raffles/{raffle['raffle_id']}/winners/")

    response = client.post(
        f"/raffles/{raffle['raffle_id']}/verify-ticket/",
        json={
            "ticket_number": 1,
            "verification_code": "asdf",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid verification code"
