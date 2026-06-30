import { useEffect, useState } from "react";
import { Check, Loader2, Send } from "lucide-react";
import { api } from "../services/api";

type UserSettings = {
  display_name: string | null;
  daily_quota: number;
  telegram_chat_id: string | null;
  telegram_is_verified: boolean;
};

export function SettingsPage() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Profile Form
  const [displayName, setDisplayName] = useState("");
  const [dailyQuota, setDailyQuota] = useState("5");
  const [savingProfile, setSavingProfile] = useState(false);

  // Telegram Verification Flow
  const [telegramIdInput, setTelegramIdInput] = useState("");
  const [otpInput, setOtpInput] = useState("");
  const [verifying, setVerifying] = useState(false);
  const [otpSent, setOtpSent] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    try {
      setLoading(true);
      const res = await api.get(`/v1/user/settings`);
      const data: UserSettings = res.data;
      setSettings(data);
      setDisplayName(data.display_name || "");
      setDailyQuota(data.daily_quota.toString());
      setTelegramIdInput(data.telegram_chat_id || "");
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveProfile() {
    try {
      setSavingProfile(true);
      setError(null);
      setSuccessMsg(null);
      const quota = parseInt(dailyQuota, 10) || 5;
      
      const res = await api.put(`/v1/user/settings/profile`, { display_name: displayName, daily_quota: quota });
      const data = res.data;
      setSettings(data);
      setSuccessMsg("Profile saved successfully.");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSavingProfile(false);
    }
  }

  async function handleSendOtp() {
    if (!telegramIdInput.trim()) {
      setError("Please enter a Telegram Chat ID first.");
      return;
    }
    
    try {
      setVerifying(true);
      setError(null);
      setSuccessMsg(null);
      
      const res = await api.post(`/v1/user/settings/telegram/verify_request`, { telegram_chat_id: telegramIdInput.trim() });
      const data = res.data;
      
      setOtpSent(true);
      setSuccessMsg("Verification code sent! Check your Telegram.");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setVerifying(false);
    }
  }

  async function handleVerifyOtp() {
    if (!otpInput.trim()) return;
    
    try {
      setVerifying(true);
      setError(null);
      setSuccessMsg(null);
      
      const res = await api.post(`/v1/user/settings/telegram/verify_confirm`, { otp: otpInput.trim() });
      const data = res.data;
      
      setSettings(data);
      setOtpSent(false);
      setOtpInput("");
      setSuccessMsg("Telegram verified successfully! You will now receive reminders.");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setVerifying(false);
    }
  }

  if (loading) return <div className="page"><p className="muted">Loading settings...</p></div>;

  return (
    <div className="page" style={{ maxWidth: "600px", margin: "0 auto" }}>
      <header className="page-header">
        <h2>Settings</h2>
      </header>

      {error && <div className="error" style={{ marginBottom: "16px" }}>{error}</div>}
      {successMsg && <div style={{ background: "#e8f5e9", color: "#2e7d32", padding: "12px", borderRadius: "8px", marginBottom: "16px" }}>{successMsg}</div>}

      <section className="task-group" style={{ marginBottom: "32px", padding: "20px", background: "#f8f9fa", borderRadius: "12px" }}>
        <h3>Profile</h3>
        
        <div style={{ marginTop: "16px" }}>
          <label style={{ display: "block", marginBottom: "8px", fontWeight: 500 }}>Display Name</label>
          <input 
            className="input-modern"
            type="text" 
            placeholder="How should I call you?"
            value={displayName}
            onChange={e => setDisplayName(e.target.value)}
          />
        </div>
        
        <div style={{ marginTop: "16px" }}>
          <label style={{ display: "block", marginBottom: "8px", fontWeight: 500 }}>Daily Problem Quota</label>
          <input 
            className="input-modern"
            type="number" 
            min="1"
            value={dailyQuota}
            onChange={e => setDailyQuota(e.target.value)}
          />
          <p className="muted" style={{ fontSize: "0.85em", marginTop: "4px" }}>Number of spaced repetition problems scheduled per day.</p>
        </div>

        <button 
          className="btn-modern" 
          style={{ marginTop: "16px", padding: "8px 16px" }}
          onClick={handleSaveProfile}
          disabled={savingProfile}
        >
          {savingProfile ? "Saving..." : "Save Profile"}
        </button>
      </section>

      <section className="task-group" style={{ padding: "20px", background: "#f8f9fa", borderRadius: "12px" }}>
        <h3 style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          Telegram Notifications
          {settings?.telegram_is_verified && <Check size={20} color="#2e7d32" />}
        </h3>
        <p className="muted" style={{ marginTop: "8px" }}>Connect your Telegram account to receive task reminders and scheduled problems directly on your phone.</p>

        {settings?.telegram_is_verified ? (
          <div style={{ marginTop: "16px", background: "#e8f5e9", padding: "16px", borderRadius: "8px", border: "1px solid #c8e6c9" }}>
            <p style={{ margin: 0, color: "#1b5e20", fontWeight: 500 }}>✓ Telegram Linked</p>
            <p style={{ margin: "4px 0 0 0", color: "#2e7d32", fontSize: "0.9em" }}>Connected to Chat ID: {settings.telegram_chat_id}</p>
          </div>
        ) : (
          <div style={{ marginTop: "24px" }}>
            <div style={{ background: "#fff3e0", padding: "16px", borderRadius: "8px", marginBottom: "16px", fontSize: "0.9em" }}>
              <strong>How to get your Telegram Chat ID:</strong>
              <ol style={{ margin: "8px 0 0 0", paddingLeft: "20px" }}>
                <li>Open Telegram and search for <strong>@userinfobot</strong></li>
                <li>Send the message <code>/start</code> to the bot</li>
                <li>The bot will reply with your numeric ID (e.g., <code>123456789</code>)</li>
                <li>Before requesting a code, make sure you have also sent a message to the actual Antigravity Reminder Bot so it has permission to message you!</li>
              </ol>
            </div>

            <label style={{ display: "block", marginBottom: "8px", fontWeight: 500 }}>Your Telegram Chat ID</label>
            <div style={{ display: "flex", gap: "8px" }}>
              <input 
                className="input-modern"
                type="text" 
                placeholder="e.g. 123456789"
                value={telegramIdInput}
                onChange={e => setTelegramIdInput(e.target.value)}
                disabled={otpSent}
              />
              {!otpSent && (
                <button 
                  className="btn-modern" 
                  onClick={handleSendOtp}
                  disabled={verifying || !telegramIdInput}
                  style={{ display: "flex", alignItems: "center", gap: "8px" }}
                >
                  {verifying ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
                  Send Code
                </button>
              )}
            </div>

            {otpSent && (
              <div style={{ marginTop: "16px", padding: "16px", background: "white", borderRadius: "8px", border: "1px solid #e0e0e0" }}>
                <label style={{ display: "block", marginBottom: "8px", fontWeight: 500 }}>Enter 6-Digit Verification Code</label>
                <div style={{ display: "flex", gap: "8px" }}>
                  <input 
                    className="input-modern"
                    type="text" 
                    placeholder="123456"
                    value={otpInput}
                    onChange={e => setOtpInput(e.target.value)}
                  />
                  <button 
                    className="btn-modern" 
                    onClick={handleVerifyOtp}
                    disabled={verifying || !otpInput}
                  >
                    {verifying ? "Verifying..." : "Verify"}
                  </button>
                </div>
                <button 
                  style={{ background: "none", border: "none", color: "#0288d1", textDecoration: "underline", marginTop: "12px", cursor: "pointer", fontSize: "0.9em" }}
                  onClick={() => { setOtpSent(false); setSuccessMsg(null); setError(null); }}
                >
                  Change Chat ID or Resend
                </button>
              </div>
            )}
          </div>
        )}
      </section>

      <footer style={{ marginTop: "32px", textAlign: "center", fontSize: "0.85em", color: "#7a7468" }}>
        Built by <a href="https://vamp-niklaus.github.io/portfolio/" target="_blank" rel="noopener noreferrer" style={{ color: "#265c55", textDecoration: "none", fontWeight: 500 }}>Vamp Niklaus</a>
      </footer>
    </div>
  );
}
