# Doraemon Backend

FastAPI backend for the Doraemon personal assistant.

## Install

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

## Telegram Setup

1. Open Telegram and message `@BotFather`.
2. Create a bot with `/newbot`.
3. Put the bot token in `TELEGRAM_BOT_TOKEN`.
4. Send one message to your new bot from your Telegram account.
5. Open this URL in a browser, replacing the token:

```text
https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates
```

6. Copy your chat `id` into `TELEGRAM_CHAT_ID`.

Test from the backend:

```bash
curl -X POST http://localhost:8000/api/v1/notifications/telegram/test \
  -H "Content-Type: application/json" \
  -d '{"message":"Doraemon Telegram test message."}'
```
