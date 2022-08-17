import psycopg.errors
import pytest

from raffle import db


def test_two_participants_cannot_claim_same_ticket(test_db_conn):
    raffle = db.queries.create_raffle(
        test_db_conn,
        name="raffle",
        total_tickets=1,
    )

    db.queries.create_tickets(
        test_db_conn,
        raffle_id=raffle.raffle_id,
        total_tickets=1,
    )

    ticket, *_ = db.queries.fetch_ticket_pool(
        test_db_conn,
        raffle_id=raffle.raffle_id,
        limit=1,
    )

    db.queries.claim_ticket(
        test_db_conn,
        raffle_id=raffle.raffle_id,
        ticket_number=ticket.ticket_number,
        ip_address="127.0.0.1",
        verification_code="asdf",
        crypt_algorithm="md5",
    )

    with pytest.raises(psycopg.errors.UniqueViolation):
        db.queries.claim_ticket(
            test_db_conn,
            raffle_id=raffle.raffle_id,
            ticket_number=ticket.ticket_number,
            ip_address="127.0.0.2",
            verification_code="asdf",
            crypt_algorithm="md5",
        )
