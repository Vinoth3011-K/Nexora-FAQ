import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, User, CheckCircle2, AlertCircle, BookOpen, ExternalLink, RotateCcw } from 'lucide-react';

function renderInline(str) {
  if (!str) return null;

  const tokenRegex = /(`[^`]+`|\*\*[^*]+\*\*|__[^_]+__|\[[^\]]+\]\([^)]+\)|https?:\/\/[^\s<)]+|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g;
  const parts = str.split(tokenRegex);

  return parts.map((part, index) => {
    if (!part) return null;

    if (part.startsWith('`') && part.endsWith('`') && part.length >= 2) {
      return (
        <code key={index} className="message-inline-code">
          {part.slice(1, -1)}
        </code>
      );
    }

    if (
      (part.startsWith('**') && part.endsWith('**') && part.length >= 4) ||
      (part.startsWith('__') && part.endsWith('__') && part.length >= 4)
    ) {
      return (
        <strong key={index} className="message-bold">
          {part.slice(2, -2)}
        </strong>
      );
    }

    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      return (
        <a key={index} href={linkMatch[2]} target="_blank" rel="noopener noreferrer" className="message-link">
          {linkMatch[1]}
        </a>
      );
    }

    if (part.startsWith('http://') || part.startsWith('https://')) {
      return (
        <a key={index} href={part} target="_blank" rel="noopener noreferrer" className="message-link">
          {part}
        </a>
      );
    }

    if (/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(part)) {
      return (
        <a key={index} href={`mailto:${part}`} className="message-link">
          {part}
        </a>
      );
    }

    return part;
  });
}

function renderMarkdownBlocks(rawText) {
  if (!rawText) return null;

  const clean = rawText
    .replace(/<svg[\s\S]*?<\/svg>/gi, '')
    .replace(/&lt;svg[\s\S]*?&gt;/gi, '')
    .replace(/\\\*/g, '*')
    .replace(/\\_/g, '_')
    .replace(/\\#/g, '#')
    .replace(/\\\[/g, '[')
    .replace(/\\\]/g, ']');

  const lines = clean.split('\n');
  const blocks = [];
  let currentList = null;

  lines.forEach((rawLine, idx) => {
    const line = rawLine.trim();
    const bulletMatch = line.match(/^[-*•]\s+(.*)$/);
    const numberMatch = line.match(/^\d+\.\s+(.*)$/);

    if (bulletMatch) {
      if (!currentList || currentList.type !== 'ul') {
        currentList = { type: 'ul', items: [], key: `ul_${idx}` };
        blocks.push(currentList);
      }
      currentList.items.push(bulletMatch[1]);
      return;
    }

    if (numberMatch) {
      if (!currentList || currentList.type !== 'ol') {
        currentList = { type: 'ol', items: [], key: `ol_${idx}` };
        blocks.push(currentList);
      }
      currentList.items.push(numberMatch[1]);
      return;
    }

    currentList = null;
    if (!line) return;

    const headingMatch = line.match(/^#{1,4}\s+(.*)$/);
    if (headingMatch) {
      blocks.push({ type: 'heading', content: headingMatch[1], key: `h_${idx}` });
      return;
    }

    blocks.push({ type: 'p', content: line, key: `p_${idx}` });
  });

  return (
    <div className="message-formatted-content">
      {blocks.map((block) => {
        if (block.type === 'heading') {
          return (
            <h4 key={block.key} className="message-subheading">
              {renderInline(block.content)}
            </h4>
          );
        }
        if (block.type === 'ul') {
          return (
            <ul key={block.key} className="message-bullet-list">
              {block.items.map((it, itemIdx) => (
                <li key={itemIdx}>{renderInline(it)}</li>
              ))}
            </ul>
          );
        }
        if (block.type === 'ol') {
          return (
            <ol key={block.key} className="message-numbered-list">
              {block.items.map((it, itemIdx) => (
                <li key={itemIdx}>{renderInline(it)}</li>
              ))}
            </ol>
          );
        }
        return (
          <p key={block.key} className="message-paragraph">
            {renderInline(block.content)}
          </p>
        );
      })}
    </div>
  );
}

export default function ChatMessage({ message, activeConversationId, onRetry }) {
  const isUser = message.sender === 'user';
  const isFallback = !isUser && message.matched === false;

  const formattedTime = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  const hasSources = !isUser && Array.isArray(message.sources) && message.sources.length > 0;

  return (
    <div className={`chat-message ${isUser ? 'user-message' : 'assistant-message'} ${message.isError ? 'message-has-error' : ''}`}>
      <div className={`message-avatar ${isUser ? 'user-avatar' : 'assistant-avatar'}`} aria-hidden="true">
        {isUser ? <User className="avatar-icon" /> : <Bot className="avatar-icon" />}
      </div>

      <div className="message-content">
        <div className="message-header-meta">
          <span className="sender-name">{isUser ? 'You' : 'Nexora Assistant'}</span>
          {formattedTime && <span className="message-timestamp">{formattedTime}</span>}
          {!isUser && message.category && (
            <span className="knowledge-tag">
              <CheckCircle2 className="tag-icon" /> {message.category}
            </span>
          )}
          {hasSources && (
            <span
              className="knowledge-tag"
              title={message.sources.map((s) => s.question || s.title).filter(Boolean).join(' | ')}
            >
              <BookOpen className="tag-icon" /> {message.sources.length} {message.sources.length === 1 ? 'source' : 'sources'}
            </span>
          )}
          {isFallback && (
            <span className="knowledge-tag tag-fallback">
              <AlertCircle className="tag-icon" /> Needs Confirmation
            </span>
          )}
        </div>

        <div className={`message-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}>
          {isUser ? <p className="message-text">{message.text}</p> : renderMarkdownBlocks(message.text)}

          {message.isError && onRetry && (
            <div className="message-retry-bar">
              <button
                type="button"
                className="message-retry-btn"
                onClick={() => onRetry(message.failedQuestion || message.text)}
              >
                <RotateCcw className="retry-icon" aria-hidden="true" />
                <span>Retry Question</span>
              </button>
            </div>
          )}

          {hasSources && (
            <div className="message-sources-panel">
              <div className="sources-panel-header">
                <BookOpen className="sources-panel-icon" aria-hidden="true" />
                <span className="sources-panel-title">Verified Sources & Documentation</span>
              </div>
              <div className="sources-card-grid">
                {message.sources.map((src, idx) => {
                  const targetCategory = src.category || 'All';
                  const sourceTitle = src.question || src.title || 'FAQ Document';
                  const matchPercentage = src.relevance_score ? Math.round(src.relevance_score * 100) : null;
                  const sourceId = src.faq_id || src.id || src.document_id;
                  const targetUrl = sourceId ? `/sources/${encodeURIComponent(sourceId)}` : '/faq';

                  return (
                    <Link
                      key={idx}
                      to={targetUrl}
                      state={{
                        fromConversationId: activeConversationId,
                        sourceData: src,
                        scrollPosition:
                          (typeof document !== 'undefined' &&
                            document.querySelector('.messages-scroll-container')?.scrollTop) ||
                          0,
                      }}
                      className="source-card-item"
                      title={`View verified source details for: ${sourceTitle}`}
                    >
                      <div className="source-card-top-row">
                        <span className="source-category-pill">{targetCategory}</span>
                        {matchPercentage !== null && matchPercentage > 0 && (
                          <span className="source-relevance-pill">{matchPercentage}% match</span>
                        )}
                      </div>
                      <div className="source-card-heading">{sourceTitle}</div>
                      <div className="source-card-footer">
                        <span>View Source Details</span>
                        <ExternalLink className="source-ext-icon" aria-hidden="true" />
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
