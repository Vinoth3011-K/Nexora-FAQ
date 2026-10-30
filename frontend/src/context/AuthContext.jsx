import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  AUTH_REFRESH_KEY,
  AUTH_TOKEN_KEY,
  AUTH_USER_KEY,
  fetchCurrentUser,
  loginUser,
  logoutUser,
  registerUser,
  getAuthToken,
} from '../services/api';

const AuthContext = createContext(null);

function readSavedUser() {
  try {
    return JSON.parse(localStorage.getItem(AUTH_USER_KEY) || 'null');
  } catch {
    return null;
  }
}

function persistSession(payload) {
  const access = payload?.tokens?.access;
  const refresh = payload?.tokens?.refresh;
  const user = payload?.user;
  if (!access || !user) {
    throw new Error('The server did not return a valid login session.');
  }
  localStorage.setItem(AUTH_TOKEN_KEY, access);
  if (refresh) {
    localStorage.setItem(AUTH_REFRESH_KEY, refresh);
  }
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  return user;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readSavedUser);
  const [isLoading, setIsLoading] = useState(true);

  const clearSession = useCallback(() => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_REFRESH_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
    setUser(null);
  }, []);

  useEffect(() => {
    let active = true;
    const token = getAuthToken();

    if (!token) {
      clearSession();
      setIsLoading(false);
      return () => {
        active = false;
      };
    }

    fetchCurrentUser()
      .then((data) => {
        if (!active) return;
        const current = data?.user || data;
        localStorage.setItem(AUTH_USER_KEY, JSON.stringify(current));
        setUser(current);
      })
      .catch((err) => {
        if (active) {
          console.warn('[Auth] Session validation failed:', err?.message || err);
          clearSession();
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [clearSession]);

  useEffect(() => {
    const onUnauthorized = () => {
      clearSession();
    };
    window.addEventListener('auth:unauthorized', onUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', onUnauthorized);
  }, [clearSession]);

  const login = useCallback(async (email, password) => {
    const payload = await loginUser(email, password);
    const current = persistSession(payload);
    setUser(current);
    return current;
  }, []);

  const register = useCallback(async (details) => {
    const payload = await registerUser(details);
    const current = persistSession(payload);
    setUser(current);
    return current;
  }, []);

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem(AUTH_REFRESH_KEY);
    try {
      if (refresh) {
        await logoutUser(refresh);
      }
    } catch (err) {
      console.warn('[Auth] Logout notification to server failed:', err);
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const value = useMemo(() => ({
    user,
    isLoading,
    isAuthenticated: Boolean(user && getAuthToken()),
    login,
    register,
    logout,
  }), [user, isLoading, login, register, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider.');
  }
  return context;
}
