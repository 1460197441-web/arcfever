create or replace function public.storage_memory_uuid_from_object_name(object_name text)
returns uuid
language plpgsql
stable
as $$
declare
  raw_memory_id text;
begin
  raw_memory_id := nullif(split_part(object_name, '/', 2), '');

  if raw_memory_id is null then
    return null;
  end if;

  return raw_memory_id::uuid;
exception
  when others then
    return null;
end;
$$;

create or replace function public.can_read_memory_photo(object_bucket_id text, object_name text)
returns boolean
language sql
stable
as $$
  select
    object_bucket_id = 'memory-photos'
    and public.storage_space_id_from_object_name(object_name) is not null
    and public.storage_memory_uuid_from_object_name(object_name) is not null
    and exists (
      select 1
      from public.memories memories
      where memories.id = public.storage_memory_uuid_from_object_name(object_name)
        and memories.couple_space_id = public.storage_space_id_from_object_name(object_name)
        and public.is_space_member(memories.couple_space_id)
    );
$$;

create or replace function public.can_manage_memory_photo(object_bucket_id text, object_name text)
returns boolean
language sql
stable
as $$
  select
    object_bucket_id = 'memory-photos'
    and public.storage_space_id_from_object_name(object_name) is not null
    and public.storage_memory_uuid_from_object_name(object_name) is not null
    and exists (
      select 1
      from public.memories memories
      where memories.id = public.storage_memory_uuid_from_object_name(object_name)
        and memories.couple_space_id = public.storage_space_id_from_object_name(object_name)
        and memories.author_id = auth.uid()
    );
$$;

create or replace function public.is_valid_memory_photo_path(
  p_memory_id uuid,
  p_couple_space_id uuid,
  p_storage_path text
)
returns boolean
language sql
stable
as $$
  select
    p_storage_path like (p_couple_space_id::text || '/' || p_memory_id::text || '/%')
    and exists (
      select 1
      from storage.objects objects
      where objects.bucket_id = 'memory-photos'
        and objects.name = p_storage_path
    );
$$;

drop policy if exists "memory_photos_select_member" on storage.objects;
create policy "memory_photos_select_member"
on storage.objects
for select
to authenticated
using (
  public.can_read_memory_photo(bucket_id, name)
);

drop policy if exists "memory_photos_insert_member" on storage.objects;
create policy "memory_photos_insert_member"
on storage.objects
for insert
to authenticated
with check (
  public.can_manage_memory_photo(bucket_id, name)
);

drop policy if exists "memory_photos_update_member" on storage.objects;
create policy "memory_photos_update_member"
on storage.objects
for update
to authenticated
using (
  public.can_manage_memory_photo(bucket_id, name)
)
with check (
  public.can_manage_memory_photo(bucket_id, name)
);

drop policy if exists "memory_photos_delete_member" on storage.objects;
create policy "memory_photos_delete_member"
on storage.objects
for delete
to authenticated
using (
  public.can_manage_memory_photo(bucket_id, name)
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

  if p_photo_paths is not null then
    foreach v_photo_path in array p_photo_paths
    loop
      if not public.is_valid_memory_photo_path(p_memory_id, v_memory.couple_space_id, v_photo_path) then
        raise exception 'Invalid private photo path';
      end if;
    end loop;
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
