-- name: list_prizes
select
  prize_id,
  raffle_id,
  name,
  amount
from
  prizes
where
  raffle_id = :raffle_id;

-- name: close_raffle!
update
  raffles
set
  winners_drawn = true
where
  raffle_id = :raffle_id;

-- name: assign_winners*!
insert into winners (raffle_id, ticket_number, prize_id)
  values (:raffle_id, :ticket_number, :prize_id);
