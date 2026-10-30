import React from 'react';
import { Package, Clock, Headphones, RefreshCw } from 'lucide-react';

const SUGGESTIONS = [
  {
    icon: Package,
    title: 'Products & Services',
    question: 'What products or services does the company offer?'
  },
  {
    icon: Clock,
    title: 'Business Hours',
    question: 'What are your business hours?'
  },
  {
    icon: Headphones,
    title: 'Customer Support',
    question: 'How can I contact customer support?'
  },
  {
    icon: RefreshCw,
    title: 'Refund Policy',
    question: 'What is your refund or cancellation policy?'
  }
];

export default function SuggestedQuestions({ onSelectQuestion, disabled = false }) {
  return (
    <div className="suggested-questions-grid" role="region" aria-label="Suggested FAQ questions">
      {SUGGESTIONS.map((item, idx) => {
        const IconComponent = item.icon;
        return (
          <button
            key={idx}
            type="button"
            className="suggestion-card"
            onClick={() => onSelectQuestion(item.question)}
            disabled={disabled}
          >
            <div className="suggestion-icon-wrap" aria-hidden="true">
              <IconComponent className="suggestion-icon" />
            </div>
            <div className="suggestion-text-wrap">
              <span className="suggestion-category">{item.title}</span>
              <span className="suggestion-question">{item.question}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
