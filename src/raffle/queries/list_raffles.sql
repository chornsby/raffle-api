-- name: list_raffles
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
      prizes.raffle_id = raffles.raffle_id) as prizes
order by
  created_at desc
limit :limit;
