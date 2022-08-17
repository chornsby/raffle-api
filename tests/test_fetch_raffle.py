import uuid


def test_fetch_raffle_success_response(client, raffle):
    url = f"/raffles/{raffle['raffle_id']}/"
    response = client.get(url)

    assert response.status_code == 200

    payload = response.json()

    assert payload["name"] == "raffle"
    assert payload["total_tickets"] == 1
    assert payload["available_tickets"] == 1
    assert payload["winners_drawn"] is False


def test_fetch_raffle_not_found(client):
    response = client.get(f"/raffles/{uuid.uuid4()}/")

    assert response.status_code == 404
    assert response.json()["detail"] == "Raffle not found"
