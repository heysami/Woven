-- Woven broker registry. Run once in the Supabase SQL editor.
-- No secrets stored: re-provision deletes+recreates the tunnel under the same
-- subdomain, so a DB leak can never expose tunnel credentials.

create table if not exists installs (
  install_id text primary key,           -- client-minted, ^[a-f0-9]{32}$
  tunnel_id  text not null,              -- Cloudflare tunnel UUID
  hostname   text not null,              -- <install_id>.getwoven.design
  created_at timestamptz not null default now(),
  last_seen  timestamptz not null default now()
);

-- reaper scans by last_seen
create index if not exists installs_last_seen_idx on installs (last_seen);
