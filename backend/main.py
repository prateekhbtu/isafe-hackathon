"""
MDRS Backend - Multimodal Deception Risk Scorer
FastAPI server for analyzing media and providing risk scores
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import httpx
import ipaddress
import socket

from risk_engine import RiskScoringEngine
from detectors.image_detector import ImageDetector
from detectors.video_detector import VideoDetector
from detectors.audio_detector import AudioDetector
from detectors.text_detector import TextDetector

app = FastAPI(
    title="MDRS API",
    description="Multimodal Deception Risk Scorer - Explainable Risk Assessment for Media",
    version="1.0.0"
)

# CORS configuration
# Get allowed origins from environment variable or use defaults
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,https://abc.pages.dev"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize detectors and risk engine
image_detector = ImageDetector()
video_detector = VideoDetector()
audio_detector = AudioDetector()
text_detector = TextDetector()
risk_engine = RiskScoringEngine()

AUDIO_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.ogg', '.flac'}
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.mov', '.avi', '.webm'}


async def _save_upload_file(file: UploadFile) -> str:
    suffix = Path(file.filename).suffix if file.filename else ''
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        return tmp_file.name


def _is_disallowed_host(hostname: str) -> bool:
    try:
        ip = ipaddress.ip_address(hostname)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        try:
            resolved = socket.getaddrinfo(hostname, None)
        except socket.gaierror:
            return True

        for entry in resolved:
            ip = ipaddress.ip_address(entry[4][0])
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                return True

    return False


async def _download_media_url(
    url: str,
    expected_prefix: str,
    allowed_extensions: set[str],
    default_extension: str
) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL must include a valid host.")
    if parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail="URL must not include credentials.")
    if _is_disallowed_host(parsed.hostname):
        raise HTTPException(status_code=400, detail="URL host is not allowed.")

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=400, detail=f"Unable to fetch media from URL: {str(exc)}")

    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
    url_suffix = Path(parsed.path).suffix.lower()

    if content_type:
        if not content_type.startswith(expected_prefix):
            raise HTTPException(status_code=400, detail=f"Invalid media type. Expected {expected_prefix} content.")
    elif not url_suffix or url_suffix not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unable to determine media type from URL.")

    if not response.content:
        raise HTTPException(status_code=400, detail="Media URL returned empty content.")

    safe_suffix = default_extension if default_extension in allowed_extensions else ''

    with tempfile.NamedTemporaryFile(delete=False, suffix=safe_suffix) as tmp_file:
        tmp_file.write(response.content)
        return tmp_file.name


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "operational",
        "service": "MDRS Backend",
        "version": "1.0.0",
        "disclaimer": "This system provides probabilistic risk assessment and does not determine truth."
    }


@app.post("/analyze/image")
async def analyze_image(
    file: UploadFile = File(...),
    source: Optional[str] = Form(None),
    timestamp: Optional[str] = Form(None),
    context: Optional[str] = Form(None)
):
    """
    Analyze an uploaded image for deception risk signals.
    
    Returns risk score, signals, and explainable recommendations.
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid file type. Expected image.")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Run detection
            signals = image_detector.detect(tmp_path, {
                'source': source,
                'timestamp': timestamp,
                'context': context
            })
            
            # Calculate risk score (async)
            result = await risk_engine.calculate_risk(
                modality='image',
                signals=signals,
                metadata={'source': source, 'timestamp': timestamp, 'context': context}
            )
            
            return JSONResponse(content=result)
        
        finally:
            # Cleanup
            os.unlink(tmp_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyze/video")
async def analyze_video(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    timestamp: Optional[str] = Form(None),
    context: Optional[str] = Form(None)
):
    """
    Analyze an uploaded video for deception risk signals.
    
    Checks for facial artifacts, lighting inconsistencies, and temporal anomalies.
    """
    try:
        if file and url:
            raise HTTPException(status_code=400, detail="Provide either a video file or URL, not both.")

        if url:
            tmp_path = await _download_media_url(url, "video/", VIDEO_EXTENSIONS, ".mp4")
        elif file:
            if not file.content_type or not file.content_type.startswith('video/'):
                raise HTTPException(status_code=400, detail="Invalid file type. Expected video.")
            tmp_path = await _save_upload_file(file)
        else:
            raise HTTPException(status_code=400, detail="Provide a video file or URL.")
        
        try:
            # Run detection
            signals = video_detector.detect(tmp_path, {
                'source': source,
                'timestamp': timestamp,
                'context': context
            })
            
            # Calculate risk score (async)
            result = await risk_engine.calculate_risk(
                modality='video',
                signals=signals,
                metadata={'source': source, 'timestamp': timestamp, 'context': context}
            )
            
            return JSONResponse(content=result)
        
        finally:
            # Cleanup
            os.unlink(tmp_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyze/audio")
async def analyze_audio(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    timestamp: Optional[str] = Form(None),
    context: Optional[str] = Form(None)
):
    """
    Analyze an uploaded audio file for deception risk signals.
    
    Checks for spectral anomalies, voice synthesis artifacts, and phoneme inconsistencies.
    """
    try:
        if file and url:
            raise HTTPException(status_code=400, detail="Provide either an audio file or URL, not both.")

        if url:
            tmp_path = await _download_media_url(url, "audio/", AUDIO_EXTENSIONS, ".mp3")
        elif file:
            if not file.content_type or not file.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail="Invalid file type. Expected audio.")
            tmp_path = await _save_upload_file(file)
        else:
            raise HTTPException(status_code=400, detail="Provide an audio file or URL.")
        
        try:
            # Run detection
            signals = audio_detector.detect(tmp_path, {
                'source': source,
                'timestamp': timestamp,
                'context': context
            })
            
            # Calculate risk score (async)
            result = await risk_engine.calculate_risk(
                modality='audio',
                signals=signals,
                metadata={'source': source, 'timestamp': timestamp, 'context': context}
            )
            
            return JSONResponse(content=result)
        
        finally:
            # Cleanup
            os.unlink(tmp_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyze/text")
async def analyze_text(
    text: str = Form(...),
    source: Optional[str] = Form(None),
    timestamp: Optional[str] = Form(None),
    context: Optional[str] = Form(None)
):
    """
    Analyze text content for deception risk signals.
    
    Checks for sensational language, stylometric anomalies, and misinformation patterns.
    """
    try:
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text content cannot be empty.")
        
        # Run detection
        signals = text_detector.detect(text, {
            'source': source,
            'timestamp': timestamp,
            'context': context
        })
        
        # Calculate risk score (async)
        result = await risk_engine.calculate_risk(
            modality='text',
            signals=signals,
            metadata={'source': source, 'timestamp': timestamp, 'context': context}
        )
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
