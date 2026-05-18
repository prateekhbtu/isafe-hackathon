'use client'

import { useState } from 'react'
import Link from 'next/link'
import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Modality = 'image' | 'video' | 'audio' | 'text'

// Format Gemini's markdown-style response
const formatGeminiText = (text: string) => {
  if (!text) return null
  
  // Split by ** markers and create formatted output
  const parts = text.split(/\*\*(.*?)\*\*/g)
  return (
    <>
      {parts.map((part, i) => 
        i % 2 === 0 ? (
          <span key={i}>{part}</span>
        ) : (
          <strong key={i} style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{part}</strong>
        )
      )}
    </>
  )
}

interface Signal {
  signal: string
  description: string
  confidence: number
  weight: number
  contribution: number
  evidence: Record<string, any>
}

interface Recommendation {
  action: string
  priority: string
  suggested_steps: string[]
  human_review_required: boolean
}

interface NewsArticle {
  source: { name: string }
  title: string
  description: string
  url: string
  publishedAt: string
}

interface NewsAPIVerification {
  newsapi_available: boolean
  credibility_score: number | null
  credibility_level?: string
  credibility_reasoning?: string
  corroborating_sources?: number
  total_related_articles?: number
  headline_matches?: number
  top_sources?: string[]
  sample_articles?: NewsArticle[]
  queries_tried?: Array<{ query: string; results_found: number }>
}

interface URLMetadata {
  source_url?: string
  source_type?: string
  title?: string
  file_size_mb?: number
}

interface AnalysisResult {
  risk_score: number
  risk_level: string
  modality: string
  signals_detected: number
  signal_breakdown: Signal[]
  explanation: string
  recommendation: Recommendation
  gemini_analysis?: string
  gemini_verified?: boolean
  newsapi_verification?: NewsAPIVerification
  url_metadata?: URLMetadata
  disclaimer: string
  timestamp: string | null
  source: string | null
}

const modalityConfig = {
  image: { icon: '🖼️', label: 'Image', accept: 'image/*' },
  video: { icon: '🎬', label: 'Video', accept: 'video/*' },
  audio: { icon: '🎧', label: 'Audio', accept: 'audio/*' },
  text: { icon: '📝', label: 'Text', accept: '' },
}

// Simple URL validation
const isValidUrl = (url: string): boolean => {
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    return false
  }
}

export default function ToolPage() {
  const [activeTab, setActiveTab] = useState<Modality>('image')
  const [file, setFile] = useState<File | null>(null)
  const [mediaUrl, setMediaUrl] = useState('')
  const [urlError, setUrlError] = useState<string | null>(null)
  const [textContent, setTextContent] = useState('')
  const [source, setSource] = useState('')
  const [timestamp, setTimestamp] = useState('')
  const [context, setContext] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setMediaUrl('')
      setUrlError(null)
      setError(null)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.currentTarget.classList.add('drag-over')
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.currentTarget.classList.remove('drag-over')
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.currentTarget.classList.remove('drag-over')
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
      setMediaUrl('')
      setUrlError(null)
      setError(null)
    }
  }

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setMediaUrl(val)
    if (file) setFile(null)
    setError(null)

    // Real-time URL validation
    if (val.trim() && !isValidUrl(val.trim())) {
      setUrlError('Please enter a valid URL starting with http:// or https://')
    } else {
      setUrlError(null)
    }
  }

  const handleAnalyze = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const formData = new FormData()

      if (activeTab === 'text') {
        if (!textContent.trim()) {
          setError('Please enter text content to analyze')
          setLoading(false)
          return
        }
        formData.append('text', textContent)
      } else if (activeTab === 'audio' || activeTab === 'video') {
        if (!file && !mediaUrl.trim()) {
          setError(`Please select a ${activeTab} file or paste a URL to analyze`)
          setLoading(false)
          return
        }
        if (mediaUrl.trim() && !isValidUrl(mediaUrl.trim())) {
          setError('Please enter a valid URL')
          setLoading(false)
          return
        }
        if (file) {
          formData.append('file', file)
        }
        if (mediaUrl.trim()) {
          formData.append('url', mediaUrl.trim())
        }
      } else {
        if (!file) {
          setError('Please select a file to analyze')
          setLoading(false)
          return
        }
        formData.append('file', file)
      }

      if (source) formData.append('source', source)
      if (timestamp) formData.append('timestamp', timestamp)
      if (context) formData.append('context', context)

      const response = await axios.post<AnalysisResult>(
        `${API_BASE_URL}/analyze/${activeTab}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 120000, // 2 min timeout for URL processing
        }
      )

      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.')
      console.error('Analysis error:', err)
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setFile(null)
    setMediaUrl('')
    setUrlError(null)
    setTextContent('')
    setSource('')
    setTimestamp('')
    setContext('')
    setResult(null)
    setError(null)
  }

  const isAnalyzeDisabled = () => {
    if (loading) return true
    if (activeTab === 'text') return !textContent.trim()
    if (activeTab === 'audio' || activeTab === 'video') {
      if (mediaUrl.trim() && !isValidUrl(mediaUrl.trim())) return true
      return !file && !mediaUrl.trim()
    }
    return !file
  }

  const getCredibilityColor = (level?: string) => {
    switch (level) {
      case 'High': return 'var(--accent-secondary)'
      case 'Medium': return '#ea580c'
      case 'Low': return 'var(--accent-primary)'
      default: return 'var(--text-tertiary)'
    }
  }

  return (
    <>
      {/* Animated Background */}
      <div className="bg-grid" />
      <div className="bg-gradient-blur bg-blur-1" />
      <div className="bg-gradient-blur bg-blur-2" />

      {/* Navigation */}
      <nav className="nav">
        <div className="container">
          <div className="nav-content">
            <Link href="/" className="logo">
              <div className="logo-icon">M</div>
              <span className="logo-text">MDRS</span>
            </Link>

            <Link href="/" className="btn btn-secondary">
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Home
            </Link>
          </div>
        </div>
      </nav>

      <main className="tool-page">
        <div className="container">
          {!result ? (
            <>
              {/* Header */}
              <div className="tool-header">
                <h1 className="tool-title">Analyze Media</h1>
                <p className="tool-subtitle">
                  Upload content or paste a URL to assess deception risk with explainable AI
                </p>
              </div>

              <div className="tool-container">
                <div className="upload-card">
                  {/* Modality Tabs */}
                  <div className="modality-tabs">
                    {(Object.keys(modalityConfig) as Modality[]).map((modality) => (
                      <button
                        key={modality}
                        className={`modality-tab ${activeTab === modality ? 'active' : ''}`}
                        onClick={() => {
                          setActiveTab(modality)
                          setFile(null)
                          setMediaUrl('')
                          setUrlError(null)
                          setTextContent('')
                          setError(null)
                        }}
                      >
                        <span className="modality-tab-icon">{modalityConfig[modality].icon}</span>
                        {modalityConfig[modality].label}
                      </button>
                    ))}
                  </div>

                  {/* Upload Area */}
                  {activeTab === 'text' ? (
                    <div className="text-input-area">
                      <textarea
                        className="text-input"
                        value={textContent}
                        onChange={(e) => setTextContent(e.target.value)}
                        placeholder="Paste or type text content to analyze for deception signals..."
                      />
                    </div>
                  ) : (
                    <div
                      className={`upload-area ${file ? 'has-file' : ''}`}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                      onClick={() => document.getElementById('file-input')?.click()}
                    >
                      <input
                        id="file-input"
                        type="file"
                        accept={modalityConfig[activeTab].accept}
                        onChange={handleFileChange}
                        style={{ display: 'none' }}
                      />
                      {file ? (
                        <>
                          <div className="upload-icon">✅</div>
                          <div className="upload-file-name">
                            <span>{file.name}</span>
                            <span style={{ opacity: 0.7 }}>
                              ({(file.size / 1024).toFixed(1)} KB)
                            </span>
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="upload-icon">
                            {modalityConfig[activeTab].icon}
                          </div>
                          <p className="upload-text">
                            Drop your {activeTab} file here or click to browse
                          </p>
                          <p className="upload-hint">
                            Supports all common {activeTab} formats
                          </p>
                        </>
                      )}
                    </div>
                  )}

                  {/* URL Input for Audio/Video */}
                  {(activeTab === 'audio' || activeTab === 'video') && (
                    <div className="url-input-section">
                      <div className="url-divider">
                        <span className="url-divider-line" />
                        <span className="url-divider-text">OR</span>
                        <span className="url-divider-line" />
                      </div>
                      <div className="url-input-wrapper">
                        <div className="url-input-icon">
                          <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                          </svg>
                        </div>
                        <input
                          type="url"
                          className={`url-input ${urlError ? 'url-input-error' : ''} ${mediaUrl && !urlError ? 'url-input-valid' : ''}`}
                          value={mediaUrl}
                          onChange={handleUrlChange}
                          placeholder={`Paste ${activeTab} URL (YouTube, direct link...)`}
                        />
                        {mediaUrl && !urlError && (
                          <div className="url-valid-icon">✓</div>
                        )}
                      </div>
                      {urlError && (
                        <p className="url-error-text">{urlError}</p>
                      )}
                      <p className="upload-hint" style={{ marginTop: '8px' }}>
                        Supports direct media links (.mp4, .mp3, .wav) and YouTube URLs
                      </p>
                    </div>
                  )}

                  {/* Metadata Section */}
                  <div className="metadata-section">
                    <h4 className="metadata-title">
                      <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Optional Metadata (Improves Analysis)
                    </h4>
                    <div className="metadata-grid">
                      <input
                        type="text"
                        className="metadata-input"
                        value={source}
                        onChange={(e) => setSource(e.target.value)}
                        placeholder="Source (e.g., Twitter)"
                      />
                      <input
                        type="text"
                        className="metadata-input"
                        value={timestamp}
                        onChange={(e) => setTimestamp(e.target.value)}
                        placeholder="Timestamp"
                      />
                      <input
                        type="text"
                        className="metadata-input"
                        value={context}
                        onChange={(e) => setContext(e.target.value)}
                        placeholder="Claimed context"
                      />
                    </div>
                  </div>

                  {/* Analyze Button */}
                  <button
                    className="analyze-btn"
                    onClick={handleAnalyze}
                    disabled={isAnalyzeDisabled()}
                  >
                    {loading ? (
                      <>
                        <div className="loading-spinner" />
                        {mediaUrl ? 'Fetching & Analyzing...' : 'Analyzing...'}
                      </>
                    ) : (
                      <>
                        <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        Analyze {modalityConfig[activeTab].label}
                      </>
                    )}
                  </button>

                  {/* Error Display */}
                  {error && (
                    <div className="error-card">
                      <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      {error}
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            /* Results Section */
            <div className="results-container">
              {/* URL Source Info */}
              {result.url_metadata && (
                <div className="url-source-card">
                  <div className="card-header">
                    <div className="card-icon">🔗</div>
                    <h3 className="card-title">Source URL Info</h3>
                    <span className="source-type-badge">
                      {result.url_metadata.source_type === 'youtube' ? '▶ YouTube' : '🌐 Direct'}
                    </span>
                  </div>
                  <div className="url-source-details">
                    {result.url_metadata.title && (
                      <p className="url-source-title">{result.url_metadata.title}</p>
                    )}
                    <p className="url-source-url">{result.url_metadata.source_url}</p>
                    {result.url_metadata.file_size_mb && (
                      <span className="url-source-size">
                        {result.url_metadata.file_size_mb} MB processed
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Risk Score Card */}
              <div className="risk-score-card">
                <p className="risk-score-label">Deception Risk Score</p>
                <div className="risk-score-value">{result.risk_score}</div>
                <span className={`risk-level-badge ${result.risk_level.toLowerCase()}`}>
                  <span style={{ fontSize: '1.2em' }}>
                    {result.risk_level === 'Low' ? '✓' : result.risk_level === 'Medium' ? '⚠' : '⚠️'}
                  </span>
                  {result.risk_level} Risk
                </span>
                <p className="risk-signals-count">
                  Based on {result.signals_detected} detected signal{result.signals_detected !== 1 ? 's' : ''}
                </p>
              </div>

              {/* Explanation Card */}
              <div className="explanation-card">
                <div className="card-header">
                  <div className="card-icon">📊</div>
                  <h3 className="card-title">Analysis Explanation</h3>
                </div>
                <p className="explanation-text">{result.explanation}</p>
              </div>

              {/* Gemini AI Card */}
              {result.gemini_analysis && (
                <div className="explanation-card gemini-card">
                  <div className="card-header">
                    <div className="card-icon">🤖</div>
                    <h3 className="card-title">AI Verification</h3>
                    {result.gemini_verified && (
                      <span className="gemini-badge">
                        <svg width="12" height="12" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        Gemini Verified
                      </span>
                    )}
                  </div>
                  <div className="explanation-text">{formatGeminiText(result.gemini_analysis)}</div>
                </div>
              )}

              {/* NewsAPI Verification Card */}
              {result.newsapi_verification && result.newsapi_verification.newsapi_available && result.newsapi_verification.credibility_score !== null && (
                <div className="explanation-card newsapi-card">
                  <div className="card-header">
                    <div className="card-icon">📰</div>
                    <h3 className="card-title">News Source Verification</h3>
                    <span
                      className="newsapi-badge"
                      style={{ background: getCredibilityColor(result.newsapi_verification.credibility_level) }}
                    >
                      {result.newsapi_verification.credibility_level} Credibility
                    </span>
                  </div>

                  <div className="newsapi-score-row">
                    <div className="newsapi-stat">
                      <span className="newsapi-stat-value">
                        {result.newsapi_verification.credibility_score}
                      </span>
                      <span className="newsapi-stat-label">Credibility Score</span>
                    </div>
                    <div className="newsapi-stat">
                      <span className="newsapi-stat-value">
                        {result.newsapi_verification.corroborating_sources || 0}
                      </span>
                      <span className="newsapi-stat-label">Sources Found</span>
                    </div>
                    <div className="newsapi-stat">
                      <span className="newsapi-stat-value">
                        {result.newsapi_verification.total_related_articles || 0}
                      </span>
                      <span className="newsapi-stat-label">Related Articles</span>
                    </div>
                    <div className="newsapi-stat">
                      <span className="newsapi-stat-value">
                        {result.newsapi_verification.headline_matches || 0}
                      </span>
                      <span className="newsapi-stat-label">Headline Matches</span>
                    </div>
                  </div>

                  {result.newsapi_verification.credibility_reasoning && (
                    <p className="newsapi-reasoning">
                      {result.newsapi_verification.credibility_reasoning}
                    </p>
                  )}

                  {result.newsapi_verification.top_sources && result.newsapi_verification.top_sources.length > 0 && (
                    <div className="newsapi-sources">
                      <p className="newsapi-sources-label">Corroborating Sources:</p>
                      <div className="newsapi-source-tags">
                        {result.newsapi_verification.top_sources.map((src, i) => (
                          <span key={i} className="newsapi-source-tag">{src}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {result.newsapi_verification.sample_articles && result.newsapi_verification.sample_articles.length > 0 && (
                    <div className="newsapi-articles">
                      <p className="newsapi-sources-label">Related Articles:</p>
                      {result.newsapi_verification.sample_articles.slice(0, 3).map((article, i) => (
                        <a
                          key={i}
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="newsapi-article-link"
                        >
                          <span className="newsapi-article-source">
                            {article.source?.name}
                          </span>
                          <span className="newsapi-article-title">{article.title}</span>
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Signal Breakdown */}
              {result.signal_breakdown.length > 0 && (
                <div className="signals-card">
                  <div className="card-header">
                    <div className="card-icon">🔍</div>
                    <h3 className="card-title">Detected Signals</h3>
                  </div>
                  {result.signal_breakdown.map((signal, index) => (
                    <div key={index} className="signal-item">
                      <div className="signal-header">
                        <span className="signal-type">
                          {signal.signal.startsWith('newsapi_') ? '📰 ' : ''}
                          {signal.signal.replace(/_/g, ' ')}
                        </span>
                        <span className="confidence-badge">
                          {(signal.confidence * 100).toFixed(0)}% Confidence
                        </span>
                      </div>
                      <p className="signal-desc">{signal.description}</p>
                      {Object.keys(signal.evidence).length > 0 && (
                        <div className="signal-evidence">
                          Evidence: {JSON.stringify(signal.evidence)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Recommendation Card */}
              <div className="recommendation-card">
                <div className="card-header">
                  <div className="card-icon">💡</div>
                  <h3 className="card-title">Recommended Action</h3>
                </div>
                <div className="recommendation-action">
                  {result.recommendation.action}
                  <span className={`priority-badge ${result.recommendation.priority.toLowerCase()}`}>
                    {result.recommendation.priority} Priority
                  </span>
                </div>
                <ul className="action-steps">
                  {result.recommendation.suggested_steps.map((step, index) => (
                    <li key={index}>{step}</li>
                  ))}
                </ul>
                {result.recommendation.human_review_required && (
                  <div className="human-review-alert">
                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    Human Review Required
                  </div>
                )}
              </div>

              {/* Disclaimer */}
              <div className="disclaimer-card">
                <div className="disclaimer-text">
                  <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  <span>{result.disclaimer}</span>
                </div>
              </div>

              {/* Back Button */}
              <button className="back-btn" onClick={resetForm}>
                <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Analyze Another File
              </button>
            </div>
          )}
        </div>
      </main>
    </>
  )
}
