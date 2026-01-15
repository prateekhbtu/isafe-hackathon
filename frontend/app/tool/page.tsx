'use client'

import { useState } from 'react'
import Link from 'next/link'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

type Modality = 'image' | 'video' | 'audio' | 'text'

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

export default function ToolPage() {
  const [activeTab, setActiveTab] = useState<Modality>('image')
  const [file, setFile] = useState<File | null>(null)
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
      setError(null)
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
    setTextContent('')
    setSource('')
    setTimestamp('')
    setContext('')
    setResult(null)
    setError(null)
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
                  Upload content to assess deception risk with explainable AI
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
                    disabled={loading || (activeTab === 'text' ? !textContent.trim() : !file)}
                  >
                    {loading ? (
                      <>
                        <div className="loading-spinner" />
                        Analyzing...
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
                  <p className="explanation-text">{result.gemini_analysis}</p>
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
                        <span className="signal-type">{signal.signal.replace(/_/g, ' ')}</span>
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
