import pytest


@pytest.fixture()
def raffles(client, raffle_factory):
    return [
        raffle_factory(name="raffle_1"),
        raffle_factory(name="raffle_2"),
    ]


def test_list_raffles_empty_response(client):
    response = client.get("/raffles/")

    assert response.status_code == 200
    assert response.json() == []


def test_list_raffles_most_recent_first(client, raffles):
    response = client.get("/raffles/")

    assert response.status_code == 200
    assert len(response.json()) == 2

    actual_1, actual_2 = response.json()
    expected_2, expected_1 = raffles

    assert actual_1["name"] == expected_1["name"]
    assert actual_2["name"] == expected_2["name"]
