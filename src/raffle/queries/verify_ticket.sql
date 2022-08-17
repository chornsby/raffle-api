-- name: fetch_ticket_with_validity^
select
  raffle_id,
  ticket_number,
  verification_code = crypt(:verification_code, verification_code) as is_valid
from
  participants
where
  raffle_id = :raffle_id
  and ticket_number = :ticket_number;

-- name: fetch_prize^
select
  prizes.name as prize
from
  participants
  left join winners using (raffle_id, ticket_number)
  left join prizes using (prize_id)
where
  participants.raffle_id = :raffle_id
  and ticket_number = :ticket_number;
