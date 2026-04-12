# Supabase Setup

1. In the Supabase dashboard, create a new project.
2. Enable Email OTP or Magic Link in Authentication.
3. Create a public storage bucket named `memory-photos`.
4. Run the SQL in `migrations/001_init.sql`.
5. Copy project URL and anon key into `.env`.

Recommended bucket rule direction:

- upload path prefix: `couple_space_id/...`
- only authenticated members of the same `couple_space` can read
