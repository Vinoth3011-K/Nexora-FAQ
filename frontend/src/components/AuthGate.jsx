import React from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';

export default function AuthGate({ children }) {
  const { isLoading, isAuthenticated } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <main className="auth-loading-screen"><div className="auth-spinner" /><p>Checking your session…</p></main>;
  }

  if (isAuthenticated) {
    if (location.pathname === '/login' || location.pathname === '/register') {
      return <Navigate to="/" replace />;
    }
    return children;
  }

  return (
    <Routes>
      <Route path="/register" element={<RegisterPage />} />
      <Route path="*" element={<LoginPage />} />
    </Routes>
  );
}
