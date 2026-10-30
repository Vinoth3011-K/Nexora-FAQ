const API_BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) || 'http://localhost:8000/api/v1';

export const AUTH_TOKEN_KEY = 'nexora_auth_token';
export const AUTH_REFRESH_KEY = 'nexora_refresh_token';
export const AUTH_USER_KEY = 'nexora_auth_user';

const pendingGets = new Map();

export function getAuthToken() {
  try {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token || token === 'null' || token === 'undefined' || !token.trim()) {
      return null;
    }
    return token.trim();
  } catch {
    return null;
  }
}

async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const isAuthEndpoint = endpoint.startsWith('/auth/login/') || endpoint.startsWith('/auth/register/');
  const token = isAuthEndpoint ? null : getAuthToken();

  const config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  };

  const isGet = !config.method || config.method.toUpperCase() === 'GET';
  const requestKey = isGet ? `${url}|${token || 'anon'}` : null;
  if (requestKey && pendingGets.has(requestKey)) {
    return pendingGets.get(requestKey);
  }

  const fetchPromise = (async () => {
    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        let message = `Request failed (${response.status})`;
        try {
          const body = await response.json();
          message = body.message || body.detail || (typeof body === 'string' ? body : JSON.stringify(body));
        } catch {
          // keep fallback status message
        }

        if (response.status === 401 && !isAuthEndpoint) {
          localStorage.removeItem(AUTH_TOKEN_KEY);
          localStorage.removeItem(AUTH_REFRESH_KEY);
          localStorage.removeItem(AUTH_USER_KEY);
          window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        }

        const err = new Error(message);
        err.status = response.status;
        throw err;
      }

      if (response.status === 204) return null;
      return await response.json();
    } catch (err) {
      console.error(`[API] ${endpoint} failed:`, err);
      throw err;
    }
  })();

  if (requestKey) {
    pendingGets.set(requestKey, fetchPromise);
    try {
      return await fetchPromise;
    } finally {
      pendingGets.delete(requestKey);
    }
  }

  return fetchPromise;
}

// Authentication
export async function loginUser(email, password) {
  return apiRequest('/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ email: email.trim(), password }),
  });
}

export async function registerUser(details) {
  return apiRequest('/auth/register/', {
    method: 'POST',
    body: JSON.stringify(details),
  });
}

export async function fetchCurrentUser() {
  return apiRequest('/auth/me/');
}

export async function logoutUser(refreshToken) {
  return apiRequest('/auth/logout/', {
    method: 'POST',
    body: JSON.stringify({ refresh: refreshToken }),
  });
}

export async function refreshAccessToken(refreshToken) {
  return apiRequest('/auth/token/refresh/', {
    method: 'POST',
    body: JSON.stringify({ refresh: refreshToken }),
  });
}

// System & Knowledge Base
export async function fetchHealth() {
  return apiRequest('/health/');
}

export async function fetchFAQs(category = 'All') {
  const params = new URLSearchParams();
  if (category && category !== 'All') {
    params.set('category', category);
  }
  params.set('page_size', '100');
  const data = await apiRequest(`/faqs/?${params.toString()}`);
  return data.results || data;
}

export async function fetchFAQById(id) {
  return apiRequest(`/faqs/${id}/`);
}

export async function fetchFAQCategories() {
  const data = await apiRequest('/faqs/categories/');
  return data.categories || [];
}

export async function searchFAQs(query, category = 'All') {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  if (category && category !== 'All') params.append('category', category);
  params.append('page_size', '100');

  const data = await apiRequest(`/faqs/search/?${params.toString()}`);
  return data.results || data;
}

// Chat & Conversation Management
export async function sendChatMessage(question, conversationId = null) {
  return apiRequest('/chat/', {
    method: 'POST',
    body: JSON.stringify({
      question: question.trim(),
      conversation_id: conversationId || null,
    }),
  });
}

export async function fetchConversations(sessionId = null) {
  if (!getAuthToken()) return [];

  const params = new URLSearchParams();
  if (sessionId) params.set('session_id', sessionId);
  params.set('page_size', '50');

  const data = await apiRequest(`/conversations/?${params.toString()}`);
  return data.results || data;
}

export async function fetchConversation(id) {
  if (!getAuthToken()) return null;
  return apiRequest(`/conversations/${id}/`);
}

export async function createConversation(title = 'New Conversation', sessionId = null) {
  return apiRequest('/conversations/', {
    method: 'POST',
    body: JSON.stringify({
      title,
      session_id: sessionId || '',
    }),
  });
}

export async function clearConversation(id) {
  return apiRequest(`/conversations/${id}/clear/`, {
    method: 'POST',
  });
}
