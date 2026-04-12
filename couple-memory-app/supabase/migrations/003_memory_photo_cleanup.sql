create table if not exists public.memory_photos (
  id uuid primary key default gen_random_uuid(),
  memory_id uuid not null references public.memories (id) on delete cascade,
  couple_space_id uuid not null references public.couple_spaces (id) on delete cascade,
  storage_path text not null unique,
  sort_order integer not null default 0,
  created_at timestamptz not null default now(),
  unique (memory_id, sort_order)
);

create index if not exists idx_memory_photos_memory_id on public.memory_photos (memory_id, sort_order);
create index if not exists idx_memory_photos_space_id on public.memory_photos (couple_space_id);

insert into public.memory_photos (memory_id, couple_space_id, storage_path, sort_order)
select
  memories.id,
  memories.couple_space_id,
  photo_items.photo_path,
  (photo_items.ordinality - 1)::integer
from public.memories
cross join lateral unnest(memories.photos) with ordinality as photo_items(photo_path, ordinality)
on conflict (storage_path) do nothing;

alter table public.memory_photos enable row level security;

drop policy if exists "memory_photos_select_member" on public.memory_photos;
create policy "memory_photos_select_member"
on public.memory_photos
for select
using (public.is_space_member(couple_space_id));

drop policy if exists "memory_photos_insert_author" on public.memory_photos;
create policy "memory_photos_insert_author"
on public.memory_photos
for insert
with check (
  public.is_space_member(couple_space_id)
  and exists (
    select 1
    from public.memories memories
    where memories.id = memory_id
      and memories.author_id = auth.uid()
      and memories.couple_space_id = couple_space_id
  )
);

drop policy if exists "memory_photos_update_author" on public.memory_photos;
create policy "memory_photos_update_author"
on public.memory_photos
for update
using (
  exists (
    select 1
    from public.memories memories
    where memories.id = memory_id
      and memories.author_id = auth.uid()
      and memories.couple_space_id = couple_space_id
  )
)
with check (
  exists (
    select 1
    from public.memories memories
    where memories.id = memory_id
      and memories.author_id = auth.uid()
      and memories.couple_space_id = couple_space_id
  )
);

drop policy if exists "memory_photos_delete_author" on public.memory_photos;
create policy "memory_photos_delete_author"
on public.memory_photos
for delete
using (
  exists (
    select 1
    from public.memories memories
    where memories.id = memory_id
      and memories.author_id = auth.uid()
      and memories.couple_space_id = couple_space_id
  )
);

create or replace function public.replace_memory_photo_refs(
  p_memory_id uuid,
  p_photo_paths text[]
)
returns public.memories
language plpgsql
security definer
set search_path = public
as $$
declare
  v_memory public.memories%rowtype;
  v_photo_path text;
  v_index integer := 0;
begin
  if auth.uid() is null then
    raise exception 'Not authenticated';
  end if;

  select *
  into v_memory
  from public.memories memories
  where memories.id = p_memory_id
    and public.is_space_member(memories.couple_space_id);

  if not found then
    raise exception 'Memory not found or access denied';
  end if;

  if v_memory.author_id <> auth.uid() then
    raise exception 'Only the memory author can modify photos';
  end if;

  update public.memories memories
  set
    photos = coalesce(p_photo_paths, '{}'::text[]),
    updated_at = now()
  where memories.id = p_memory_id
  returning * into v_memory;

  delete from public.memory_photos memory_photos
  where memory_photos.memory_id = p_memory_id;

  if p_photo_paths is not null then
    foreach v_photo_path in array p_photo_paths
    loop
      insert into public.memory_photos (
        memory_id,
        couple_space_id,
        storage_path,
        sort_order
      )
      values (
        p_memory_id,
        v_memory.couple_space_id,
        v_photo_path,
        v_index
      );

      v_index := v_index + 1;
    end loop;
  end if;

  return v_memory;
end;
$$;

create or replace function public.delete_memory_with_photo_refs(
  p_memory_id uuid
)
returns text[]
language plpgsql
security definer
set search_path = public
as $$
declare
  v_memory public.memories%rowtype;
  v_photo_paths text[];
begin
  if auth.uid() is null then
    raise exception 'Not authenticated';
  end if;

  select *
  into v_memory
  from public.memories memories
  where memories.id = p_memory_id
    and public.is_space_member(memories.couple_space_id);

  if not found then
    raise exception 'Memory not found or access denied';
  end if;

  if v_memory.author_id <> auth.uid() then
    raise exception 'Only the memory author can delete this memory';
  end if;

  select coalesce(array_agg(memory_photos.storage_path order by memory_photos.sort_order), v_memory.photos, '{}'::text[])
  into v_photo_paths
  from public.memory_photos memory_photos
  where memory_photos.memory_id = p_memory_id;

  delete from public.memories memories
  where memories.id = p_memory_id;

  return coalesce(v_photo_paths, '{}'::text[]);
end;
$$;
