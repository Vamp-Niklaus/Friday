import { MessageSquare, CheckSquare, History, Calendar, Settings } from "lucide-react";
import { BrowserRouter, NavLink, Navigate, Route, Routes } from "react-router-dom";

import { ChatPage } from "./pages/ChatPage";
import { HistoryPage } from "./pages/HistoryPage";
import { TodosPage } from "./pages/TodosPage";
import { SchedulerPage } from "./pages/SchedulerPage";
import { SettingsPage } from "./pages/SettingsPage";
import { AuthPage } from "./pages/AuthPage";
import { supabase } from "./services/supabase";
import { useEffect, useState } from "react";
import { Session } from "@supabase/supabase-js";

const navItems = [
  { label: "Chat", to: "/chat", icon: MessageSquare },
  { label: "Todos", to: "/todos", icon: CheckSquare },
  { label: "Scheduler", to: "/scheduler", icon: Calendar },
  { label: "History", to: "/history", icon: History },
  { label: "Settings", to: "/settings", icon: Settings },
];

export default function App() {
  const [session, setSession] = useState<Session | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (!session) {
    return <AuthPage />;
  }

  return (
    <BrowserRouter>
      <main className="app-shell">
        <aside className="sidebar">
          <h1>Friday</h1>
          <nav>
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.label}
                  to={item.to}
                  className={({ isActive }) =>
                    isActive ? "nav-button nav-button-active" : "nav-button"
                  }
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
          
          <div style={{ marginTop: 'auto', paddingTop: '24px' }}>
             <button 
                onClick={() => supabase.auth.signOut()} 
                className="nav-button" 
                style={{ width: '100%' }}
              >
                Sign Out
             </button>
          </div>
        </aside>
        <section className="content">
          <Routes>
            <Route path="/" element={<Navigate to="/chat" replace />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/todos" element={<TodosPage />} />
            <Route path="/scheduler" element={<SchedulerPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </section>
      </main>
    </BrowserRouter>
  );
}
