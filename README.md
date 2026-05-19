# MDRS - Multimodal Deception Risk Scorer

<div align="center">

![MDRS Logo](https://img.shields.io/badge/MDRS-Explainable%20Risk%20Scoring-1f6feb?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

Explainable, probabilistic media authenticity assessment for image, video, audio, and text.

[Features](#features) | [Architecture](#architecture) | [Chrome-extension](#chrome-extension) | [Quick-start](#quick-start) | [Usage](#usage) | [Ethical-considerations](#ethical-considerations)

</div>

---

## Overview

MDRS (Multimodal Deception Risk Scorer) delivers probabilistic authenticity risk scores with transparent signals, confidence values, and reviewer guidance. The platform is designed for production usage with a stateless API tier, pluggable detectors, and an optional browser extension for in-context triage on any web page.

Key principles:

- Probabilistic, not definitive: risk scores in the 0-100 range
- Explainable: evidence signals and weighted contributions are visible
- Human-in-the-loop: output is advisory and designed for review workflows
- Transparent: scoring weights and thresholds are configurable
- Privacy-first: no tracking or surveillance logic in the core system

---

## Features

Core capabilities:

- Image: manipulation artifacts, metadata anomalies, compression patterns
- Video: temporal inconsistencies, lighting anomalies, face distortion cues
- Audio: spectral anomalies, synthesis artifacts, phoneme irregularities
- Text: sensational language, stylometric drift, emotional manipulation cues

Operational features:

- Risk triage: Low / Medium / High with structured recommendations
- Evidence breakdown: signal-level confidence and contribution
- URL-based ingestion: audio/video analysis from direct URLs
- Metadata enrichment: optional source and timestamp context
- Extension-first flow: in-browser scanning with a persistent side panel

---

## Architecture

High-level system flow:

```
Client (Next.js UI or API consumer)
        |
        | HTTP REST
        v
FastAPI Gateway
        |
        | Dispatch by modality
        v
Detection Modules (image, video, audio, text)
        |
        | Signals + confidence
        v
Risk Engine
  - weighted aggregation
  - threshold mapping
  - explanation + recommendations
        |
        v
JSON response (risk score, signals, guidance)
```

Backend responsibilities:

- FastAPI endpoints in backend/main.py
- Modality detectors in backend/detectors
- Risk scoring and explanations in backend/risk_engine.py
- URL media ingestion with size/duration constraints in backend/utils/url_handler.py

Frontend responsibilities:

- Multi-modality input experience
- Results dashboard with explainability and signal breakdown
- Optional NewsAPI and Gemini verification panels

Scaling model:

- Stateless API for horizontal scaling
- Media ingestion with bounded size and duration limits
- Pluggable detector modules for model upgrades

---

## Chrome Extension

Architecture overview:

```
Web Page DOM
    |
    | user intent (text selection or media context)
    v
Content Script / Context Menu
    |
    | runtime messaging
    v
Service Worker
    |
    | REST API
    v
MDRS Backend
    |
    v
Side Panel UI (signals, risk score, guidance)
```

Data flow:

- Text: selection -> content script -> service worker -> POST /analyze/text
- Image: context menu -> service worker fetches blob -> POST /analyze/image
- Audio/Video: context menu -> URL passthrough -> POST /analyze/audio or /analyze/video

Permissions model:

- activeTab: user-initiated access to the current page
- contextMenus: media scan actions
- sidePanel: persistent results UI
- storage: API endpoint configuration

Extension file map:

```
chrome-extension/
├── manifest.json          # Manifest V3 configuration
├── background.js          # Service worker: menus, API calls, routing
├── content.js             # Selection detection + UI hooks
├── content.css            # Scan button and notification styles
├── sidepanel.html         # Side panel container
├── sidepanel.css          # Side panel visual system
├── sidepanel.js           # Result rendering pipeline
├── popup.html             # Toolbar popup
├── popup.css              # Popup styles
├── popup.js               # API URL config + health check
└── icons/
```

---

## External Verification APIs

NewsAPI.org credibility check:

- Integrates via backend/newsapi_client.py
- Cross-references extracted claim queries against NewsAPI.org
- Returns credibility score, sources, and sample articles
- Optional and disabled when NEWSAPI_KEY is not configured

Gemini verification (optional):

- Integrates via backend/gemini_client.py
- Adds model-based verification and additional risk factor synthesis
- Controlled by GEMINI_API_URL health endpoint

---

## Quick Start

Prerequisites:

- Python 3.9+
- Node.js 18+
- npm or yarn

### Backend

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

pip install -r requirements.txt

python main.py
```

API server: http://localhost:8000

### Frontend

```bash
cd frontend

npm install
npm run dev
```

Web app: http://localhost:3000

### Chrome Extension (optional)

1. Open chrome://extensions
2. Enable Developer mode
3. Click Load unpacked and select chrome-extension
4. Pin the extension and use it on any content page

---

## Usage

### Web Interface

1. Open http://localhost:3000
2. Select Image, Video, Audio, or Text
3. Upload media or provide a direct URL (audio/video)
4. Add optional metadata (source, timestamp)
5. Click Analyze Media
6. Review score, signals, and recommendations

### API Examples

Analyze image:

```bash
curl -X POST http://localhost:8000/analyze/image \
  -F "file=@sample.jpg" \
  -F "source=Twitter" \
  -F "timestamp=2026-01-15"
```

Analyze text:

```bash
curl -X POST http://localhost:8000/analyze/text \
  -F "text=BREAKING: You won't believe this shocking news!" \
  -F "source=Facebook"
```

Analyze audio by URL:

```bash
curl -X POST http://localhost:8000/analyze/audio \
  -F "url=https://example.com/sample.mp3" \
  -F "source=Podcast"
```

Analyze video by URL:

```bash
curl -X POST http://localhost:8000/analyze/video \
  -F "url=https://example.com/sample.mp4" \
  -F "source=News Clip"
```

### Response Format

```json
{
  "risk_score": 68,
  "risk_level": "High",
  "modality": "image",
  "signals_detected": 3,
  "signal_breakdown": [
    {
      "signal": "manipulation_artifacts",
      "description": "Unusual aspect ratio detected",
      "confidence": 0.45,
      "contribution": 15.75,
      "evidence": { "aspect_ratio": 3.2 }
    }
  ],
  "explanation": "Risk score of 68/100 calculated from 3 signals...",
  "recommendation": {
    "action": "Human Verification Advised",
    "priority": "Medium",
    "suggested_steps": ["Manual review recommended", "Verify source..."],
    "human_review_required": true
  },
  "disclaimer": "This is a probabilistic assessment. Human verification remains essential."
}
```

---

## Detection Signals

Image detector signals:

- Manipulation artifacts: unusual geometry or aspect ratios
- Compression anomaly: re-encoding patterns vs. resolution
- Metadata inconsistency: missing or conflicting EXIF
- Noise pattern: statistical noise irregularities

Video detector signals:

- Facial warping cues
- Lighting and shadow inconsistencies
- Temporal discontinuities across frames
- Audio-visual mismatch indicators

Audio detector signals:

- Spectral anomalies and unnatural frequency patterns
- Phoneme consistency deviations
- Voice synthesis artifacts
- Background audio mismatches

Text detector signals:

- Sensational or manipulative language markers
- Sentiment volatility and emotional triggering
- Stylometric drift vs. expected writing patterns
- Source credibility indicators

---

## Ethical Considerations

Core commitments:

- No binary claims: the system does not declare "real" or "fake"
- Probabilistic framing: risk is presented with uncertainty
- Human agency: reviewers make final decisions
- Transparency: weights and thresholds are configurable
- Privacy-first: no personal data storage or tracking

Operational limits:

- This system cannot detect all manipulation techniques
- False positives and negatives are possible
- Metadata quality affects accuracy
- Current detectors use baseline heuristics; production deployments should integrate trained models

---

## Configuration

Environment variables:

- NEWSAPI_KEY: enable NewsAPI.org credibility checks
- GEMINI_API_URL: optional Gemini verification endpoint
- ALLOWED_ORIGINS: comma-separated CORS allowlist for the API

Adjust risk weights in backend/risk_engine.py:

```python
WEIGHTS = {
    "image": {
        "manipulation_artifacts": 0.35,
        "metadata_inconsistency": 0.20,
        # ...
    }
}
```

Modify risk thresholds:

```python
THRESHOLDS = {
    "low": 30,
    "medium": 60,
    "high": 100
}
```

Media ingestion limits (backend/utils/url_handler.py):

- Max download size: 100 MB
- Max media duration: 300 seconds
- Sampling window: first 20 seconds
- YouTube URLs require yt-dlp installed

---

## Testing

Basic API health check:

```bash
curl http://localhost:8000
```

Sample text analysis:

```bash
curl -X POST http://localhost:8000/analyze/text \
  -F "text=This is a normal statement."
```

---

## Project Structure

```
isafe-hackathon/
├── backend/
│   ├── main.py                    # FastAPI server
│   ├── risk_engine.py             # Risk scoring logic
│   ├── requirements.txt           # Python dependencies
│   ├── detectors/                 # Modality detectors
│   └── utils/                     # URL handling and helpers
├── chrome-extension/              # Browser extension
├── frontend/                      # Next.js app
│   ├── app/                       # UI pages and layout
│   ├── package.json               # Node dependencies
│   ├── tsconfig.json              # TypeScript config
│   └── next.config.js             # Next.js config
├── test_api.py                    # API smoke test
└── README.md                      # This file
```

---

## Deployment

### Backend (FastAPI)

Docker:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY backend/ .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Cloud (Render, Railway, etc.):

- Deploy backend/
- Start command: uvicorn main:app --host 0.0.0.0 --port $PORT

### Frontend (Next.js)

```bash
npm run build
npm start
```

---

## Contributing

Contributions welcome for:

- Integrating trained ML models
- Adding cross-modal consistency checks
- Improving UI/UX and accessibility
- Writing tests and benchmarking
- Expanding verification integrations

---

## License

MIT License - See LICENSE file for details.

---

## Support

Create an issue on GitHub for questions or bugs.
