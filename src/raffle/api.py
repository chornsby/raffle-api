"""An example raffle API developed in Python using FastAPI.

For the purposes of this project, a [raffle](https://en.wikipedia.org/wiki/Raffle)
is a gambling game played where individual players claim tickets in the hopes of
winning a prize. Each ticket has a unique number and verification code. Once
every ticket has been claimed, a **manager** may draw the winners and assign a
winning ticket to each prize. Players can check the winning ticket numbers and
verify whether their ticket has won a prize by providing their ticket number and
verification code.

See the project `README.md` file for more details.
"""
import random
import uuid

import psycopg
import pydantic
from fastapi import Depends, FastAPI, HTTPException
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt

from raffle.config import Settings

from . import db, deps, verification

app = FastAPI(title="Raffle API", description=__doc__)


class CreatePrizeRequest(pydantic.BaseModel):
    name: str = pydantic.Field(..., example="Prize Name", min_length=1)
    amount: pydantic.PositiveInt = pydantic.Field(..., example=1)


class CreateRaffleRequest(pydantic.BaseModel):
    name: str = pydantic.Field(..., example="Raffle Name", min_length=1)
    total_tickets: pydantic.PositiveInt = pydantic.Field(..., example=100)
    prizes: list[CreatePrizeRequest] = pydantic.Field(min_items=1)


class PrizeResponse(pydantic.BaseModel):
    name: str = pydantic.Field(..., example="Prize Name", min_length=1)
    amount: pydantic.PositiveInt = pydantic.Field(..., example=1)


class RaffleResponse(pydantic.BaseModel):
    raffle_id: pydantic.UUID4 = pydantic.Field(..., example=uuid.uuid4())
    name: str = pydantic.Field(..., example="Raffle Name", min_length=1)
    total_tickets: pydantic.PositiveInt = pydantic.Field(..., example=100)
    available_tickets: pydantic.NonNegativeInt = pydantic.Field(..., example=50)
    winners_drawn: bool = pydantic.Field(..., example=False)
    prizes: list[PrizeResponse] = pydantic.Field(min_items=1)


@app.get("/raffles/", response_model=list[RaffleResponse])
def list_raffles(
    conn: psycopg.Connection = Depends(deps.get_conn),
) -> list[RaffleResponse]:
    """Return a list of the most recently created raffles and their prizes."""
    rows = db.queries.list_raffles(conn, limit=10)
    return [
        RaffleResponse(
            raffle_id=row.raffle_id,
            name=row.name,
            total_tickets=row.total_tickets,
            available_tickets=row.available_tickets,
            winners_drawn=row.winners_drawn,
            prizes=[
                PrizeResponse(name=prize["name"], amount=prize["amount"])
                for prize in row.prizes
            ],
        )
        for row in rows
    ]


@app.post(
    "/raffles/",
    dependencies=[Depends(deps.is_manager)],
    response_model=RaffleResponse,
    responses={
        403: {
            "content": {
                "application/json": {
                    "example": {"detail": "Unauthorized"},
                }
            }
        },
    },
)
def create_raffle(
    request: CreateRaffleRequest,
    conn: psycopg.Connection = Depends(deps.get_conn),
) -> RaffleResponse:
    """Create a new raffle and allocate tickets and prizes.

    Only requests from configured **manager** ip addresses will succeed.
    """
    with conn.transaction():
        row = db.queries.create_raffle(
            conn,
            name=request.name,
            total_tickets=request.total_tickets,
        )

        db.queries.create_tickets(
            conn,
            raffle_id=row.raffle_id,
            total_tickets=request.total_tickets,
        )

        db.queries.create_prizes(
            conn,
            [
                {"raffle_id": row.raffle_id, "name": prize.name, "amount": prize.amount}
                for prize in request.prizes
            ],
        )

    return RaffleResponse(
        raffle_id=row.raffle_id,
        name=row.name,
        total_tickets=row.total_tickets,
        available_tickets=row.available_tickets,
        winners_drawn=row.winners_drawn,
        prizes=[
            PrizeResponse(name=prize.name, amount=prize.amount)
            for prize in request.prizes
        ],
    )


@app.get(
    "/raffles/{raffle_id}/",
    response_model=RaffleResponse,
    responses={
        404: {
            "content": {
                "application/json": {
                    "example": {"detail": "Raffle not found"},
                }
            }
        }
    },
)
def fetch_raffle(
    raffle_id: pydantic.UUID4,
    conn: psycopg.Connection = Depends(deps.get_conn),
) -> RaffleResponse:
    """Return an individual raffle details based on its identifier."""
    row = db.queries.fetch_raffle(conn, raffle_id=raffle_id)

    if row is None:
        raise HTTPException(404, "Raffle not found")

    return RaffleResponse(
        raffle_id=row.raffle_id,
        name=row.name,
        total_tickets=row.total_tickets,
        available_tickets=row.available_tickets,
        winners_drawn=row.winners_drawn,
        prizes=[
            PrizeResponse(name=prize["name"], amount=prize["amount"])
            for prize in row.prizes
        ],
    )


class ClaimTicketResponse(pydantic.BaseModel):
    ticket_number: pydantic.PositiveInt = pydantic.Field(..., example=5)
    verification_code: str = pydantic.Field(..., example="LDSFIUEN")


@app.post(
    "/raffles/{raffle_id}/participate/",
    response_model=ClaimTicketResponse,
    responses={
        403: {
            "content": {
                "application/json": {
                    "example": {"detail": "Already participated"},
                }
            },
        },
        404: {
            "content": {
                "application/json": {
                    "example": {"detail": "Raffle not found"},
                }
            },
        },
        410: {
            "content": {
                "application/json": {
                    "example": {"detail": "No tickets remaining"},
                }
            },
        },
        500: {
            "content": {
                "application/json": {
                    "example": {"detail": "Concurrency error"},
                }
            },
        },
    },
)
def claim_ticket(
    raffle_id: pydantic.UUID4,
    ip_address: str = Depends(deps.get_ip_address),
    conn: psycopg.Connection = Depends(deps.get_conn),
    settings: Settings = Depends(deps.get_settings),
) -> ClaimTicketResponse:
    """Attempt to claim a ticket in the given raffle.

    This can fail in a number of interesting ways:

    1. No available tickets remain
    2. The IP address has already participated
    3. The ticket intended to be claimed has been taken by another process

    Of these, only the third case is retryable. It is left to the caller to
    retry or present an appropriate error to the user.

    To reduce the likelihood of the third case, we randomly choose a ticket to
    claim from a configurable sized pool of the next tickets in line. If we see
    high contention for claiming tickets then this pool size can be increased.
    """
    row = db.queries.fetch_raffle(conn, raffle_id=raffle_id)

    if row is None:
        raise HTTPException(404, "Raffle not found")

    has_participated = db.queries.has_ip_address_participated(
        conn,
        raffle_id=raffle_id,
        ip_address=ip_address,
    )

    if has_participated:
        raise HTTPException(403, "Already participated")

    verification_code = verification.generate_verification_code(
        population=settings.verification_code_allowed_characters,
        k=settings.verification_code_length,
    )

    try:
        for attempt in Retrying(
            reraise=True,
            retry=retry_if_exception_type(psycopg.errors.UniqueViolation),
            stop=stop_after_attempt(settings.participate_max_attempts),
        ):
            with attempt:
                ticket_pool = db.queries.fetch_ticket_pool(
                    conn,
                    raffle_id=row.raffle_id,
                    limit=settings.participate_ticket_pool,
                )

                if not ticket_pool:
                    raise HTTPException(410, "No tickets remaining")

                ticket = random.choice(ticket_pool)

                with conn.transaction():
                    db.queries.claim_ticket(
                        conn,
                        raffle_id=row.raffle_id,
                        ticket_number=ticket.ticket_number,
                        ip_address=ip_address,
                        verification_code=verification_code,
                        crypt_algorithm=settings.verification_code_crypt_algorithm,
                    )
                    db.queries.release_ticket(conn, raffle_id=raffle_id)
    except psycopg.errors.UniqueViolation:
        raise HTTPException(500, "Concurrency error")

    return ClaimTicketResponse(
        ticket_number=ticket.ticket_number,
        verification_code=verification_code,
    )


class WinnerResponse(pydantic.BaseModel):
    ticket_number: pydantic.PositiveInt = pydantic.Field(..., example=5)
    prize: str = pydantic.Field(..., example="Prize Name")


@app.get("/raffles/{raffle_id}/winners/", response_model=list[WinnerResponse])
def list_winners(
    raffle_id: pydantic.UUID4,
    conn: psycopg.Connection = Depends(deps.get_conn),
) -> list[WinnerResponse]:
    """Return a list of all winners for the given raffle and their prizes."""
    raffle = db.queries.fetch_raffle(conn, raffle_id=raffle_id)

    if raffle is None:
        raise HTTPException(404)

    if not raffle.winners_drawn:
        raise HTTPException(400)

    rows = db.queries.list_winners(conn, raffle_id=raffle_id)

    return [
        WinnerResponse(
            ticket_number=row.ticket_number,
            prize=row.prize,
        )
        for row in rows
    ]


@app.post(
    "/raffles/{raffle_id}/winners/",
    dependencies=[Depends(deps.is_manager)],
    response_model=list[WinnerResponse],
    responses={
        400: {
            "content": {
                "application/json": {
                    "examples": {
                        "tickets_remaining": {
                            "summary": "Tickets remaining",
                            "value": {"detail": "Tickets remaining"},
                        },
                        "winners_drawn": {
                            "summary": "Winners already drawn",
                            "value": {"detail": "Winners already drawn"},
                        },
                    }
                }
            }
        },
        403: {
            "content": {
                "application/json": {
                    "example": {"detail": "Unauthorized"},
                }
            }
        },
        404: {
            "content": {
                "application/json": {
                    "example": {"detail": "Raffle not found"},
                }
            }
        },
    },
)
def draw_winners(
    raffle_id: pydantic.UUID4,
    conn: psycopg.Connection = Depends(deps.get_conn),
) -> list[WinnerResponse]:
    """Assign prizes to tickets at the end of a raffle.

    Only requests from configured **manager** ip addresses will succeed.
    """
    raffle = db.queries.fetch_raffle(conn, raffle_id=raffle_id)

    if raffle is None:
        raise HTTPException(404, "Raffle not found")

    if raffle.available_tickets:
        raise HTTPException(400, "Tickets remaining")

    if raffle.winners_drawn:
        raise HTTPException(400, "Winners already drawn")

    prizes = [
        prize
        for template in db.queries.list_prizes(conn, raffle_id=raffle_id)
        for prize in [template] * template.amount
    ]

    # Using random.sample not random.choices because a single ticket may not win
    # multiple prizes
    winning_numbers = random.sample(range(1, raffle.total_tickets + 1), k=len(prizes))

    with conn.transaction():
        db.queries.close_raffle(conn, raffle_id=raffle_id)
        db.queries.assign_winners(
            conn,
            [
                {
                    "raffle_id": raffle_id,
                    "ticket_number": ticket_number,
                    "prize_id": prize.prize_id,
                }
                for prize, ticket_number in zip(prizes, winning_numbers)
            ],
        )

    return [
        WinnerResponse(
            ticket_number=ticket_number,
            prize=prize.name,
        )
        for prize, ticket_number in zip(prizes, winning_numbers)
    ]


class VerifyTicketRequest(pydantic.BaseModel):
    ticket_number: pydantic.PositiveInt = pydantic.Field(..., example=5)
    verification_code: str = pydantic.Field(..., example="LDSFIUEN")


class VerifyTicketResponse(pydantic.BaseModel):
    has_won: bool = pydantic.Field(..., example=True)
    prize: str | None = pydantic.Field(..., example="Prize Name")


@app.post(
    "/raffles/{raffle_id}/verify-ticket/",
    response_model=VerifyTicketResponse,
    responses={
        200: {
            "content": {
                "application/json": {
                    "examples": {
                        "has_won": {
                            "summary": "Has won",
                            "value": {"has_won": True, "prize": "Prize Name"},
                        },
                        "has_not_won": {
                            "summary": "Has not won",
                            "value": {"has_won": False, "prize": None},
                        },
                    }
                }
            }
        },
        400: {
            "content": {
                "application/json": {
                    "examples": {
                        "winners_not_drawn": {
                            "summary": "Winners not drawn",
                            "value": {"detail": "Winners not drawn"},
                        },
                        "invalid_verification_code": {
                            "summary": "Invalid verification code",
                            "value": {"detail": "Invalid verification code"},
                        },
                    }
                }
            }
        },
        404: {
            "content": {
                "application/json": {
                    "examples": {
                        "raffle_not_found": {
                            "summary": "Raffle not found",
                            "value": {"detail": "Raffle not found"},
                        },
                        "ticket_not_found": {
                            "summary": "Ticket not found",
                            "value": {"detail": "Ticket not found"},
                        },
                    }
                }
            }
        },
    },
)
def verify_ticket(
    raffle_id: pydantic.UUID4,
    request: VerifyTicketRequest,
    conn: psycopg.Connection = Depends(deps.get_conn),
) -> VerifyTicketResponse:
    """Confirm the winning status of the player's ticket.

    This endpoint will allow a player to check the status of their ticket for a
    given raffle and confirm whether they have won a prize.

    Request are rejected if the raffle winners have not yet been drawn by a
    **manager** or if the given `verification_code` is not accepted.
    """
    raffle = db.queries.fetch_raffle(conn, raffle_id=raffle_id)

    if raffle is None:
        raise HTTPException(404, "Raffle not found")

    if not raffle.winners_drawn:
        raise HTTPException(400, "Winners not drawn")

    ticket = db.queries.fetch_ticket_with_validity(
        conn,
        raffle_id=raffle_id,
        ticket_number=request.ticket_number,
        verification_code=request.verification_code,
    )

    if ticket is None:
        raise HTTPException(404, "Ticket not found")

    if not ticket.is_valid:
        raise HTTPException(400, "Invalid verification code")

    ticket = db.queries.fetch_prize(
        conn,
        raffle_id=raffle_id,
        ticket_number=request.ticket_number,
    )

    return VerifyTicketResponse(has_won=bool(ticket.prize), prize=ticket.prize)
