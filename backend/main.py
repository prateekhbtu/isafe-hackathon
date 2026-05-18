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
from newsapi_client import newsapi_client
from utils.url_handler import (
    is_youtube_url,
    stream_download_media,
    extract_youtube_stream,
    ffmpeg_sample_media,
    get_media_duration,
    cleanup_temp_files,
    MAX_DURATION_SECONDS,
)

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


def _validate_url(url: str) -> None:
    """
    Validate URL with SSRF protection.
    Raises HTTPException on invalid/dangerous URLs.
    """
    parsed = urlparse(url)

    # Block dangerous protocols
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(
            status_code=400,
            detail="URL must start with http:// or https://"
        )
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL must include a valid host.")
    if parsed.username or parsed.password:
        raise HTTPException(
            status_code=400, detail="URL must not include credentials."
        )

    # Block internal/private hosts
    hostname = parsed.hostname.lower()
    blocked_hosts = {
        "localhost", "0.0.0.0", "metadata.google.internal",
        "169.254.169.254",  # AWS/GCP metadata
    }
    if hostname in blocked_hosts:
        raise HTTPException(status_code=400, detail="URL host is not allowed.")

    if _is_disallowed_host(parsed.hostname):
        raise HTTPException(status_code=400, detail="URL host is not allowed.")


async def _resolve_media_url(
    url: str, media_type: str
) -> tuple[str, dict]:
    """
    Resolve a media URL to a local temp file.
    Handles both direct media URLs and YouTube URLs.

    Args:
        url: The media URL
        media_type: 'audio' or 'video'

    Returns:
        Tuple of (temp_file_path, url_metadata)
    """
    _validate_url(url)

    temp_paths = []  # Track all temp files for cleanup on error

    try:
        if is_youtube_url(url):
            # YouTube: use yt-dlp
            raw_path, url_meta = await extract_youtube_stream(url, media_type)
            temp_paths.append(raw_path)
        else:
            # Direct URL: stream download
            raw_path, url_meta = await stream_download_media(url, media_type)
            temp_paths.append(raw_path)

        # Check duration with ffprobe if available
        duration = await get_media_duration(raw_path)
        if duration and duration > MAX_DURATION_SECONDS:
            cleanup_temp_files(*temp_paths)
            raise HTTPException(
                status_code=400,
                detail=f"Media duration ({int(duration)}s) exceeds limit "
                       f"({MAX_DURATION_SECONDS}s)."
            )

        # Sample with ffmpeg (first 20 seconds only)
        sampled_path = await ffmpeg_sample_media(raw_path, media_type)
        if sampled_path != raw_path:
            temp_paths.append(sampled_path)
            # We can clean up the raw file now
            cleanup_temp_files(raw_path)
            temp_paths.remove(raw_path)
            return sampled_path, url_meta
        else:
            return raw_path, url_meta

    except HTTPException:
        cleanup_temp_files(*temp_paths)
        raise
    except ValueError as e:
        cleanup_temp_files(*temp_paths)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        cleanup_temp_files(*temp_paths)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process media URL: {str(e)}"
        )


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
        "version": "1.1.0",
        "features": {
            "url_ingestion": True,
            "youtube_support": True,
            "newsapi_verification": newsapi_client.is_available(),
            "gemini_ai": True,
        },
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
    Now also cross-references with NewsAPI if context is provided.
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
            
            # NewsAPI: cross-reference image context if provided
            newsapi_result = None
            if context and newsapi_client.is_available():
                try:
                    newsapi_result = await newsapi_client.verify_claim(context)
                except Exception as e:
                    print(f"NewsAPI image context check error: {e}")

            # Calculate risk score (async)
            result = await risk_engine.calculate_risk(
                modality='image',
                signals=signals,
                metadata={'source': source, 'timestamp': timestamp, 'context': context},
                newsapi_result=newsapi_result,
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
    Analyze a video for deception risk signals.
    
    Accepts EITHER a file upload OR a URL (direct media link or YouTube).
    Checks for facial artifacts, lighting inconsistencies, and temporal anomalies.
    """
    tmp_path = None
    url_meta = None

    try:
        if file and url:
            raise HTTPException(status_code=400, detail="Provide either a video file or URL, not both.")

        if url:
            tmp_path, url_meta = await _resolve_media_url(url, "video")
        elif file:
            if not file.content_type or not file.content_type.startswith('video/'):
                raise HTTPException(status_code=400, detail="Invalid file type. Expected video.")
            tmp_path = await _save_upload_file(file)
        else:
            raise HTTPException(status_code=400, detail="Provide a video file or URL.")
        
        try:
            # Run detection
            signals = video_detector.detect(tmp_path, {
                'source': source or (url_meta.get('source_url') if url_meta else None),
                'timestamp': timestamp,
                'context': context
            })
            
            # Calculate risk score (async)
            result = await risk_engine.calculate_risk(
                modality='video',
                signals=signals,
                metadata={
                    'source': source,
                    'timestamp': timestamp,
                    'context': context,
                    'url_metadata': url_meta,
                }
            )

            # Add URL metadata to result if applicable
            if url_meta:
                result['url_metadata'] = {
                    'source_url': url_meta.get('source_url'),
                    'source_type': url_meta.get('source_type', 'direct'),
                    'title': url_meta.get('title'),
                    'file_size_mb': url_meta.get('file_size_mb'),
                }
            
            return JSONResponse(content=result)
        
        finally:
            # Cleanup
            if tmp_path:
                cleanup_temp_files(tmp_path)
    
    except HTTPException:
        raise
    except Exception as e:
        if tmp_path:
            cleanup_temp_files(tmp_path)
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
    Analyze an audio file for deception risk signals.
    
    Accepts EITHER a file upload OR a URL (direct media link or YouTube).
    Checks for spectral anomalies, voice synthesis artifacts, and phoneme inconsistencies.
    """
    tmp_path = None
    url_meta = None

    try:
        if file and url:
            raise HTTPException(status_code=400, detail="Provide either an audio file or URL, not both.")

        if url:
            tmp_path, url_meta = await _resolve_media_url(url, "audio")
        elif file:
            if not file.content_type or not file.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail="Invalid file type. Expected audio.")
            tmp_path = await _save_upload_file(file)
        else:
            raise HTTPException(status_code=400, detail="Provide an audio file or URL.")
        
        try:
            # Run detection
            signals = audio_detector.detect(tmp_path, {
                'source': source or (url_meta.get('source_url') if url_meta else None),
                'timestamp': timestamp,
                'context': context
            })
            
            # Calculate risk score (async)
            result = await risk_engine.calculate_risk(
                modality='audio',
                signals=signals,
                metadata={
                    'source': source,
                    'timestamp': timestamp,
                    'context': context,
                    'url_metadata': url_meta,
                }
            )

            # Add URL metadata to result if applicable
            if url_meta:
                result['url_metadata'] = {
                    'source_url': url_meta.get('source_url'),
                    'source_type': url_meta.get('source_type', 'direct'),
                    'title': url_meta.get('title'),
                    'file_size_mb': url_meta.get('file_size_mb'),
                }
            
            return JSONResponse(content=result)
        
        finally:
            # Cleanup
            if tmp_path:
                cleanup_temp_files(tmp_path)
    
    except HTTPException:
        raise
    except Exception as e:
        if tmp_path:
            cleanup_temp_files(tmp_path)
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
    Now also cross-references claims against NewsAPI news sources.
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

        # NewsAPI: cross-reference text claims against news sources
        newsapi_result = None
        if newsapi_client.is_available():
            try:
                newsapi_result = await newsapi_client.verify_claim(text)
            except Exception as e:
                print(f"NewsAPI text verification error: {e}")
        
        # Calculate risk score (async)
        result = await risk_engine.calculate_risk(
            modality='text',
            signals=signals,
            metadata={'source': source, 'timestamp': timestamp, 'context': context},
            newsapi_result=newsapi_result,
        )
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
