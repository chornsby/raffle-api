# Raffle API

An example raffle API developed in Python using FastAPI.

## Background

For the purposes of this project, a
[raffle](https://en.wikipedia.org/wiki/Raffle) is a gambling game played where
individual players claim tickets in the hopes of winning a prize. Each ticket
has a unique number and verification code. Once every ticket has been claimed, a
manager may draw the winners and assign a winning ticket to each prize. Players
can check the winning ticket numbers and verify whether their ticket has won a
prize by providing their ticket number and verification code.

### Requirements

- Raffles have a set number of tickets and prizes specified at creation
- Only managers can create new raffles
- Ticket numbers are sequential starting from `1` to `N` where `N` is the total
  number of tickets
- But tickets must be given to players in a non-sequential order
- Each ticket has a randomly generated verification code used to validate the
  ownership of a ticket
- The verification code is the conceptual equivalent of a password and so must
  not be stored in plaintext
- Ticket numbers are unique within a given raffle
- Players are limited to participate once per raffle based on their ip address
- Managers may draw the winning tickets only when there are no tickets remaining
- Winning tickets are not predetermined
- Each ticket can only win a single prize
- Manager permissions are only granted to a configurable list of ip addresses
- The application should perform reasonably even with a large number of tickets,
  prizes, and players

## Development

To run the API you will need the following tools:

- [docker](https://docs.docker.com/engine/install/)
- [docker-compose](https://docs.docker.com/compose/install/)
- [python3.10](https://www.python.org/downloads/)
- [tox](https://tox.wiki/en/latest/install.html)

```shell
# Run linters
tox -e lint

# Set up development environment configuration in .env file
cp .env.example .env

# Run tests with coverage
docker-compose up -d postgres
tox

# Update dependency versions in the requirements lock files
tox -e deps-update

# Run the API in docker
docker-compose up api

# Or, alternately, run the API locally with autoreload
tox -e venv
.venv/bin/raffle-cli run --reload
```

You can access the automatically generated interactive API documentation at
http://localhost:8000/docs.

## Retrospective

### Challenges

The most interesting challenge was allowing for non-sequential drawing of
tickets for participants. I approached this by giving an impression of complete
randomness by sorting the available tickets by a random number assigned at
ticket creation. But, in the scenario where many requests to `/participate/` are
received in a short space of time, I wanted to reduce the likelihood that all of
them would try to claim the same ticket number. This lead to the current design
where we claim a random ticket from a pool of available tickets (that themselves
are ordered randomly) in order to reduce contention. I made the parameters here
configurable in `config.py` since appropriate values would be dependent on how
many API servers are running and expected traffic peaks.

### Technologies

I found it nice to work with `aiosql` and write SQL directly rather than an ORM
framework like `sqlalchemy` or the one in `Django` which are very commonly used.

One benefit was that I thought more about the structure of the database tables
and took full advantage of natural compound keys (such as a `ticket` being
uniquely identified by its `raffle_id` and `ticket_number`). Following the
Django model would have introduced many more synthetic `bigint` primary keys.

I did miss a structured system for applying and maintaining schema migrations,
so I built the absolute minimal possible version in `cli.py`.

As usual, `FastAPI` was a joy to work with and I only felt let down when I was
typing out the examples of all the error responses that the API could return.
This was a much more manual process than I would like and, if I continued to
work on the API, they would very easily fall out of sync with the code.

Once again, `pip-tools` was great to specify a list of direct dependencies and
keep these clearly separated from transitive dependencies in the compiled lock
files in the `requirements` directory.

## License

Distributed under the terms of the MIT license, `raffle-api` is free and open
source software.
