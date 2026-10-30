const BASE_STORAGE_KEYS = {
  CONVERSATIONS: 'nexora_faq_conversations',
  ACTIVE_CONVERSATION_ID: 'nexora_faq_active_id'
};

function storageKey(name) {
  let accountKey = 'legacy';
  try {
    const user = JSON.parse(localStorage.getItem('nexora_auth_user') || 'null');
    if (user) {
      accountKey = String(user.id ?? user.email ?? 'user').replace(/[^a-zA-Z0-9_-]/g, '_');
    }
  } catch {
    // Fallback to legacy bucket
  }
  return `${BASE_STORAGE_KEYS[name]}_${accountKey}`;
}

const memoryFallback = {};

export function getStoredConversations() {
  try {
    const raw = localStorage.getItem(storageKey('CONVERSATIONS'));
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : null;
  } catch (err) {
    console.warn('[Storage] Failed to read conversations:', err);
    return memoryFallback[storageKey('CONVERSATIONS')] || null;
  }
}

export function saveStoredConversations(conversations) {
  try {
    memoryFallback[storageKey('CONVERSATIONS')] = conversations;
    localStorage.setItem(storageKey('CONVERSATIONS'), JSON.stringify(conversations));
    return true;
  } catch (err) {
    console.warn('[Storage] Failed to write conversations:', err);
    return false;
  }
}

export function getStoredActiveId() {
  try {
    const id = localStorage.getItem(storageKey('ACTIVE_CONVERSATION_ID'));
    return id || memoryFallback[storageKey('ACTIVE_CONVERSATION_ID')] || null;
  } catch (err) {
    console.warn('[Storage] Failed to read active ID:', err);
    return memoryFallback[storageKey('ACTIVE_CONVERSATION_ID')] || null;
  }
}

export function saveStoredActiveId(id) {
  try {
    memoryFallback[storageKey('ACTIVE_CONVERSATION_ID')] = id;
    if (id) {
      localStorage.setItem(storageKey('ACTIVE_CONVERSATION_ID'), id);
    } else {
      localStorage.removeItem(storageKey('ACTIVE_CONVERSATION_ID'));
    }
    return true;
  } catch (err) {
    console.warn('[Storage] Failed to write active ID:', err);
    return false;
  }
}

export function createNewConversation(customTitle = 'New Conversation') {
  const timestamp = new Date().toISOString();
  return {
    id: `conv_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`,
    title: customTitle,
    createdAt: timestamp,
    updatedAt: timestamp,
    messages: []
  };
}
