import React, { useState, useEffect, useMemo } from 'react';
import { Link, useSearchParams, useLocation, useNavigate } from 'react-router-dom';
import { 
  Search, 
  X, 
  ArrowLeft, 
  HelpCircle, 
  SlidersHorizontal,
  Bot,
  FilterX,
  Tag,
  CheckCircle2,
  MessageCircle
} from 'lucide-react';
import { FAQS_DATA, FAQ_CATEGORIES } from '../data/faqs.js';
import FAQItem from '../components/FAQItem';
import { fetchFAQs, fetchFAQCategories, searchFAQs } from '../services/api';

export default function FAQPage({ onAskInChat }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();

  const urlCategory = searchParams.get('category');
  const urlFaqId = searchParams.get('id') || searchParams.get('faq_id');

  useEffect(() => {
    if (urlFaqId) {
      navigate(`/sources/${encodeURIComponent(urlFaqId)}`, { 
        replace: true,
        state: location.state
      });
    }
  }, [urlFaqId, navigate, location.state]);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(urlCategory || 'All');
  const [categories, setCategories] = useState(FAQ_CATEGORIES);
  const [backendFAQs, setBackendFAQs] = useState(null);

  useEffect(() => {
    if (urlCategory && urlCategory !== selectedCategory) {
      setSelectedCategory(urlCategory);
    }
  }, [urlCategory]);

  useEffect(() => {
    fetchFAQCategories()
      .then((cats) => {
        if (cats && cats.length > 0) {
          setCategories(cats);
        }
      })
      .catch((err) => {
        console.warn('[FAQPage] Using default categories:', err);
      });
  }, []);

  useEffect(() => {
    let active = true;
    const timer = setTimeout(() => {
      const request = searchQuery.trim()
        ? searchFAQs(searchQuery.trim(), selectedCategory)
        : fetchFAQs(selectedCategory);

      request
        .then((data) => {
          if (active && Array.isArray(data)) {
            setBackendFAQs(data);
          }
        })
        .catch((err) => {
          if (active) {
            console.warn('[FAQPage] Fallback to local FAQ data:', err);
            setBackendFAQs(null);
          }
        });
    }, 250);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [searchQuery, selectedCategory]);

  const allFAQsList = useMemo(() => {
    return backendFAQs && backendFAQs.length > 0 ? backendFAQs : FAQS_DATA;
  }, [backendFAQs]);

  const selectedFaq = useMemo(() => {
    if (!urlFaqId) return null;
    return allFAQsList.find(
      (f) => String(f.id) === String(urlFaqId) || (f.slug && String(f.slug) === String(urlFaqId))
    ) || null;
  }, [urlFaqId, allFAQsList]);

  const relatedFAQs = useMemo(() => {
    if (!selectedFaq) return [];
    return allFAQsList.filter(
      (f) => f.category === selectedFaq.category && String(f.id) !== String(selectedFaq.id)
    );
  }, [selectedFaq, allFAQsList]);

  const filteredFAQs = useMemo(() => {
    if (backendFAQs !== null) {
      return backendFAQs;
    }

    const query = searchQuery.toLowerCase().trim();
    return FAQS_DATA.filter((faq) => {
      const matchesCategory = selectedCategory === 'All' || faq.category === selectedCategory;
      const matchesSearch =
        !query ||
        faq.question.toLowerCase().includes(query) ||
        faq.answer.toLowerCase().includes(query) ||
        (faq.keywords && faq.keywords.some((k) => k.toLowerCase().includes(query)));

      return matchesCategory && matchesSearch;
    });
  }, [backendFAQs, searchQuery, selectedCategory]);

  const handleCategorySelect = (cat) => {
    setSelectedCategory(cat);
    const newParams = new URLSearchParams(searchParams);
    if (cat === 'All') {
      newParams.delete('category');
    } else {
      newParams.set('category', cat);
    }
    newParams.delete('id');
    newParams.delete('faq_id');
    setSearchParams(newParams, { replace: true });
  };

  const handleBackToAll = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.delete('id');
    newParams.delete('faq_id');
    setSearchParams(newParams);
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedCategory('All');
    setSearchParams({}, { replace: true });
  };

  const totalQuestionsCount = backendFAQs ? backendFAQs.length : FAQS_DATA.length;

  return (
    <div className="faq-page-container">
      <header className="page-header">
        <div className="page-header-top">
          <Link to="/" className="back-link-btn" title="Return to Chat Assistant">
            <ArrowLeft className="back-icon" aria-hidden="true" />
            <span>Back to Assistant</span>
          </Link>
          <span className="page-status-pill">
            {selectedFaq ? 'Verified Source Detail' : 'Knowledge Base v1.0'}
          </span>
        </div>

        <div className="page-header-title-block">
          <div className="title-icon-badge" aria-hidden="true">
            <HelpCircle className="header-badge-icon" />
          </div>
          <div>
            <h1 className="page-main-heading">
              {selectedFaq ? 'Verified FAQ Documentation' : 'Frequently Asked Questions'}
            </h1>
            <p className="page-subheading">
              {selectedFaq 
                ? 'Official verified company answer and reference documentation retrieved by the AI Assistant.'
                : 'Browse verified company answers regarding our products, business hours, billing, cancellation policies, and customer support.'}
            </p>
          </div>
        </div>
      </header>

      {selectedFaq ? (
        <main className="faq-content-wrap">
          <div className="faq-detail-view-card">
            <div className="faq-detail-nav-row">
              <button 
                type="button" 
                className="faq-detail-back-link" 
                onClick={handleBackToAll}
                title="Return to FAQ category list"
              >
                <ArrowLeft className="back-icon" aria-hidden="true" />
                <span>Browse All FAQs {selectedFaq.category ? `in "${selectedFaq.category}"` : ''}</span>
              </button>

              <span className="source-relevance-pill">
                Verified Knowledge Base Document
              </span>
            </div>

            <div className="faq-detail-header-block">
              <div className="faq-detail-pills">
                <span className="faq-category-pill">
                  <Tag className="pill-icon" aria-hidden="true" />
                  {selectedFaq.category}
                </span>
                <span className="faq-matched-badge">
                  <CheckCircle2 className="pill-icon" aria-hidden="true" />
                  Source #{selectedFaq.id}
                </span>
              </div>
              <h2 className="faq-detail-question-heading">{selectedFaq.question}</h2>
            </div>

            <div className="faq-detail-body">
              <h3 className="faq-detail-body-label">Official Answer & Documentation</h3>
              <p className="faq-detail-answer-text">{selectedFaq.answer}</p>

              {selectedFaq.keywords && selectedFaq.keywords.length > 0 && (
                <div className="faq-detail-keywords-section">
                  <span className="keywords-label">Related Topics:</span>
                  <div className="keywords-list">
                    {selectedFaq.keywords.map((kw, i) => (
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
                onClick={() => onAskInChat(selectedFaq.question)}
                title="Open Chat Assistant and ask this question directly"
              >
                <MessageCircle className="btn-icon" aria-hidden="true" />
                <span>Ask Chatbot about this</span>
              </button>

              <button
                type="button"
                className="secondary-action-btn"
                onClick={handleBackToAll}
              >
                <SlidersHorizontal className="btn-icon" aria-hidden="true" />
                <span>Explore Other FAQs</span>
              </button>
            </div>
          </div>

          {relatedFAQs.length > 0 && (
            <section className="faq-related-section" aria-label="Related FAQs in this category">
              <h3 className="related-section-title">Other Questions in {selectedFaq.category}</h3>
              <div className="faq-accordion-list">
                {relatedFAQs.map((faq) => (
                  <FAQItem
                    key={faq.id}
                    faq={faq}
                    onAskInChat={onAskInChat}
                  />
                ))}
              </div>
            </section>
          )}
        </main>
      ) : (
        <main className="faq-content-wrap">
          <section className="faq-controls-card" aria-label="FAQ Search and Filters">
            <div className="faq-search-box">
              <Search className="search-input-icon" aria-hidden="true" />
              <label htmlFor="faq-search-input" className="visually-hidden">
                Search FAQs by question or keyword
              </label>
              <input
                id="faq-search-input"
                type="text"
                className="faq-search-input"
                placeholder="Search by keywords, questions, or topics (e.g. refund, hours, pricing)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button
                  type="button"
                  className="search-clear-btn"
                  onClick={() => setSearchQuery('')}
                  aria-label="Clear search input"
                >
                  <X className="clear-icon" />
                </button>
              )}
            </div>

            <div className="category-filter-chips" role="group" aria-label="Filter by category">
              <span className="filter-label">
                <SlidersHorizontal className="filter-icon" aria-hidden="true" />
                Categories:
              </span>
              {categories.map((cat) => {
                const isSelected = selectedCategory === cat;
                return (
                  <button
                    key={cat}
                    type="button"
                    className={`category-chip ${isSelected ? 'is-selected' : ''}`}
                    onClick={() => handleCategorySelect(cat)}
                    aria-pressed={isSelected}
                  >
                    {cat}
                  </button>
                );
              })}
            </div>
          </section>

          <div className="faq-results-meta">
            <span className="results-count">
              Showing <strong>{filteredFAQs.length}</strong> of {totalQuestionsCount} questions
              {selectedCategory !== 'All' && ` in "${selectedCategory}"`}
              {searchQuery && ` matching "${searchQuery}"`}
            </span>

            {(searchQuery || selectedCategory !== 'All') && (
              <button
                type="button"
                className="reset-filters-link"
                onClick={handleResetFilters}
              >
                Reset Filters
              </button>
            )}
          </div>

          {filteredFAQs.length > 0 ? (
            <div className="faq-accordion-list" role="region" aria-label="FAQ Question List">
              {filteredFAQs.map((faq) => (
                <FAQItem
                  key={faq.id}
                  faq={faq}
                  onAskInChat={onAskInChat}
                />
              ))}
            </div>
          ) : (
            <div className="faq-empty-results-card">
              <div className="empty-results-icon-wrap" aria-hidden="true">
                <FilterX className="empty-filter-icon" />
              </div>
              <h2 className="empty-results-title">No matching questions found</h2>
              <p className="empty-results-desc">
                We couldn't find any FAQs matching "{searchQuery}". Try using different terms, clearing the category filter, or ask our interactive chatbot directly.
              </p>
              <div className="empty-results-actions">
                <button
                  type="button"
                  className="primary-action-btn"
                  onClick={handleResetFilters}
                >
                  Reset Search & Filters
                </button>
                <Link to="/" className="secondary-action-btn">
                  <Bot className="btn-icon" aria-hidden="true" />
                  Ask Assistant Instead
                </Link>
              </div>
            </div>
          )}
        </main>
      )}
    </div>
  );
}
