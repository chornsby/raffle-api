-- name: fetch_raffle^
select
  raffle_id,
  name,
  total_tickets,
  available_tickets,
  winners_drawn,
  prizes
from
  raffles,
  lateral (
    select
      jsonb_agg(jsonb_build_object('name', prizes.name, 'amount', prizes.amount)) as prizes
    from
      prizes
    where
      prizes.raffle_id = :raffle_id) as prizes
where
  raffle_id = :raffle_id;
