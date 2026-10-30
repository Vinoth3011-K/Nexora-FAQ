import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Building2, 
  Plus, 
  MessageSquare, 
  HelpCircle, 
  Info, 
  Sliders, 
  X, 
  ChevronRight,
  LogOut
} from 'lucide-react';

export default function Sidebar({
  isOpen,
  onClose,
  conversations = [],
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onOpenSettings
}) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const displayName = user?.name || [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email || 'User';
  const initials = displayName.split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0].toUpperCase()).join('') || 'U';

  const handleLogout = async () => {
    try { await logout(); } catch (error) { console.warn('Logout request failed; local session was cleared.', error); }
    navigate('/login', { replace: true });
  };

  const handleConversationClick = (id) => {
    onSelectConversation(id);
    navigate('/');
    if (window.innerWidth <= 768) {
      onClose();
    }
  };

  const handleNewChatClick = () => {
    onNewChat();
    navigate('/');
    if (window.innerWidth <= 768) {
      onClose();
    }
  };

  const handleNavClick = () => {
    if (window.innerWidth <= 768) {
      onClose();
    }
  };

  return (
    <>
      {/* Mobile backdrop */}
      <div 
        className={`sidebar-backdrop ${isOpen ? 'is-visible' : ''}`} 
        onClick={onClose} 
        aria-hidden="true" 
      />

      <aside className={`app-sidebar ${isOpen ? 'is-open' : ''}`} aria-label="Application Sidebar">
        {/* Sidebar Header / Brand */}
        <div className="sidebar-brand-header">
          <div className="brand-logo-wrap" aria-hidden="true">
            <Building2 className="brand-icon" />
          </div>
          <div className="brand-info">
            <span className="brand-name">Nexora Technologies</span>
            <span className="brand-tagline">Knowledge Assistant</span>
          </div>
          <button 
            type="button" 
            className="sidebar-close-mobile-btn" 
            onClick={onClose}
            aria-label="Close sidebar menu"
          >
            <X className="close-icon" />
          </button>
        </div>

        {/* New Chat Action */}
        <div className="sidebar-action-wrap">
          <button
            type="button"
            className="new-chat-btn"
            onClick={handleNewChatClick}
            aria-label="Start a new chat conversation"
          >
            <Plus className="new-chat-icon" />
            <span>New Conversation</span>
          </button>
        </div>

        {/* Recent Conversations List */}
        <div className="sidebar-section conversations-section">
          <div className="section-header-title">
            <span>Recent Conversations</span>
            <span className="conv-count-badge">{conversations.length}</span>
          </div>

          <div className="conversations-scroll-list" role="list">
            {conversations.length === 0 ? (
              <div className="empty-conversations-state">
                <MessageSquare className="empty-icon" aria-hidden="true" />
                <p className="empty-title">No conversations yet</p>
                <p className="empty-hint">Start a chat or ask a question to see history here.</p>
              </div>
            ) : (
              conversations.map((conv) => {
                const isActive = conv.id === activeConversationId;
                const messageCount = conv.messages ? conv.messages.length : 0;
                return (
                  <button
                    key={conv.id}
                    type="button"
                    className={`conversation-item-btn ${isActive ? 'is-active' : ''}`}
                    onClick={() => handleConversationClick(conv.id)}
                    aria-current={isActive ? 'true' : 'false'}
                  >
                    <MessageSquare className="conv-icon" aria-hidden="true" />
                    <div className="conv-title-wrap">
                      <span className="conv-title" title={conv.title}>{conv.title}</span>
                      <span className="conv-meta">{messageCount} {messageCount === 1 ? 'msg' : 'msgs'}</span>
                    </div>
                    {isActive && <ChevronRight className="active-chevron" aria-hidden="true" />}
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Navigation Section */}
        <div className="sidebar-section nav-links-section">
          <div className="section-header-title">
            <span>Knowledge & Info</span>
          </div>

          <nav className="sidebar-nav" aria-label="Main navigation">
            <NavLink
              to="/"
              end
              className={({ isActive }) => `sidebar-nav-link ${isActive ? 'is-active' : ''}`}
              onClick={handleNavClick}
            >
              <MessageSquare className="nav-icon" aria-hidden="true" />
              <span>Chat Assistant</span>
            </NavLink>

            <NavLink
              to="/faq"
              className={({ isActive }) => `sidebar-nav-link ${isActive ? 'is-active' : ''}`}
              onClick={handleNavClick}
            >
              <HelpCircle className="nav-icon" aria-hidden="true" />
              <span>FAQ Knowledge Base</span>
            </NavLink>

            <NavLink
              to="/about"
              className={({ isActive }) => `sidebar-nav-link ${isActive ? 'is-active' : ''}`}
              onClick={handleNavClick}
            >
              <Info className="nav-icon" aria-hidden="true" />
              <span>About RAG Architecture</span>
            </NavLink>

            <button
              type="button"
              className="sidebar-nav-link settings-nav-btn"
              onClick={() => {
                onOpenSettings();
                handleNavClick();
              }}
            >
              <Sliders className="nav-icon" aria-hidden="true" />
              <span>System Settings</span>
            </button>
          </nav>
        </div>

        {/* User Profile / Status Footer */}
        <div className="sidebar-footer">
          <div className="user-profile-badge">
            <div className="user-avatar-circle" aria-hidden="true">
              <span>{initials}</span>
            </div>
            <div className="user-details">
              <span className="user-name">{displayName}</span>
              <span className="user-role">{user?.email || 'Signed in'}</span>
            </div>
            <button type="button" className="sidebar-logout-btn" onClick={handleLogout} title="Log out" aria-label="Log out">
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
