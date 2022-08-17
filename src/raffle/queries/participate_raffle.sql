-- name: has_ip_address_participated$
select
  exists (
    select
      true
    from
      participants
    where
      raffle_id = :raffle_id
      and ip_address = :ip_address);

-- name: fetch_ticket_pool
select
  ticket_number
from
  tickets
  left join participants using (raffle_id, ticket_number)
where
  raffle_id = :raffle_id
  and ip_address is null
order by
  ticket_order
limit :limit;

-- name: claim_ticket!
insert into participants (raffle_id, ticket_number, ip_address, verification_code)
  values (:raffle_id, :ticket_number, :ip_address, crypt(:verification_code, gen_salt(:crypt_algorithm)));

-- name: release_ticket!
update
  raffles
set
  available_tickets = available_tickets - 1
where
  raffle_id = :raffle_id;
