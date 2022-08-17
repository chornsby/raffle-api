import uuid


def test_claim_ticket_success_response(client, override_ip, raffle):
    with override_ip("127.0.0.1"):
        response = client.post(f"/raffles/{raffle['raffle_id']}/participate/")

    assert response.status_code == 200

    assert 1 <= response.json()["ticket_number"] <= 3


def test_claim_ticket_does_not_exist(client, override_ip):
    with override_ip("127.0.0.1"):
        response = client.post(f"/raffles/{uuid.uuid4()}/participate/")

    assert response.status_code == 404
    assert response.json()["detail"] == "Raffle not found"


def test_claim_ticket_cannot_participate_twice(client, override_ip, raffle):
    with override_ip("127.0.0.1"):
        response = client.post(f"/raffles/{raffle['raffle_id']}/participate/")

    assert response.status_code == 200

    with override_ip("127.0.0.1"):
        response = client.post(f"/raffles/{raffle['raffle_id']}/participate/")

    assert response.status_code == 403
    assert response.json()["detail"] == "Already participated"


def test_claim_ticket_no_more_tickets(client, override_ip, raffle):
    with override_ip("127.0.0.1"):
        response = client.post(f"/raffles/{raffle['raffle_id']}/participate/")

    assert response.status_code == 200

    with override_ip("127.0.0.2"):
        response = client.post(f"/raffles/{raffle['raffle_id']}/participate/")

    assert response.status_code == 410
    assert response.json()["detail"] == "No tickets remaining"
