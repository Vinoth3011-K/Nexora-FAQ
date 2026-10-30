import React, { useState, useEffect } from 'react';
import { ChevronDown, Tag, MessageCircle, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function FAQItem({ 
  faq, 
  onAskInChat, 
  defaultExpanded = false,
  isHighlighted = false 
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded || isHighlighted);
  const navigate = useNavigate();

  // If item becomes highlighted, ensure it automatically expands
  useEffect(() => {
    if (isHighlighted) {
      setIsExpanded(true);
    }
  }, [isHighlighted]);

  const handleAskQuestion = (e) => {
    e.stopPropagation();
    if (onAskInChat) {
      onAskInChat(faq.question);
    } else {
      navigate('/');
    }
  };

  const itemId = `faq-content-${faq.id}`;
  const headerId = `faq-header-${faq.id}`;

  return (
    <article 
      id={`faq-${faq.id}`}
      data-faq-id={faq.id}
      className={`faq-accordion-item ${isExpanded ? 'is-expanded' : ''} ${isHighlighted ? 'is-highlighted' : ''}`}
    >
      <button
        type="button"
        id={headerId}
        className="faq-question-btn"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        aria-controls={itemId}
      >
        <div className="faq-question-left">
          <div className="faq-pills-row">
            <span className="faq-category-pill">
              <Tag className="pill-icon" aria-hidden="true" />
              {faq.category}
            </span>
            {isHighlighted && (
              <span className="faq-matched-badge">
                <CheckCircle2 className="pill-icon" aria-hidden="true" />
                Referenced Source
              </span>
            )}
          </div>
          <h3 className="faq-question-text">{faq.question}</h3>
        </div>

        <div className="faq-chevron-wrap" aria-hidden="true">
          <ChevronDown className="faq-chevron-icon" />
        </div>
      </button>

      {isExpanded && (
        <div id={itemId} role="region" aria-labelledby={headerId} className="faq-answer-panel">
          <div className="faq-answer-inner">
            <p className="faq-answer-text">{faq.answer}</p>
            
            <div className="faq-footer-action">
              <button
                type="button"
                className="faq-ask-chat-btn"
                onClick={handleAskQuestion}
                title="Send this exact question to the FAQ Chatbot"
              >
                <MessageCircle className="btn-icon" aria-hidden="true" />
                <span>Ask Chatbot about this</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </article>
  );
}
