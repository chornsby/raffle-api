-- name: create_raffle<!
insert into raffles (name, total_tickets, available_tickets)
  values (:name, :total_tickets, :total_tickets)
returning
  raffle_id, name, total_tickets, available_tickets, winners_drawn;

-- name: create_tickets!
insert into tickets (raffle_id, ticket_number)
select
  :raffle_id,
  ticket_number
from
  generate_series(1, :total_tickets) as ticket_number;

-- name: create_prizes*!
insert into prizes (raffle_id, name, amount)
  values (:raffle_id, :name, :amount);
