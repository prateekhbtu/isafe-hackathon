# MDRS - Multimodal Deception Risk Scorer

<div align="center">

![MDRS Logo](https://img.shields.io/badge/MDRS-AI%20Assisted%20Triage-blueviolet?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Explainable, Probabilistic Media Authenticity Assessment**

[Features](#-features) • [Architecture](#-architecture) • [Setup](#-quick-start) • [Usage](#-usage) • [Ethics](#-ethical-considerations)

</div>

---

## 🎯 Overview

**MDRS (Multimodal Deception Risk Scorer)** is a production-grade web application designed for hackathons and policy demonstrations. It provides **probabilistic risk assessment** for images, videos, audio, and text—**never** making binary "real vs. fake" claims.

### 🌟 Key Principles

- ✅ **Probabilistic, not definitive** - Risk scores (0-100), not verdicts
- ✅ **Explainable** - Every score shows contributing signals
- ✅ **Human-in-the-loop** - Supports decisions, doesn't replace them
- ✅ **Transparent** - Configurable weights, visible logic
- ✅ **Ethical** - No surveillance, no automated takedowns

---

## 🚀 Features

### Core Capabilities

| Modality | Detection Signals | Technology |
|----------|------------------|------------|
| **Image** | Manipulation artifacts, metadata anomalies, compression patterns | PIL + Heuristics |
| **Video** | Facial warping, lighting inconsistencies, temporal anomalies | File analysis + Simulated ML |
| **Audio** | Spectral anomalies, voice synthesis artifacts, phoneme patterns | Signal processing heuristics |
| **Text** | Sensational language, stylometric drift, emotional manipulation | NLP pattern matching |

### Unique Features

1. **Cross-Modal Consistency Checking** (Future: Audio-visual sync, emotion-text alignment)
2. **Risk Triage Categories**: Low / Medium / High with actionable recommendations
3. **Evidence Visualization**: Heatmaps, confidence scores, signal breakdowns
4. **Metadata Contextualization**: Source credibility, timestamp verification

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (Next.js)                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │  Image  │  │  Video  │  │  Audio  │  │   Text  │        │
│  │ Upload  │  │ Upload  │  │ Upload  │  │  Input  │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │              │
│       └────────────┴────────────┴────────────┘              │
│                        │                                     │
│                        ▼                                     │
│             Results Dashboard + Explainability              │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              API Endpoints Layer                      │   │
│  │  /analyze/image  /analyze/video  /analyze/audio      │   │
│  │                 /analyze/text                         │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│                       ▼                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Detection Modules                          │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │    │
│  │  │  Image   │ │  Video   │ │  Audio   │ │  Text  │ │    │
│  │  │ Detector │ │ Detector │ │ Detector │ │Detector│ │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────┘ │    │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │ Signals List                         │
│                       ▼                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          Risk Scoring Engine                          │   │
│  │  • Weighted aggregation                               │   │
│  │  • Threshold categorization (Low/Med/High)           │   │
│  │  • Explanation generation                             │   │
│  │  • Recommendation mapping                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                       │                                      │
│                       ▼                                      │
│             JSON Response with Risk Assessment               │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- FastAPI (Python 3.9+)
- PIL/Pillow for image processing
- Lightweight heuristics (production-ready placeholders for ML models)

**Frontend:**
- Next.js 14 (React + TypeScript)
- Axios for API calls
- Responsive CSS with gradient design

---

## 📦 Quick Start

### Prerequisites

- **Python 3.9+**
- **Node.js 18+**
- **npm** or **yarn**

### Installation

#### 1️⃣ Clone Repository

```bash
cd "/home/prateek/Downloads/isafe hackathon"
```

#### 2️⃣ Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

Backend will run at: **http://localhost:8000**

#### 3️⃣ Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will run at: **http://localhost:3000**

---

## 💻 Usage

### Web Interface

1. Open **http://localhost:3000** in your browser
2. Select a modality tab (Image / Video / Audio / Text)
3. Upload media or paste text
4. **(Optional)** Add metadata: source, timestamp, context
5. Click **"Analyze Media"**
6. View:
   - **Risk Score** (0-100)
   - **Risk Level** (Low / Medium / High)
   - **Signal Breakdown** with confidence scores
   - **Explainable Recommendations**

### API Usage (Direct)

#### Analyze Image

```bash
curl -X POST http://localhost:8000/analyze/image \
  -F "file=@sample.jpg" \
  -F "source=Twitter" \
  -F "timestamp=2026-01-15"
```

#### Analyze Text

```bash
curl -X POST http://localhost:8000/analyze/text \
  -F "text=BREAKING: You won't believe this shocking news!" \
  -F "source=Facebook"
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
  "disclaimer": "This is probabilistic assessment. Human verification essential."
}
```

---

## 🔬 Detection Signals

### Image Detector

| Signal | Description | Method |
|--------|-------------|--------|
| **Manipulation Artifacts** | Unusual dimensions, aspect ratios | Geometric analysis |
| **Compression Anomaly** | Re-encoding patterns | File size vs. resolution |
| **Metadata Inconsistency** | Stripped EXIF data | Metadata parsing |
| **Noise Pattern** | Unnatural noise distribution | Pixel sampling (simulated) |

### Video Detector

| Signal | Description | Production Equivalent |
|--------|-------------|----------------------|
| **Facial Warping** | Deepfake artifacts | ResNet + LSTM |
| **Lighting/Shadow Anomaly** | Inconsistent illumination | Physics-based rendering check |
| **Temporal Inconsistency** | Unnatural frame transitions | Optical flow analysis |
| **Audio-Visual Mismatch** | Lip-sync issues | Cross-modal sync model |

### Audio Detector

| Signal | Description | Production Equivalent |
|--------|-------------|----------------------|
| **Spectral Anomaly** | Unnatural frequency patterns | FFT + ML classifier |
| **Phoneme Inconsistency** | Artificial phoneme transitions | Deep phoneme model |
| **Voice Synthesis Artifact** | TTS/cloning artifacts | WaveNet/Tacotron detector |
| **Background Mismatch** | Environmental audio inconsistency | Scene audio model |

### Text Detector

| Signal | Description | Method |
|--------|-------------|--------|
| **Sensational Language** | Clickbait, hyperbole | Keyword pattern matching |
| **Emotional Manipulation** | Fear, outrage triggers | Sentiment analysis |
| **Stylometric Drift** | Unusual writing patterns | Sentence structure analysis |
| **Source Credibility** | Unknown/unverified sources | Metadata validation |

---

## ⚖️ Ethical Considerations

### Core Commitments

1. **No Binary Claims**: System **never** outputs "This is fake" or "This is real"
2. **Probabilistic Framing**: All scores presented as risk likelihoods, not certainties
3. **Human Agency**: Users always make final decisions
4. **Transparency**: All signal weights and logic are configurable and visible
5. **No Surveillance**: No personal data storage, no tracking

### Limitations (Disclosed to Users)

- ❌ Cannot detect all novel manipulation techniques
- ❌ May produce false positives/negatives
- ❌ Depends on quality of input metadata
- ❌ Heuristics are placeholders (production needs trained models)
- ❌ Adversaries can evade detection by design

### Recommended Usage

✅ **DO:**
- Use for preliminary triage in newsrooms
- Support human fact-checkers
- Provide early warnings for viral content
- Educate users about media literacy

❌ **DON'T:**
- Automatically remove content based on scores
- Use for surveillance or targeting individuals
- Present scores as definitive truth
- Deploy without human oversight

---

## 🛠️ Configuration

### Adjust Risk Weights

Edit `backend/risk_engine.py`:

```python
WEIGHTS = {
    'image': {
        'manipulation_artifacts': 0.35,  # Adjust here
        'metadata_inconsistency': 0.20,
        ...
    }
}
```

### Modify Thresholds

```python
THRESHOLDS = {
    'low': 30,    # 0-30: Low risk
    'medium': 60, # 30-60: Medium risk
    'high': 100   # 60-100: High risk
}
```

---

## 🧪 Testing

### Test with Sample Media

```bash
# Backend API health check
curl http://localhost:8000

# Test text analysis
curl -X POST http://localhost:8000/analyze/text \
  -F "text=This is a normal statement."

# Expected: Low risk score
```

### Production Deployment Checklist

- [ ] Replace heuristics with trained ML models
- [ ] Add rate limiting to API endpoints
- [ ] Implement authentication for production use
- [ ] Set up HTTPS
- [ ] Add comprehensive logging
- [ ] Integrate fact-checking APIs
- [ ] Conduct bias/fairness audits

---

## 📚 Project Structure

```
isafe hackathon/
├── backend/
│   ├── main.py                    # FastAPI server
│   ├── risk_engine.py             # Risk scoring logic
│   ├── requirements.txt           # Python dependencies
│   └── detectors/
│       ├── __init__.py
│       ├── image_detector.py      # Image analysis
│       ├── video_detector.py      # Video analysis
│       ├── audio_detector.py      # Audio analysis
│       └── text_detector.py       # Text analysis
├── frontend/
│   ├── app/
│   │   ├── layout.tsx             # Root layout
│   │   ├── page.tsx               # Main page component
│   │   └── globals.css            # Global styles
│   ├── package.json               # Node dependencies
│   ├── tsconfig.json              # TypeScript config
│   └── next.config.js             # Next.js config
└── README.md                      # This file
```

---

## 🚀 Deployment

### Backend (FastAPI)

**Option 1: Docker**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY backend/ .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Option 2: Cloud (Render, Railway, etc.)**
- Deploy `backend/` folder
- Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Frontend (Next.js)

**Vercel (Recommended):**
```bash
cd frontend
vercel deploy
```

**Manual Build:**
```bash
npm run build
npm start
```

---

## 🤝 Contributing

This is a hackathon prototype. Contributions welcome for:

- Integrating real ML models (ResNet, audio classifiers, etc.)
- Adding cross-modal consistency checks
- Improving UI/UX
- Writing tests
- Enhancing documentation

---

## 📄 License

MIT License - See LICENSE file for details.

---

## 🙏 Acknowledgments

Inspired by:
- VerifEye's explainable detection approach
- Ethical AI frameworks (Partnership on AI, IEEE)
- Misinformation research community

**Built for:** iSafe Hackathon 2026  
**Focus:** Cyber policy, human-centered AI, media literacy

---

## 📞 Support

For questions or issues:
- Create an issue on GitHub
- Contact: [Your Contact Info]

---

<div align="center">

**⚠️ Remember: This tool assists humans, it doesn't replace them. ⚠️**

*"The best defense against misinformation is human judgment informed by transparent technology."*

</div>
