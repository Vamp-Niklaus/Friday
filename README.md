# Friday (The Ultimate AI Personal Assistant)

**Live App:** [https://friday-soul.onrender.com/chat](https://friday-soul.onrender.com/chat)

Friday is an intelligent, full-stack personal assistant designed to seamlessly manage tasks, reminders, and daily problem-solving queues. By combining a beautiful React frontend with a powerful AI-driven Python backend, Friday acts as a smart companion that understands natural language and proactively reaches out to you through Telegram when deadlines approach.

---

## 🌟 Key Features

- **Natural Language Task Management:** Simply tell Friday what you want to do (e.g., "Remind me to call Mom tomorrow at 5 PM"), and the AI will automatically parse the intent, date, and time to create a structured task.
- **Spaced Repetition & Problem Queue:** A dedicated problem-solving tracker built for continuous learning. Set daily quotas and let Friday enforce revision schedules.
- **Proactive Telegram Notifications:** Friday automatically pushes smart, grouped reminders to your Telegram app (Immediate, Past Due, and Today's Problems) so you never miss a beat.
- **Google Authentication:** Securely log in using Google OAuth, powered by Supabase.
- **Unified Monolith Architecture:** The entire app is elegantly served from a single FastAPI server, meaning no complex CORS issues and blazing-fast performance.

---

## 🛠 Tech Stack

- **Frontend:** React, Vite, Vanilla CSS (Mobile-first, responsive design with a sleek Bottom Navigation bar).
- **Backend:** FastAPI (Python), `httpx` (Async HTTP client).
- **AI Brain:** Google Gemini Flash (via OpenRouter/OpenAI-compatible APIs) for natural language understanding and task extraction.
- **Database:** Supabase (PostgreSQL) with Row-Level Security (RLS) and Singleton client patterns to prevent connection leaks.
- **Hosting:** Render.com (Hosting the React frontend statically directly through FastAPI).

---

## 📁 Project Structure

```text
Vamp-Niklaus/Friday/
│
├── frontend/                # React Vite Application
│   ├── src/                 
│   │   ├── components/      # Reusable UI components (Sidebar, Bottom Nav)
│   │   ├── pages/           # Application views (Chat, Todos, Scheduler, Settings)
│   │   └── services/        # API clients (Axios, Supabase auth)
│   └── vite.config.ts       # Vite configuration
│
├── backend/                 # FastAPI Python Application
│   ├── app/
│   │   ├── api/             # API routes (Chat, Todos, Cron, Problems)
│   │   ├── core/            # Configuration and environment variables
│   │   ├── database/        # Supabase repository pattern
│   │   ├── services/        # AI logic, Telegram integration, and Reminder cycles
│   │   └── main.py          # Application entrypoint & React static file server
│   └── requirements.txt     # Python dependencies
│
└── build.sh                 # Unified build script for Render.com
```

---

## 🚀 How It Works Under the Hood

### 1. The Monolith Architecture
Instead of hosting the frontend and backend on separate platforms, Friday uses a **Monolith Architecture**. When you visit the app, the FastAPI backend intercepts the request, serves the compiled React application from the `frontend/dist` folder, and handles all `/api/v1/...` requests natively. 

### 2. The AI Brain (`OmniAgent`)
When a user sends a chat message, the backend routes it to the `OmniAgent`. The agent uses the LLM to determine if the message is a general conversation, a task request, or a problem queue addition. It extracts timestamps and metadata and automatically interacts with the database repositories.

### 3. The Cron Job System
Friday's backend exposes a stateless `/api/v1/cron/reminders` endpoint that accepts `GET` and `HEAD` requests. An external cron service (like UptimeRobot) pings this endpoint every 5 minutes. The backend instantly returns a `200 OK` response while asynchronously running a background task that evaluates open tasks, groups them, and pushes them to Telegram if they are due.

---

## 💻 Running Locally

### Prerequisites
- Node.js & npm
- Python 3.10+
- A Supabase Project
- A Telegram Bot Token

### Steps
1. **Clone the repository:**
   ```bash
   git clone https://github.com/Vamp-Niklaus/Friday.git
   cd Friday
   ```

2. **Setup the Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Setup the Backend:**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the `backend/` directory with your API keys:
   ```env
   SUPABASE_URL=...
   SUPABASE_SERVICE_ROLE_KEY=...
   TELEGRAM_BOT_TOKEN=...
   OPENAI_API_KEY=...
   ```

5. **Start the Backend:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```