import { useState } from 'react';
import { supabase } from '../services/supabase';
import { LogIn } from 'lucide-react';

export function AuthPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      if (isSignUp) {
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        setMessage('Check your email for the confirmation link!');
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    const { error } = await supabase.auth.signInWithOAuth({ provider: 'google' });
    if (error) setError(error.message);
    setLoading(false);
  };

  const handleResetPassword = async () => {
    if (!email) {
      setError("Please enter your email first to reset password.");
      return;
    }
    setLoading(true);
    const { error } = await supabase.auth.resetPasswordForEmail(email);
    if (error) {
      setError(error.message);
    } else {
      setMessage("Password reset email sent!");
    }
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', padding: '20px' }}>
      <div style={{ width: '100%', maxWidth: '420px', background: '#ffffff', padding: '40px', borderRadius: '12px', border: '1px solid #e1ded7', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}>
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <LogIn size={40} color="#265c55" style={{ marginBottom: '10px' }} />
          <h1 style={{ margin: 0, fontSize: '24px', color: '#1d252c' }}>Welcome to Friday</h1>
          <p style={{ margin: '8px 0 0 0', color: '#7a7468', fontSize: '14px' }}>Sign in or create an account</p>
        </div>
        
        {message && <div style={{ background: '#e6f4ea', color: '#1e4b35', padding: '10px', borderRadius: '6px', marginBottom: '15px', fontSize: '14px' }}>{message}</div>}
        {error && <div style={{ background: '#fce8e8', color: '#a83232', padding: '10px', borderRadius: '6px', marginBottom: '15px', fontSize: '14px' }}>{error}</div>}

        <form onSubmit={handleEmailAuth} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', color: '#4a5660' }}>Email</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #d4cec3' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', color: '#4a5660' }}>Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #d4cec3' }}
            />
          </div>
          
          <button type="submit" disabled={loading} style={{ background: '#265c55', color: '#fff', padding: '12px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}>
            {loading ? 'Processing...' : isSignUp ? 'Sign Up' : 'Sign In'}
          </button>
        </form>

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '15px', fontSize: '13px' }}>
          <button onClick={() => setIsSignUp(!isSignUp)} style={{ background: 'none', border: 'none', color: '#265c55', cursor: 'pointer', padding: 0 }}>
            {isSignUp ? 'Already have an account? Sign In' : 'Need an account? Sign Up'}
          </button>
          {!isSignUp && (
            <button onClick={handleResetPassword} style={{ background: 'none', border: 'none', color: '#7a7468', cursor: 'pointer', padding: 0 }}>
              Forgot Password?
            </button>
          )}
        </div>

        <div style={{ margin: '25px 0', borderBottom: '1px solid #e1ded7', position: 'relative', textAlign: 'center' }}>
          <span style={{ background: '#fff', padding: '0 10px', position: 'relative', top: '10px', color: '#7a7468', fontSize: '14px' }}>OR</span>
        </div>

        <button 
          onClick={handleGoogleLogin} 
          disabled={loading}
          style={{ width: '100%', background: '#fff', color: '#1d252c', padding: '12px', borderRadius: '6px', border: '1px solid #d4cec3', cursor: 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '10px', fontWeight: 'bold' }}
        >
          <img src="https://www.google.com/favicon.ico" alt="Google" width="16" height="16" />
          Continue with Google
        </button>
      </div>
    </div>
  );
}
