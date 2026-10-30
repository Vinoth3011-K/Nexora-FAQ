import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Info, 
  CheckCircle2,
  Cpu
} from 'lucide-react';

export default function AboutPage() {
  return (
    <div className="about-page-container">
      {/* Page Header */}
      <header className="page-header">
        <div className="page-header-top">
          <Link to="/" className="back-link-btn" title="Return to Chat Assistant">
            <ArrowLeft className="back-icon" aria-hidden="true" />
            <span>Back to Assistant</span>
          </Link>
          <span className="page-status-pill">Overview</span>
        </div>

        <div className="page-header-title-block">
          <div className="title-icon-badge" aria-hidden="true">
            <Info className="header-badge-icon" />
          </div>
          <div>
            <h1 className="page-main-heading">About Nexora FAQ Assistant</h1>
            <p className="page-subheading">
              Learn more about the Nexora FAQ Assistant and its capabilities.
            </p>
          </div>
        </div>
      </header>

      {/* Main Content Sections */}
      <main className="about-content-wrap">
        {/* Section 1: Overview */}
        <section className="about-card" aria-labelledby="about-overview-title">
          <h2 id="about-overview-title" className="about-card-title">
            <Cpu className="about-title-icon" aria-hidden="true" />
            About the Assistant
          </h2>
          <p className="about-card-text">
            The <strong>Company FAQ Assistant</strong> is designed to empower employees, prospective clients, and team members with instant, accurate access to company information. Instead of manually combing through lengthy handbooks, wiki pages, or policy repositories, users can naturally converse with an intelligent assistant to locate verified answers on demand.
          </p>
          <div className="about-features-grid">
            <div className="about-mini-feature">
              <CheckCircle2 className="feature-check-icon" aria-hidden="true" />
              <span>Instant knowledge discovery</span>
            </div>
            <div className="about-mini-feature">
              <CheckCircle2 className="feature-check-icon" aria-hidden="true" />
              <span>Grounded company answers</span>
            </div>
            <div className="about-mini-feature">
              <CheckCircle2 className="feature-check-icon" aria-hidden="true" />
              <span>Reduces internal support overhead</span>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

