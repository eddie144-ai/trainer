-- BidBeacon / ContractRadar — Supabase Postgres schema (maps 1:1 to radar/store.py)
create table if not exists tenders (
  dedupe_key     text primary key,
  ocid           text,
  title          text,
  description    text,
  status         text,
  buyer          text,
  cpv            text,
  cpv_desc       text,
  cpv_additional jsonb default '[]',
  category       text,
  suitability    text,
  value_amount   numeric,
  value_currency text,
  deadline       timestamptz,
  published      timestamptz,
  region         jsonb default '{}',
  source         text,
  url            text,
  first_seen     timestamptz default now(),
  last_seen      timestamptz default now()
);
create index if not exists idx_tenders_deadline on tenders(deadline);
create index if not exists idx_tenders_cpv on tenders(cpv);

-- paying members; a row is added by the Stripe Payment Link webhook, profile
-- filled by the signup form. status flips to 'canceled' on subscription end.
create table if not exists subscribers (
  id         uuid primary key default gen_random_uuid(),
  email      text unique not null,
  profile    jsonb not null default '{}',
  status     text not null default 'active',
  created_at timestamptz default now()
);
