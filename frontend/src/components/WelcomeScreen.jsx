import React from 'react';
import { Sparkles, Bot, ShieldCheck } from 'lucide-react';
import SuggestedQuestions from './SuggestedQuestions';

export default function WelcomeScreen({ onSelectQuestion, disabled = false }) {
  return (
    <div className="welcome-screen">
      <div className="welcome-badge">
        <Sparkles className="badge-sparkle-icon" aria-hidden="true" />
        <span>RAG Knowledge Base Assistant</span>
      </div>

      <div className="welcome-avatar-wrapper" aria-hidden="true">
        <div className="welcome-avatar-glow"></div>
        <div className="welcome-avatar">
          <Bot className="welcome-bot-icon" />
        </div>
      </div>

      <h1 className="welcome-title">How can we help you today?</h1>

      <p className="welcome-description">
        Ask anything about our company policies, products, services, pricing plans, and 
        customer support. Responses are powered by our company FAQ knowledge base.
      </p>

      <div className="welcome-trust-row" aria-hidden="true">
        <span className="trust-item"><ShieldCheck className="trust-icon" /> Verified Company Knowledge</span>
        <span className="trust-divider">•</span>
        <span className="trust-item">Instant Answers</span>
        <span className="trust-divider">•</span>
        <span className="trust-item">15+ Categorized Topics</span>
      </div>

      <div className="welcome-suggestions-section">
        <h2 className="suggestions-label">Popular Frequently Asked Questions</h2>
        <SuggestedQuestions onSelectQuestion={onSelectQuestion} disabled={disabled} />
      </div>
    </div>
  );
}
