# Couple Memory MVP

## Project Structure

```text
couple-memory-app/
  app/
    (auth)/
      login.tsx
      invite.tsx
    (tabs)/
      _layout.tsx
      map.tsx
      new-memory.tsx
    memory/
      [id].tsx
    _layout.tsx
    index.tsx
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
  .env.example
  README.md
```

## Tech Stack

- Expo SDK 54
- TypeScript
- Expo Router
- Supabase Auth, Database, Storage
- React Query
- react-native-maps

## MVP Pages

- Login
- Invite binding
- New memory
- Map
- Memory detail

## RLS Summary

- All tables enable RLS.
- Users can only access data from their own `couple_space`.
- `couple_members.user_id` is unique so one account belongs to only one couple space.
- Only the memory author can edit or delete their memory in the MVP.
