# Couple Memory App

An Expo + TypeScript + Supabase MVP for a private couple memory app. One `couple_space` is limited to exactly two members.

## Current MVP scope

- Login
- Invite binding
- New memory
- Map
- Memory detail
- Memory field editing

Each memory contains:

- `title`
- `date`
- `place_name`
- `lat`
- `lng`
- `note`
- `photos`
- `author_id`
- `couple_space_id`

## Project structure

```text
app/
  (auth)/
  (tabs)/
  memory/
src/
  components/
  constants/
  hooks/
  lib/
  services/
  store/
  types/
  utils/
supabase/
  migrations/
  seed.sql
docs/
  mvp-plan.md
```

## Tech plan

- `Expo SDK 54`
- `TypeScript`
- `expo-router`
- `@supabase/supabase-js`
- `@tanstack/react-query`
- `react-native-maps`

Web keeps the current lightweight map panel so the MVP can compile and run easily. Android and iOS still use the native map component.

## Environment variables

Copy `.env.example` to `.env` and fill in:

```bash
EXPO_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
EXPO_PUBLIC_SUPABASE_MEMORY_BUCKET=memory-photos
EXPO_PUBLIC_MAP_INITIAL_LAT=31.2304
EXPO_PUBLIC_MAP_INITIAL_LNG=121.4737
```

Meaning:

- `EXPO_PUBLIC_SUPABASE_URL`: Supabase project URL
- `EXPO_PUBLIC_SUPABASE_ANON_KEY`: Supabase anon key
- `EXPO_PUBLIC_SUPABASE_MEMORY_BUCKET`: private image bucket name
- `EXPO_PUBLIC_MAP_INITIAL_LAT`: fallback latitude when there are no memories
- `EXPO_PUBLIC_MAP_INITIAL_LNG`: fallback longitude when there are no memories

Environment variables do not change for the private Storage upgrade.

## How to start

```bash
npm install
npm run web
```

You can also run:

```bash
npm run android
npm run ios
```

## How to connect Supabase

1. Create a Supabase project.
2. Enable Email OTP or Magic Link in Authentication.
3. Run [001_init.sql](C:/Users/arcfever/Documents/New%20project/couple-memory-app/supabase/migrations/001_init.sql).
4. Run [002_storage_private_memory_photos.sql](C:/Users/arcfever/Documents/New%20project/couple-memory-app/supabase/migrations/002_storage_private_memory_photos.sql).
5. Fill `.env` with your project URL and anon key.
6. Restart Expo.

## Storage design

- Bucket name: `memory-photos`
- Bucket visibility: private, not public
- Object path format: `couple_space_id/memory_id/filename`
- Frontend stores object paths in `memories.photos`
- Frontend reads photos through signed URLs, not public URLs

## SQL migrations

- [001_init.sql](C:/Users/arcfever/Documents/New%20project/couple-memory-app/supabase/migrations/001_init.sql)
  - core tables, functions, main RLS
- [002_storage_private_memory_photos.sql](C:/Users/arcfever/Documents/New%20project/couple-memory-app/supabase/migrations/002_storage_private_memory_photos.sql)
  - creates the private bucket
  - enforces storage path shape
  - adds `storage.objects` RLS for same-space members only
- [003_memory_photo_cleanup.sql](C:/Users/arcfever/Documents/New%20project/couple-memory-app/supabase/migrations/003_memory_photo_cleanup.sql)
  - adds `memory_photos`
  - backfills existing photo paths
  - adds DB-side helpers for photo replacement and memory deletion cleanup

## Frontend files changed for private photos

- [memories.ts](C:/Users/arcfever/Documents/New%20project/couple-memory-app/src/services/memories.ts)
  - upload stores Storage paths, not public URLs
  - delete and replace are now centralized here
- [storage.ts](C:/Users/arcfever/Documents/New%20project/couple-memory-app/src/services/storage.ts)
  - builds object paths, resolves signed URLs, and removes private files
- [new-memory.tsx](C:/Users/arcfever/Documents/New%20project/couple-memory-app/app/(tabs)/new-memory.tsx)
  - supports private-path preview resolution
- [[id].tsx](C:/Users/arcfever/Documents/New%20project/couple-memory-app/app/memory/[id].tsx)
  - resolves signed photo URLs
  - adds delete confirmation before removing a memory
- [edit.tsx](C:/Users/arcfever/Documents/New%20project/couple-memory-app/app/memory/[id]/edit.tsx)
  - edits `title`, `date`, `place_name`, `lat`, `lng`, `note`

## Verification steps for private Storage

### 1. I can upload and view my own photos

1. Log in with account A.
2. Create or join a `couple_space`.
3. Add a memory with one or more photos.
4. Open the memory detail page.
5. Confirm the images render.
6. In Supabase Storage, confirm objects are under `couple_space_id/memory_id/filename`.

### 2. My girlfriend can view photos in the same couple space

1. Log in with account B.
2. Join the same space using the invite code.
3. Open the same memory detail page.
4. Confirm signed URLs are generated and images render.

### 3. An account outside the space cannot read the images

1. Log in with account C that is not a member of the space.
2. Try to read the same object through Storage Explorer or by calling `createSignedUrl`.
3. Confirm access is denied because `storage.objects` RLS checks `couple_space_id` membership.

### 4. The bucket is not public

1. Open Supabase Storage settings.
2. Confirm `memory-photos` has `public = false`.
3. Confirm the frontend never uses `getPublicUrl`.

## Verification steps for delete and replace cleanup

### 1. Delete a memory and remove its private files

1. Create a memory with photos.
2. Open the memory detail page.
3. Tap `Delete this memory`.
4. Confirm the alert.
5. Confirm the memory disappears from the map and detail route.
6. Check `memory_photos` in Supabase and confirm rows for that memory are gone.
7. Check the `memory-photos` bucket and confirm the corresponding files were removed.

### 2. Replace photos without breaking DB references

There is no edit page yet, so use the replace flow through the service layer when adding the future edit UI.

1. Start with an existing memory that already has private photos.
2. Call `replaceMemoryPhotos(memoryId, sourceUris)` from the app flow that will own editing.
3. Confirm new files upload first under `couple_space_id/memory_id/filename`.
4. Confirm the database switches to the new `memory_photos` rows and new `memories.photos` values.
5. Confirm old files are then removed from Storage.

### 3. Permission check before delete or replace

1. Log in with a user outside the memory's `couple_space`.
2. Try to trigger delete or replace for the target memory.
3. Confirm the service rejects access before destructive work begins.

## Integration checklist

Use this checklist during final two-person testing:

1. Account A signs up and logs in.
2. Account A creates a couple space and copies the invite code.
3. Account B signs up, logs in, and joins with the invite code.
4. Account A creates a memory with photos.
5. Account A opens the detail page and confirms signed private photos load.
6. Account B opens the same memory and confirms the same private photos load.
7. Account A edits `title`, `date`, `place_name`, `lat`, `lng`, and `note`, then confirms the map and detail page refresh correctly.
8. Replace photo refs through the app flow when the edit-photo UI is connected, and confirm new files upload before old files are removed.
9. Delete a memory from the detail page, confirm the confirmation dialog appears, then confirm DB rows and private files are cleaned up.
10. Sign out and sign back in with both accounts, then confirm access still matches the same `couple_space`.
11. Attempt access from a third account outside the space and confirm private photo reads are denied.

## Android local build and install

For local Android device testing from this repo:

1. Install Android Studio and the Android SDK.
2. Enable USB debugging on your Android phone.
3. Connect the phone with USB and verify it appears in `adb devices`.
4. In this project run:

```bash
npm install
npx expo run:android
```

This will generate the native Android folder if needed, build a debug app, and install it on the connected device.

If you only want to test through Expo Go:

```bash
npm run android
```

For a shareable install build later, use EAS:

```bash
npx eas build -p android --profile preview
```

That part requires EAS project setup and is not required for local USB install testing.

## Validation run in this workspace

These local checks were run successfully after the private Storage change:

```bash
npm run typecheck
npx expo export --platform web
```

## Notes on scenario validation

I validated the code path and policies locally, but I could not execute the three-account Supabase scenario end-to-end from this workspace because no live Supabase project credentials or test accounts were provided here. Use the verification steps above against your real project to confirm the access rules.

## Known limitations

- The current delete and replace flow is not fully transactional across Postgres and Storage because Supabase Storage operations do not participate in the same database transaction.
- Delete currently removes DB references first through a DB function, then removes files from Storage. If Storage cleanup fails afterward, orphan files may remain in the private bucket.
- Replace currently uploads new files first, switches DB references in one DB function, then removes old files. If old file cleanup fails, the user still sees the new photos, but stale files may remain in Storage.
- The current app does not yet expose a photo-edit UI. The replacement logic is implemented in the service layer and is ready for the future edit flow.
- To harden this further, move delete/replace orchestration into an Edge Function or queue failed file removals into a cleanup table, then run a scheduled cleanup task to remove orphan files safely.

## Next steps

1. Add delete flow for old private images when a memory photo is removed.
2. Add edit-memory support while preserving the same private path strategy.
3. Add copy/share invite actions.
