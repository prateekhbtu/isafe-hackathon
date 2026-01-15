'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

export default function Home() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <>
      {/* Animated Background */}
      <div className="bg-grid" />

      {/* Navigation */}
      <nav className={`nav ${scrolled ? 'nav-scrolled' : ''}`}>
        <div className="container">
          <div className="nav-content">
            <Link href="/" className="logo">
              <div className="logo-icon">M</div>
              <span className="logo-text">MDRS</span>
            </Link>

            <ul className="nav-links">
              <li><a href="#features">Features</a></li>
              <li><a href="#how-it-works">How It Works</a></li>
              <li><a href="#technology">Technology</a></li>
            </ul>

            <Link href="/tool" className="btn btn-primary">
              Try Now
              <svg className="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <div className="hero-content">
            <div className="hero-badge">
              <span className="hero-badge-dot" />
              AI-Powered Media Analysis
            </div>

            <h1 className="hero-title">
              Detect Deception.<br />Protect Truth.
            </h1>

            <p className="hero-subtitle">
              MDRS analyzes images, videos, audio, and text using advanced AI to identify
              manipulation signals and provide explainable risk scores — empowering human
              judgment in the fight against misinformation.
            </p>

            <div className="hero-buttons">
              <Link href="/tool" className="btn btn-primary btn-large">
                Start Analyzing
                <svg className="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
              <a href="#how-it-works" className="btn btn-secondary btn-large">
                Learn More
              </a>
            </div>

            <div className="hero-stats">
              <div className="hero-stat">
                <div className="hero-stat-value">4</div>
                <div className="hero-stat-label">Modalities</div>
              </div>
              <div className="hero-stat">
                <div className="hero-stat-value">15+</div>
                <div className="hero-stat-label">Signals</div>
              </div>
              <div className="hero-stat">
                <div className="hero-stat-value">AI</div>
                <div className="hero-stat-label">Verified</div>
              </div>
              <div className="hero-stat">
                <div className="hero-stat-value">100%</div>
                <div className="hero-stat-label">Explainable</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="section section-alt">
        <div className="container">
          <div className="section-header">
            <span className="section-tag">Features</span>
            <h2 className="section-title">Multimodal Intelligence</h2>
            <p className="section-subtitle">
              Comprehensive analysis across all media types with state-of-the-art
              detection techniques.
            </p>
          </div>

          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🖼️</div>
              <h3 className="feature-title">Image Analysis</h3>
              <p className="feature-desc">
                Error Level Analysis (ELA), copy-move detection, metadata inspection,
                and reverse image search signals to identify manipulated or misattributed images.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">🎬</div>
              <h3 className="feature-title">Video Analysis</h3>
              <p className="feature-desc">
                Frame-level consistency checks, temporal anomaly detection, deepfake
                indicators, and compression artifact analysis for video authenticity.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">🎧</div>
              <h3 className="feature-title">Audio Analysis</h3>
              <p className="feature-desc">
                Voice synthesis detection, splice point identification, background
                noise analysis, and spectral consistency checks for audio integrity.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">📝</div>
              <h3 className="feature-title">Text Analysis</h3>
              <p className="feature-desc">
                Sentiment analysis, urgency pattern detection, source verification,
                claim extraction, and linguistic markers for textual misinformation.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">🤖</div>
              <h3 className="feature-title">AI-Powered Verification</h3>
              <p className="feature-desc">
                Integrated Gemini AI provides additional contextual analysis,
                cross-referencing, and verification insights for comprehensive assessment.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3 className="feature-title">Explainable Risk Scores</h3>
              <p className="feature-desc">
                Every risk score comes with detailed signal breakdowns, confidence
                levels, and actionable recommendations — no black box decisions.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="section">
        <div className="container">
          <div className="section-header">
            <span className="section-tag">Process</span>
            <h2 className="section-title">How It Works</h2>
            <p className="section-subtitle">
              Three simple steps to get actionable insights about your media.
            </p>
          </div>

          <div className="steps-container">
            <div className="step-card">
              <div className="step-number">1</div>
              <h3 className="step-title">Upload Media</h3>
              <p className="step-desc">
                Select an image, video, audio file, or paste text content along with
                optional metadata like source and context.
              </p>
            </div>

            <div className="step-card">
              <div className="step-number">2</div>
              <h3 className="step-title">AI Analysis</h3>
              <p className="step-desc">
                Our system runs multiple detection algorithms and AI verification
                to identify manipulation signals and assess risk.
              </p>
            </div>

            <div className="step-card">
              <div className="step-number">3</div>
              <h3 className="step-title">Get Insights</h3>
              <p className="step-desc">
                Receive a detailed risk score with signal breakdowns, explanations,
                and recommended human actions.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Technology Section */}
      <section id="technology" className="section section-alt">
        <div className="container">
          <div className="section-header">
            <span className="section-tag">Stack</span>
            <h2 className="section-title">Powered By</h2>
            <p className="section-subtitle">
              Built with cutting-edge technologies for reliability and performance.
            </p>
          </div>

          <div className="tech-grid">
            <div className="tech-item">
              <div className="tech-icon">⚡</div>
              <div className="tech-name">FastAPI</div>
            </div>
            <div className="tech-item">
              <div className="tech-icon">⚛️</div>
              <div className="tech-name">Next.js 14</div>
            </div>
            <div className="tech-item">
              <div className="tech-icon">🐍</div>
              <div className="tech-name">Python</div>
            </div>
            <div className="tech-item">
              <div className="tech-icon">🧠</div>
              <div className="tech-name">Gemini AI</div>
            </div>
            <div className="tech-item">
              <div className="tech-icon">🔬</div>
              <div className="tech-name">PIL/NumPy</div>
            </div>
            <div className="tech-item">
              <div className="tech-icon">📊</div>
              <div className="tech-name">SciPy</div>
            </div>
            <div className="tech-item">
              <div className="tech-icon">💬</div>
              <div className="tech-name">TextBlob</div>
            </div>
            <div className="tech-item">
              <div className="tech-icon">🔐</div>
              <div className="tech-name">TypeScript</div>
            </div>
          </div>
        </div>
      </section>

      {/* Ethical Notice */}
      <section className="section">
        <div className="container">
          <div className="section-header">
            <span className="section-tag">Ethics</span>
            <h2 className="section-title">Responsible AI Design</h2>
            <p className="section-subtitle">
              We believe in augmenting human judgment, not replacing it.
            </p>
          </div>

          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">⚖️</div>
              <h3 className="feature-title">No Binary Claims</h3>
              <p className="feature-desc">
                We never declare content "real" or "fake." Risk scores guide investigation,
                not accusation.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">🔍</div>
              <h3 className="feature-title">Full Transparency</h3>
              <p className="feature-desc">
                Every signal, confidence level, and reasoning is exposed. You see exactly
                how conclusions were reached.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">👤</div>
              <h3 className="feature-title">Human In The Loop</h3>
              <p className="feature-desc">
                Final decisions must be made by humans. Our system supports judgment,
                not automated enforcement.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-card">
            <h2 className="cta-title">Ready to Analyze?</h2>
            <p className="cta-subtitle">
              Start detecting deception risks in your media content today.
            </p>
            <Link href="/tool" className="btn btn-large" style={{ background: 'white', color: 'black' }}>
              Try MDRS Now
              <svg className="btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <p className="footer-text">
            Built for iSafe Hackathon 2026 • <a href="#" className="footer-link">Multimodal Deception Risk Scorer</a>
          </p>
        </div>
      </footer>
    </>
  )
}
