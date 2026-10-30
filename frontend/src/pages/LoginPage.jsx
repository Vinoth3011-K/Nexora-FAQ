import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Building2, LockKeyhole, Mail } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(email.trim(), password);
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message || 'Unable to log in. Please check your credentials.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-screen">
      <section className="auth-card">
        <div className="auth-brand-icon"><Building2 size={25} /></div>
        <p className="auth-eyebrow">NEXORA TECHNOLOGIES</p>
        <h1>Welcome back</h1>
        <p className="auth-subtitle">Sign in to continue to your Knowledge Assistant.</p>
        <form onSubmit={handleSubmit} className="auth-form">
          <label>Email address</label>
          <div className="auth-input-wrap"><Mail size={18} /><input type="email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" placeholder="you@company.com" required /></div>
          <label>Password</label>
          <div className="auth-input-wrap"><LockKeyhole size={18} /><input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" placeholder="Enter your password" required /></div>
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button className="auth-submit" type="submit" disabled={submitting}>{submitting ? 'Signing in…' : 'Sign in'}</button>
        </form>
        <p className="auth-switch">New to Nexora? <Link to="/register">Create an account</Link></p>
      </section>
    </main>
  );
}
