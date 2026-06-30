alter table user_settings add column display_name text;
alter table user_settings add column telegram_chat_id text;
alter table user_settings add column telegram_is_verified boolean not null default false;
alter table user_settings add column telegram_otp text;
alter table user_settings add column telegram_otp_expires_at timestamptz;
