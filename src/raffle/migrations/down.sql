-- name: delete_schema#
drop table if exists winners cascade;

drop table if exists participants cascade;

drop table if exists tickets cascade;

drop table if exists prizes cascade;

drop table if exists raffles cascade;

drop extension if exists pgcrypto;
