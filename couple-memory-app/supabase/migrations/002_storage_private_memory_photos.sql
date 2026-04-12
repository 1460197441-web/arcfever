insert into storage.buckets (
  id,
  name,
  public,
  file_size_limit,
  allowed_mime_types
)
values (
  'memory-photos',
  'memory-photos',
  false,
  10485760,
  array['image/jpeg', 'image/png', 'image/webp', 'image/heic']
)
on conflict (id) do update
set
  public = false,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

create or replace function public.storage_space_id_from_object_name(object_name text)
returns uuid
language plpgsql
stable
as $$
declare
  raw_space_id text;
begin
  raw_space_id := nullif(split_part(object_name, '/', 1), '');

  if raw_space_id is null then
    return null;
  end if;

  return raw_space_id::uuid;
exception
  when others then
    return null;
end;
$$;

create or replace function public.storage_memory_id_from_object_name(object_name text)
returns text
language sql
stable
as $$
  select nullif(split_part(object_name, '/', 2), '');
$$;

create or replace function public.can_access_memory_photo(object_bucket_id text, object_name text)
returns boolean
language sql
stable
as $$
  select
    object_bucket_id = 'memory-photos'
    and public.storage_space_id_from_object_name(object_name) is not null
    and public.storage_memory_id_from_object_name(object_name) is not null
    and public.is_space_member(public.storage_space_id_from_object_name(object_name));
$$;

drop policy if exists "memory_photos_select_member" on storage.objects;
create policy "memory_photos_select_member"
on storage.objects
for select
to authenticated
using (
  public.can_access_memory_photo(bucket_id, name)
);

drop policy if exists "memory_photos_insert_member" on storage.objects;
create policy "memory_photos_insert_member"
on storage.objects
for insert
to authenticated
with check (
  public.can_access_memory_photo(bucket_id, name)
);

drop policy if exists "memory_photos_update_member" on storage.objects;
create policy "memory_photos_update_member"
on storage.objects
for update
to authenticated
using (
  public.can_access_memory_photo(bucket_id, name)
)
with check (
  public.can_access_memory_photo(bucket_id, name)
);

drop policy if exists "memory_photos_delete_member" on storage.objects;
create policy "memory_photos_delete_member"
on storage.objects
for delete
to authenticated
using (
  public.can_access_memory_photo(bucket_id, name)
);
