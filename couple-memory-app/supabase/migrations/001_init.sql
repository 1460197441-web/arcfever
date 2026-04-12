create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null unique,
  display_name text,
  avatar_url text,
  created_at timestamptz not null default now()
);

create table if not exists public.couple_spaces (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  owner_user_id uuid not null references auth.users (id) on delete cascade,
  invite_code text not null unique default upper(substring(md5(gen_random_uuid()::text), 1, 8)),
  max_members integer not null default 2 check (max_members = 2),
  created_at timestamptz not null default now()
);

create table if not exists public.couple_members (
  id uuid primary key default gen_random_uuid(),
  couple_space_id uuid not null references public.couple_spaces (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  role text not null check (role in ('owner', 'partner')),
  joined_at timestamptz not null default now(),
  unique (couple_space_id, user_id),
  unique (user_id)
);

create table if not exists public.memories (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  date date not null,
  place_name text not null,
  lat double precision not null,
  lng double precision not null,
  note text not null default '',
  photos text[] not null default '{}',
  author_id uuid not null references auth.users (id) on delete cascade,
  couple_space_id uuid not null references public.couple_spaces (id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_memories_space_date on public.memories (couple_space_id, date desc);
create index if not exists idx_memories_space_place on public.memories (couple_space_id, place_name);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_memories_updated_at on public.memories;
create trigger trg_memories_updated_at
before update on public.memories
for each row
execute procedure public.set_updated_at();

create or replace function public.is_space_member(target_space_id uuid)
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from public.couple_members cm
    where cm.couple_space_id = target_space_id
      and cm.user_id = auth.uid()
  );
$$;

create or replace function public.is_space_owner(target_space_id uuid)
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from public.couple_spaces cs
    where cs.id = target_space_id
      and cs.owner_user_id = auth.uid()
  );
$$;

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, email, display_name)
  values (new.id, coalesce(new.email, ''), new.raw_user_meta_data ->> 'display_name')
  on conflict (id) do update
  set email = excluded.email;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row
execute procedure public.handle_new_user();

create or replace function public.create_couple_space(p_name text)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_space_id uuid;
begin
  if auth.uid() is null then
    raise exception 'Not authenticated';
  end if;

  if exists (select 1 from public.couple_members where user_id = auth.uid()) then
    raise exception 'User already belongs to a couple space';
  end if;

  insert into public.couple_spaces (name, owner_user_id)
  values (p_name, auth.uid())
  returning id into v_space_id;

  insert into public.couple_members (couple_space_id, user_id, role)
  values (v_space_id, auth.uid(), 'owner');

  return v_space_id;
end;
$$;

create or replace function public.join_couple_space(p_invite_code text)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_space_id uuid;
  v_count integer;
begin
  if auth.uid() is null then
    raise exception 'Not authenticated';
  end if;

  if exists (select 1 from public.couple_members where user_id = auth.uid()) then
    raise exception 'User already belongs to a couple space';
  end if;

  select id into v_space_id
  from public.couple_spaces
  where invite_code = upper(trim(p_invite_code));

  if v_space_id is null then
    raise exception 'Invite code not found';
  end if;

  select count(*) into v_count
  from public.couple_members
  where couple_space_id = v_space_id;

  if v_count >= 2 then
    raise exception 'Couple space is already full';
  end if;

  insert into public.couple_members (couple_space_id, user_id, role)
  values (v_space_id, auth.uid(), 'partner');

  return v_space_id;
end;
$$;

alter table public.profiles enable row level security;
alter table public.couple_spaces enable row level security;
alter table public.couple_members enable row level security;
alter table public.memories enable row level security;

drop policy if exists "profiles_select_self" on public.profiles;
create policy "profiles_select_self" on public.profiles
for select using (auth.uid() = id);

drop policy if exists "profiles_insert_self" on public.profiles;
create policy "profiles_insert_self" on public.profiles
for insert with check (auth.uid() = id);

drop policy if exists "profiles_update_self" on public.profiles;
create policy "profiles_update_self" on public.profiles
for update using (auth.uid() = id) with check (auth.uid() = id);

drop policy if exists "spaces_select_member" on public.couple_spaces;
create policy "spaces_select_member" on public.couple_spaces
for select using (public.is_space_member(id));

drop policy if exists "spaces_insert_owner" on public.couple_spaces;
create policy "spaces_insert_owner" on public.couple_spaces
for insert with check (auth.uid() = owner_user_id);

drop policy if exists "spaces_update_owner" on public.couple_spaces;
create policy "spaces_update_owner" on public.couple_spaces
for update using (public.is_space_owner(id)) with check (public.is_space_owner(id));

drop policy if exists "members_select_same_space" on public.couple_members;
create policy "members_select_same_space" on public.couple_members
for select using (public.is_space_member(couple_space_id));

drop policy if exists "memories_select_member" on public.memories;
create policy "memories_select_member" on public.memories
for select using (public.is_space_member(couple_space_id));

drop policy if exists "memories_insert_member" on public.memories;
create policy "memories_insert_member" on public.memories
for insert with check (auth.uid() = author_id and public.is_space_member(couple_space_id));

drop policy if exists "memories_update_author" on public.memories;
create policy "memories_update_author" on public.memories
for update using (auth.uid() = author_id and public.is_space_member(couple_space_id))
with check (auth.uid() = author_id and public.is_space_member(couple_space_id));

drop policy if exists "memories_delete_author" on public.memories;
create policy "memories_delete_author" on public.memories
for delete using (auth.uid() = author_id and public.is_space_member(couple_space_id));
