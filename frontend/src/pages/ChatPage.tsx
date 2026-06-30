import { FormEvent, useEffect, useRef, useState, UIEvent } from "react";
import { getChatHistory, sendChatMessage, api } from "../services/api";
import { Link } from "react-router-dom";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const INITIAL_MESSAGE: Message = {
  role: "assistant",
  content: `Hello! I can manage your standard ToDo list OR your Spaced Repetition queue.

**To create a standard reminder (ToDo List):**
Use words like "remind me" or "schedule".
- "remind me to call John at 5pm"
- "remind me to join meet at 8 pm https://meet.google.com/..."

**To add a problem to Spaced Repetition (Scheduler):**
Use words like "loop" or "track".
- "loop this problem https://leetcode.com/problems/two-sum"
- "track this concept for spaced repetition"

**To update a task:**
- "postpone my call with John to tomorrow"`,
};

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const [telegramVerified, setTelegramVerified] = useState<boolean | null>(null);
  const [displayName, setDisplayName] = useState<string | null>(null);

  const windowRef = useRef<HTMLDivElement | null>(null);
  const prevScrollHeightRef = useRef<number>(0);

  // Load initial history
  useEffect(() => {
    async function init() {
      try {
        const data = await getChatHistory(20, 0);
        if (data.messages.length < 20) {
          setHasMore(false);
        }
        if (data.messages.length === 0) {
          setMessages([INITIAL_MESSAGE]);
        } else {
          setMessages(data.messages);
        }
        setOffset(20);
        
        // Auto scroll to bottom on initial load
        setTimeout(() => {
          if (windowRef.current) {
            windowRef.current.scrollTop = windowRef.current.scrollHeight;
          }
        }, 50);
      } catch (err) {
        console.error("Failed to load history", err);
      }
      
      try {
        const res = await api.get(`/v1/user/settings`);
        setTelegramVerified(res.data.telegram_is_verified);
        setDisplayName(res.data.display_name);
      } catch (err) {
        console.error("Failed to load settings", err);
      }
    }
    init();
  }, []);

  async function handleScroll(e: UIEvent<HTMLDivElement>) {
    const target = e.currentTarget;
    // If scrolled to top and we have more messages
    if (target.scrollTop === 0 && hasMore && !loadingHistory) {
      setLoadingHistory(true);
      prevScrollHeightRef.current = target.scrollHeight;
      
      try {
        const data = await getChatHistory(20, offset);
        if (data.messages.length < 20) {
          setHasMore(false);
        }
        setMessages(prev => [...data.messages, ...prev]);
        setOffset(prev => prev + 20);
        
        // Restore scroll position so it doesn't jump to top
        setTimeout(() => {
          if (windowRef.current) {
            windowRef.current.scrollTop = windowRef.current.scrollHeight - prevScrollHeightRef.current;
          }
        }, 0);
      } catch (err) {
        console.error("Failed to fetch older messages", err);
      } finally {
        setLoadingHistory(false);
      }
    }
  }

  // Scroll to bottom when sending a new message
  useEffect(() => {
    if (sending && windowRef.current) {
      windowRef.current.scrollTop = windowRef.current.scrollHeight;
    }
  }, [messages, sending]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || sending) return;

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");
    setSending(true);

    try {
      const response = await sendChatMessage(trimmed);
      setMessages((prev) => [...prev, { role: "assistant", content: response.message }]);
    } catch (error) {
      const detail =
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Something went wrong. Try again.";
      setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${detail}` }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="page">
      <header className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Chat</h2>
        {displayName && <div style={{ fontSize: "15px", color: "#4a5660", fontWeight: 500 }}>Hi, {displayName}!</div>}
      </header>
      
      {telegramVerified === false && (
        <div style={{ background: "#fff3e0", borderLeft: "4px solid #ef6c00", padding: "12px 16px", marginBottom: "16px", borderRadius: "0 8px 8px 0" }}>
          <p style={{ margin: 0, color: "#e65100", fontSize: "0.95em" }}>
            ⚠️ <strong>Missing Telegram ID:</strong> Please add and verify your Telegram ID in <Link to="/settings" style={{ color: "#d84315", textDecoration: "underline" }}>Settings</Link> to receive your task reminders.
          </p>
        </div>
      )}

      <section className="chat-window" ref={windowRef} onScroll={handleScroll}>
        {loadingHistory && <div className="muted" style={{ textAlign: 'center', padding: '10px' }}>Loading older messages...</div>}
        {messages.map((message, index) => (
          <div
            key={index}
            className={message.role === "user" ? "user-message" : "assistant-message"}
            style={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}
          >
            {message.content}
          </div>
        ))}
        {sending && <div className="assistant-message assistant-typing">Thinking...</div>}
      </section>
      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          placeholder="Type a reminder..."
          value={input}
          onChange={(event) => setInput(event.target.value)}
          disabled={sending}
        />
        <button type="submit" disabled={sending || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
