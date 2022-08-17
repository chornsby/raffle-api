import pytest


def test_create_raffle_success_response(client, manager_ip, override_ip):
    with override_ip(manager_ip):
        response = client.post(
            "/raffles/",
            json={
                "name": "test",
                "total_tickets": 5,
                "prizes": [
                    {"name": "prize", "amount": 1},
                ],
            },
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["name"] == "test"
    assert payload["total_tickets"] == 5
    assert payload["available_tickets"] == 5
    assert payload["winners_drawn"] is False


def test_create_raffle_unauthorized(client, override_ip):
    with override_ip("127.0.0.1"):
        response = client.post(
            "/raffles/",
            json={
                "name": "test",
                "total_tickets": 5,
                "prizes": [
                    {"name": "prize", "amount": 1},
                ],
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Unauthorized"


@pytest.mark.parametrize(
    "json",
    [
        {
            "name": "test",
            "total_tickets": 5,
            "prizes": [],
        },
        {
            "name": "test",
            "total_tickets": 0,
            "prizes": [{"name": "prize", "amount": 1}],
        },
        {
            "name": "test",
            "total_tickets": -1,
            "prizes": [{"name": "prize", "amount": 1}],
        },
        {
            "name": "test",
            "total_tickets": 5,
            "prizes": [{"name": "prize", "amount": 0}],
        },
        {
            "name": "test",
            "total_tickets": 5,
            "prizes": [{"name": "prize", "amount": -1}],
        },
        {
            "name": "test",
            "total_tickets": 5,
            "prizes": [{"name": "", "amount": 1}],
        },
        {
            "name": "",
            "total_tickets": 5,
            "prizes": [{"name": "prize", "amount": 1}],
        },
    ],
)
def test_create_raffle_validation_error(client, json, manager_ip, override_ip):
    with override_ip(manager_ip):
        response = client.post("/raffles/", json=json)

    assert response.status_code == 422
