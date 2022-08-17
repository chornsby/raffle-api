-- name: create_schema#
create extension pgcrypto;

create table raffles (
  raffle_id uuid not null default gen_random_uuid () primary key,
  created_at timestamp not null default now(),
  name varchar(100) not null,
  total_tickets integer not null,
  available_tickets integer not null,
  winners_drawn bool not null default false,
  check (0 < total_tickets),
  check (0 <= available_tickets and available_tickets <= total_tickets)
);

create table prizes (
  prize_id serial primary key,
  raffle_id uuid not null references raffles on delete cascade,
  name varchar(100) not null,
  amount integer not null,
  check (0 < amount)
);

create table tickets (
  raffle_id uuid not null references raffles on delete cascade,
  ticket_number integer not null,
  ticket_order float not null default random(),
  check (0 < ticket_number),
  primary key (raffle_id, ticket_number)
);

create table participants (
  raffle_id uuid not null references raffles on delete restrict,
  ticket_number integer not null,
  ip_address inet not null,
  verification_code varchar(128) not null,
  foreign key (raffle_id, ticket_number) references tickets,
  primary key (raffle_id, ticket_number),
  unique (raffle_id, ip_address)
);

create table winners (
  raffle_id uuid not null references raffles on delete restrict,
  ticket_number integer not null,
  prize_id integer not null references prizes,
  foreign key (raffle_id, ticket_number) references participants,
  foreign key (raffle_id, ticket_number) references tickets,
  primary key (raffle_id, ticket_number)
);
