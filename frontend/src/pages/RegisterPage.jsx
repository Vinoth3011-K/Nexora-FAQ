import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Building2, LockKeyhole, Mail, UserRound } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm_password: '' });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const update = key => event => setForm(current => ({ ...current, [key]: event.target.value }));

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    if (form.password !== form.confirm_password) {
      setError('Passwords do not match.');
      return;
    }
    setSubmitting(true);
    try {
      await register({ ...form, name: form.name.trim(), email: form.email.trim() });
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message || 'Unable to create your account.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-screen">
      <section className="auth-card auth-card-register">
        <div className="auth-brand-icon"><Building2 size={25} /></div>
        <p className="auth-eyebrow">NEXORA TECHNOLOGIES</p>
        <h1>Create your account</h1>
        <p className="auth-subtitle">Register to access the company Knowledge Assistant.</p>
        <form onSubmit={handleSubmit} className="auth-form">
          <label>Full name</label>
          <div className="auth-input-wrap"><UserRound size={18} /><input value={form.name} onChange={update('name')} autoComplete="name" placeholder="Your full name" required /></div>
          <label>Email address</label>
          <div className="auth-input-wrap"><Mail size={18} /><input type="email" value={form.email} onChange={update('email')} autoComplete="email" placeholder="you@company.com" required /></div>
          <label>Password</label>
          <div className="auth-input-wrap"><LockKeyhole size={18} /><input type="password" value={form.password} onChange={update('password')} autoComplete="new-password" minLength={8} placeholder="At least 8 characters" required /></div>
          <label>Confirm password</label>
          <div className="auth-input-wrap"><LockKeyhole size={18} /><input type="password" value={form.confirm_password} onChange={update('confirm_password')} autoComplete="new-password" minLength={8} placeholder="Re-enter your password" required /></div>
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button className="auth-submit" type="submit" disabled={submitting}>{submitting ? 'Creating account…' : 'Create account'}</button>
        </form>
        <p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p>
      </section>
    </main>
  );
}
