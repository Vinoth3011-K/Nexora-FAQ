import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  HelpCircle, 
  Tag, 
  CheckCircle2, 
  MessageCircle, 
  BookOpen
} from 'lucide-react';
import { FAQS_DATA } from '../data/faqs';
import { fetchFAQById } from '../services/api';

export default function SourceDetailPage({ activeConversationId, onAskInChat }) {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  // Originating conversation ID passed from the ChatMessage source card
  const fromConversationId = location.state?.fromConversationId || activeConversationId;
  const returnScrollTop = location.state?.scrollPosition || 0;
  const passedSourceData = location.state?.sourceData;

  const [source, setSource] = useState(() => {
    // Check if full source data was passed in navigation state
    if (passedSourceData && (passedSourceData.answer || passedSourceData.text)) {
      return {
        id: passedSourceData.faq_id || passedSourceData.id || id,
        question: passedSourceData.question || passedSourceData.title || `Source #${id}`,
        answer: passedSourceData.answer || passedSourceData.text,
        category: passedSourceData.category || 'General',
        relevance_score: passedSourceData.relevance_score,
        keywords: passedSourceData.keywords || []
      };
    }
    // Check fallback local FAQs data
    const local = FAQS_DATA.find((f) => String(f.id) === String(id) || String(f.slug) === String(id));
    return local || null;
  });

  const [isLoading, setIsLoading] = useState(!source);
  const [error, setError] = useState(null);

  // Fetch from backend API to ensure we display the latest database content
  useEffect(() => {
    let isMounted = true;

    async function loadSource() {
      try {
        setIsLoading(true);
        const data = await fetchFAQById(id);
        if (!isMounted) return;

        if (data && (data.question || data.title)) {
          setSource({
            id: data.id,
            question: data.question || data.title,
            answer: data.answer || data.content || data.text,
            category: data.category || 'General',
            relevance_score: passedSourceData?.relevance_score || data.relevance_score,
            keywords: data.keywords || []
          });
          setError(null);
        }
      } catch (err) {
        console.warn(`[SourceDetailPage] Failed to fetch source #${id} from backend API:`, err);
        if (!isMounted) return;

        // If we already have local or passed source data, continue using it
        if (!source) {
          const local = FAQS_DATA.find((f) => String(f.id) === String(id) || String(f.slug) === String(id));
          if (local) {
            setSource(local);
            setError(null);
          } else if (passedSourceData) {
            setSource({
              id: passedSourceData.faq_id || passedSourceData.id || id,
              question: passedSourceData.question || passedSourceData.title || `Source #${id}`,
              answer: passedSourceData.answer || passedSourceData.text || 'Official verified documentation.',
              category: passedSourceData.category || 'General',
              relevance_score: passedSourceData.relevance_score,
              keywords: passedSourceData.keywords || []
            });
            setError(null);
          } else {
            setError(`Could not find details for Source #${id}.`);
          }
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadSource();
    return () => {
      isMounted = false;
    };
  }, [id, passedSourceData]);

  // Return to the exact originating chat conversation
  const handleBackToChat = () => {
    navigate('/', {
      state: {
        returnToConversationId: fromConversationId,
        returnScrollTop: returnScrollTop
      }
    });
  };

  // Submit the source question as a follow-up in the SAME conversation
  const handleAskInChat = () => {
    if (!source) return;
    const questionToAsk = source.question || source.title;
    if (onAskInChat) {
      onAskInChat(questionToAsk, fromConversationId);
    } else {
      navigate('/', {
        state: {
          askQuestion: questionToAsk,
          targetConversationId: fromConversationId,
          timestamp: Date.now()
        }
      });
    }
  };

  const matchPercentage = source?.relevance_score
    ? Math.round(source.relevance_score * 100)
    : (passedSourceData?.relevance_score ? Math.round(passedSourceData.relevance_score * 100) : null);

  return (
    <div className="faq-page-container source-detail-page-container">
      {/* Page Header */}
      <header className="page-header">
        <div className="page-header-top">
          <button 
            type="button" 
            className="back-link-btn" 
            onClick={handleBackToChat}
            title="Return to your chat conversation"
          >
            <ArrowLeft className="back-icon" aria-hidden="true" />
            <span>Back to Assistant</span>
          </button>
          <span className="page-status-pill">
            Verified Source #{id}
          </span>
        </div>

        <div className="page-header-title-block">
          <div className="title-icon-badge" aria-hidden="true">
            <BookOpen className="header-badge-icon" />
          </div>
          <div>
            <h1 className="page-main-heading">Verified Source & Documentation</h1>
            <p className="page-subheading">
              Official company reference documentation retrieved by the AI Assistant to formulate verified responses.
            </p>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="faq-content-wrap">
        {isLoading && !source ? (
          <div className="faq-detail-view-card source-detail-state-card">
            <div className="loading-spinner source-loading-spinner" aria-hidden="true" />
            <p className="source-loading-text">
              Loading verified source documentation...
            </p>
          </div>
        ) : error && !source ? (
          <div className="faq-detail-view-card source-detail-state-card">
            <p className="source-error-text">
              {error}
            </p>
            <button
              type="button"
              className="primary-action-btn"
              onClick={handleBackToChat}
            >
              <ArrowLeft className="btn-icon" aria-hidden="true" />
              <span>Return to Chat Assistant</span>
            </button>
          </div>
        ) : source ? (
          <div className="faq-detail-view-card">
            <div className="faq-detail-nav-row">
              <button 
                type="button" 
                className="faq-detail-back-link" 
                onClick={handleBackToChat}
                title="Return to your chat conversation"
              >
                <ArrowLeft className="back-icon" aria-hidden="true" />
                <span>Return to Chat Conversation</span>
              </button>

              <span className="source-relevance-pill">
                {matchPercentage ? `${matchPercentage}% Match Relevance` : 'Verified Knowledge Base Document'}
              </span>
            </div>

            <div className="faq-detail-header-block">
              <div className="faq-detail-pills">
                {source.category && (
                  <span className="faq-category-pill">
                    <Tag className="pill-icon" aria-hidden="true" />
                    {source.category}
                  </span>
                )}
                <span className="faq-matched-badge">
                  <CheckCircle2 className="pill-icon" aria-hidden="true" />
                  Source #{source.id || id}
                </span>
              </div>
              <h2 className="faq-detail-question-heading">{source.question || source.title}</h2>
            </div>

            <div className="faq-detail-body">
              <h3 className="faq-detail-body-label">Official Answer & Documentation</h3>
              <p className="faq-detail-answer-text">{source.answer || source.content || source.text}</p>

              {source.keywords && source.keywords.length > 0 && (
                <div className="faq-detail-keywords-section">
                  <span className="keywords-label">Related Topics:</span>
                  <div className="keywords-list">
                    {source.keywords.map((kw, i) => (
                      <span key={i} className="keyword-tag">{kw}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="faq-detail-footer-actions">
              <button
                type="button"
                className="primary-action-btn faq-detail-ask-btn"
                onClick={handleAskInChat}
                title="Return to chat and submit this question as a follow-up in the same conversation"
              >
                <MessageCircle className="btn-icon" aria-hidden="true" />
                <span>Ask Chatbot about this</span>
              </button>

              <Link
                to={source.category && source.category !== 'All' ? `/faq?category=${encodeURIComponent(source.category)}` : '/faq'}
                className="secondary-action-btn"
                title="Explore the entire FAQ Knowledge Base repository"
              >
                <HelpCircle className="btn-icon" aria-hidden="true" />
                <span>Browse in FAQ Knowledge Base</span>
              </Link>
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
}

