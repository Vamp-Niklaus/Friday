# Supabase Setup

Run the SQL files in `migrations/` from the Supabase SQL editor, in filename order.

For Phase 2, run:

```text
supabase/migrations/001_initial_schema.sql
```

The backend should connect to Supabase with the service role key, because V1 has no login and all database writes happen through the FastAPI backend.
