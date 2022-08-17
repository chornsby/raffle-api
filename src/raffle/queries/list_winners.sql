-- name: list_winners
select
  ticket_number,
  prizes.name as prize
from
  winners
  join prizes using (raffle_id, prize_id)
where
  raffle_id = :raffle_id
order by
  ticket_number;
