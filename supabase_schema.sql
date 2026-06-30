-- Enable crypto extension for UUIDs
create extension if not exists pgcrypto;

-- ENUMS
create type chat_message_role as enum ('user', 'assistant', 'system');
create type task_status as enum ('open', 'completed', 'forgotten');
create type task_item_type as enum ('task', 'problem');
create type agent_run_status as enum ('success', 'needs_follow_up', 'failed');
create type reminder_delivery_status as enum ('sent', 'failed', 'skipped');

-- Updated At Trigger Function
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;


-- TABLES
create table chat_messages (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  role chat_message_role not null,
  content text not null,
  created_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb
);

create table agent_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  chat_message_id uuid references chat_messages(id) on delete set null,
  agent_name text not null,
  llm_provider text not null,
  llm_model text not null,
  status agent_run_status not null,
  input jsonb not null default '{}'::jsonb,
  output jsonb not null default '{}'::jsonb,
  error text,
  created_at timestamptz not null default now()
);

create table tasks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  source_chat_message_id uuid references chat_messages(id) on delete set null,
  agent_run_id uuid references agent_runs(id) on delete set null,
  title text not null,
  notes text,
  item_type task_item_type not null default 'task',
  status task_status not null default 'open',
  todo_at timestamptz not null,
  reminder_start_at timestamptz not null,
  next_revision_at timestamptz,
  timezone text not null default 'Asia/Kolkata',
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb,
  constraint tasks_title_not_blank check (length(trim(title)) > 0),
  constraint tasks_completed_at_matches_status check (
    (status = 'completed' and completed_at is not null)
    or
    (status != 'completed' and completed_at is null)
  )
);

create trigger tasks_set_updated_at
before update on tasks
for each row
execute function set_updated_at();

create table reminder_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  task_id uuid not null references tasks(id) on delete cascade,
  scheduled_for timestamptz not null,
  sent_at timestamptz,
  channel text not null default 'telegram',
  status reminder_delivery_status not null,
  message text,
  error text,
  created_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb
);

create table user_settings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade unique,
  display_name text,
  daily_quota integer not null default 5,
  queue_start_date date not null default current_date,
  telegram_chat_id text,
  telegram_is_verified boolean not null default false,
  telegram_otp text,
  telegram_otp_expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger user_settings_set_updated_at
before update on user_settings
for each row
execute function set_updated_at();

-- INDEXES
create unique index reminder_events_task_scheduled_channel_idx on reminder_events (task_id, scheduled_for, channel);
create index chat_messages_created_at_idx on chat_messages (created_at desc);
create index agent_runs_chat_message_id_idx on agent_runs (chat_message_id);
create index tasks_status_todo_at_idx on tasks (status, todo_at);
create index tasks_reminder_start_at_idx on tasks (reminder_start_at);
create index tasks_created_at_idx on tasks (created_at desc);
create index reminder_events_scheduled_for_idx on reminder_events (scheduled_for);
create index reminder_events_task_id_idx on reminder_events (task_id);


-- ROW LEVEL SECURITY (RLS)
alter table chat_messages enable row level security;
alter table agent_runs enable row level security;
alter table tasks enable row level security;
alter table reminder_events enable row level security;
alter table user_settings enable row level security;

-- Chat Messages Policies
create policy "Users can view their own chat messages" on chat_messages for select using (auth.uid() = user_id);
create policy "Users can insert their own chat messages" on chat_messages for insert with check (auth.uid() = user_id);
create policy "Users can update their own chat messages" on chat_messages for update using (auth.uid() = user_id);
create policy "Users can delete their own chat messages" on chat_messages for delete using (auth.uid() = user_id);

-- Tasks Policies
create policy "Users can view their own tasks" on tasks for select using (auth.uid() = user_id);
create policy "Users can insert their own tasks" on tasks for insert with check (auth.uid() = user_id);
create policy "Users can update their own tasks" on tasks for update using (auth.uid() = user_id);
create policy "Users can delete their own tasks" on tasks for delete using (auth.uid() = user_id);

-- Agent Runs Policies
create policy "Users can view their own agent runs" on agent_runs for select using (auth.uid() = user_id);
create policy "Users can insert their own agent runs" on agent_runs for insert with check (auth.uid() = user_id);
create policy "Users can update their own agent runs" on agent_runs for update using (auth.uid() = user_id);
create policy "Users can delete their own agent runs" on agent_runs for delete using (auth.uid() = user_id);

-- Reminder Events Policies
create policy "Users can view their own reminder events" on reminder_events for select using (auth.uid() = user_id);
create policy "Users can insert their own reminder events" on reminder_events for insert with check (auth.uid() = user_id);
create policy "Users can update their own reminder events" on reminder_events for update using (auth.uid() = user_id);
create policy "Users can delete their own reminder events" on reminder_events for delete using (auth.uid() = user_id);

-- User Settings Policies
create policy "Users can view their own settings" on user_settings for select using (auth.uid() = user_id);
create policy "Users can insert their own settings" on user_settings for insert with check (auth.uid() = user_id);
create policy "Users can update their own settings" on user_settings for update using (auth.uid() = user_id);
create policy "Users can delete their own settings" on user_settings for delete using (auth.uid() = user_id);
