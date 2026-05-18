"""
URL Media Handler
Handles URL-based media ingestion for audio and video.
Supports:
  - Direct media URLs (.mp4, .mp3, .wav, .mov)
  - YouTube URLs (via yt-dlp metadata extraction)
  - Streaming downloads with size limits
  - FFmpeg sampling (first 15-20 seconds only)
  - Automatic temp file cleanup

Optimized for Render Free Tier:
  - No full downloads of large media
  - Strict size/duration limits
  - Temporary file handling in /tmp
  - Timeout protection
"""
import os
import re
import json
import shutil
import tempfile
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse

import httpx


# ── Limits ───────────────────────────────────────────────────────────
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_DURATION_SECONDS = 300              # 5 minutes
SAMPLE_DURATION_SECONDS = 20            # Only process first 20s
STREAM_CHUNK_SIZE = 64 * 1024           # 64 KB chunks
DOWNLOAD_TIMEOUT = 60.0                 # seconds
FFMPEG_TIMEOUT = 30                     # seconds for ffmpeg/ffprobe

YOUTUBE_PATTERNS = [
    r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=",
    r"(?:https?://)?youtu\.be/",
    r"(?:https?://)?(?:www\.)?youtube\.com/shorts/",
    r"(?:https?://)?(?:www\.)?youtube\.com/embed/",
]

AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm"}


def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube link."""
    return any(re.match(pattern, url) for pattern in YOUTUBE_PATTERNS)


def _check_tool_available(tool: str) -> bool:
    """Check if a CLI tool is available on the system."""
    return shutil.which(tool) is not None


def _detect_media_type_from_url(url: str) -> Optional[str]:
    """
    Detect if URL points to audio or video based on extension.
    Returns 'audio', 'video', or None.
    """
    parsed = urlparse(url)
    path_lower = parsed.path.lower()
    ext = Path(path_lower).suffix

    if ext in AUDIO_EXTENSIONS:
        return "audio"
    elif ext in VIDEO_EXTENSIONS:
        return "video"
    return None


async def stream_download_media(
    url: str, expected_type: str, max_bytes: int = MAX_DOWNLOAD_BYTES
) -> Tuple[str, Dict[str, Any]]:
    """
    Stream-download media from a direct URL with size limits.
    Does NOT fully download — stops after max_bytes.

    Args:
        url: Direct media URL
        expected_type: 'audio' or 'video'
        max_bytes: Maximum bytes to download

    Returns:
        Tuple of (temp_file_path, metadata_dict)

    Raises:
        ValueError: If URL is invalid or media too large
    """
    parsed = urlparse(url)
    ext = Path(parsed.path).suffix.lower()

    # Default extension if none detected
    if expected_type == "audio" and ext not in AUDIO_EXTENSIONS:
        ext = ".mp3"
    elif expected_type == "video" and ext not in VIDEO_EXTENSIONS:
        ext = ".mp4"

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp_path = tmp_file.name
    downloaded = 0
    content_type = ""

    try:
        async with httpx.AsyncClient(
            timeout=DOWNLOAD_TIMEOUT, follow_redirects=True
        ) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()

                content_type = (
                    response.headers.get("content-type", "").split(";")[0].strip()
                )

                # Check content-length header for early rejection
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > max_bytes:
                    tmp_file.close()
                    os.unlink(tmp_path)
                    raise ValueError(
                        f"Media too large: {int(content_length) / (1024*1024):.1f} MB "
                        f"(limit: {max_bytes / (1024*1024):.0f} MB)"
                    )

                async for chunk in response.aiter_bytes(STREAM_CHUNK_SIZE):
                    downloaded += len(chunk)
                    if downloaded > max_bytes:
                        tmp_file.close()
                        os.unlink(tmp_path)
                        raise ValueError(
                            f"Media exceeds size limit of {max_bytes / (1024*1024):.0f} MB"
                        )
                    tmp_file.write(chunk)

        tmp_file.close()

        metadata = {
            "source_url": url,
            "content_type": content_type,
            "file_size_bytes": downloaded,
            "file_size_mb": round(downloaded / (1024 * 1024), 2),
            "extension": ext,
        }

        return tmp_path, metadata

    except httpx.HTTPError as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise ValueError(f"Failed to download media: {str(e)}")
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


async def extract_youtube_stream(
    url: str, media_type: str = "audio"
) -> Tuple[str, Dict[str, Any]]:
    """
    Use yt-dlp to extract and download the smallest quality stream from YouTube.
    Does NOT download full quality — selects worst/smallest format.

    Args:
        url: YouTube URL
        media_type: 'audio' or 'video'

    Returns:
        Tuple of (temp_file_path, metadata_dict)

    Raises:
        ValueError: If yt-dlp fails or is unavailable
    """
    if not _check_tool_available("yt-dlp"):
        raise ValueError(
            "yt-dlp is not installed. YouTube URL support requires yt-dlp."
        )

    # Step 1: Extract metadata with yt-dlp -J (no download)
    try:
        info_proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                "yt-dlp",
                "-J",
                "--no-warnings",
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=FFMPEG_TIMEOUT,
        )
        stdout, stderr = await info_proc.communicate()

        if info_proc.returncode != 0:
            raise ValueError(
                f"yt-dlp metadata extraction failed: {stderr.decode()[:200]}"
            )

        info = json.loads(stdout.decode())
        duration = info.get("duration", 0)
        title = info.get("title", "Unknown")

        if duration and duration > MAX_DURATION_SECONDS:
            raise ValueError(
                f"Video too long: {duration}s (limit: {MAX_DURATION_SECONDS}s). "
                f"Only media up to {MAX_DURATION_SECONDS // 60} minutes is supported."
            )

    except asyncio.TimeoutError:
        raise ValueError("yt-dlp metadata extraction timed out")
    except json.JSONDecodeError:
        raise ValueError("Failed to parse yt-dlp metadata output")

    # Step 2: Download smallest format
    ext = ".wav" if media_type == "audio" else ".mp4"
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp_path = tmp_file.name
    tmp_file.close()

    try:
        if media_type == "audio":
            # Audio only, worst quality
            format_args = ["-f", "worstaudio", "-x", "--audio-format", "wav"]
        else:
            # Video, worst quality (144p or smallest)
            format_args = ["-f", "worstvideo+worstaudio/worst"]

        dl_proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                "yt-dlp",
                *format_args,
                "-o",
                tmp_path,
                "--no-warnings",
                "--no-playlist",
                "--max-filesize",
                f"{MAX_DOWNLOAD_BYTES}",
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=120,  # YouTube downloads can be slower
        )
        stdout, stderr = await dl_proc.communicate()

        if dl_proc.returncode != 0:
            raise ValueError(f"yt-dlp download failed: {stderr.decode()[:200]}")

        # yt-dlp may change the extension; find the actual file
        actual_path = tmp_path
        if not os.path.exists(actual_path):
            # Check with different extensions
            base = os.path.splitext(tmp_path)[0]
            for try_ext in [".wav", ".mp3", ".m4a", ".mp4", ".webm", ".mkv"]:
                candidate = base + try_ext
                if os.path.exists(candidate):
                    actual_path = candidate
                    break

        if not os.path.exists(actual_path):
            raise ValueError("yt-dlp download produced no output file")

        file_size = os.path.getsize(actual_path)
        metadata = {
            "source_url": url,
            "source_type": "youtube",
            "title": title,
            "duration_seconds": duration,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
        }

        return actual_path, metadata

    except asyncio.TimeoutError:
        cleanup_temp_file(tmp_path)
        raise ValueError("yt-dlp download timed out")
    except Exception:
        cleanup_temp_file(tmp_path)
        raise


async def ffmpeg_sample_media(
    input_path: str,
    media_type: str,
    duration: int = SAMPLE_DURATION_SECONDS,
) -> str:
    """
    Use ffmpeg to extract a sample from media (first N seconds).
    This avoids processing full-length media on Render free tier.

    Args:
        input_path: Path to input media file
        media_type: 'audio' or 'video'
        duration: Seconds to sample

    Returns:
        Path to sampled output file
    """
    if not _check_tool_available("ffmpeg"):
        # If ffmpeg is not available, return the original file
        return input_path

    ext = ".wav" if media_type == "audio" else ".mp4"
    tmp_output = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    output_path = tmp_output.name
    tmp_output.close()

    try:
        if media_type == "audio":
            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-t", str(duration),
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "-y",
                output_path,
            ]
        else:
            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-t", str(duration),
                "-vf", "fps=1,scale=320:-2",
                "-an",
                "-y",
                output_path,
            ]

        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=FFMPEG_TIMEOUT,
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            # Fallback: return original file
            cleanup_temp_file(output_path)
            return input_path

        return output_path

    except asyncio.TimeoutError:
        cleanup_temp_file(output_path)
        return input_path
    except Exception:
        cleanup_temp_file(output_path)
        return input_path


async def get_media_duration(file_path: str) -> Optional[float]:
    """
    Use ffprobe to get media duration in seconds.

    Args:
        file_path: Path to media file

    Returns:
        Duration in seconds, or None if ffprobe unavailable
    """
    if not _check_tool_available("ffprobe"):
        return None

    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=FFMPEG_TIMEOUT,
        )
        stdout, _ = await proc.communicate()

        if proc.returncode == 0:
            data = json.loads(stdout.decode())
            duration_str = data.get("format", {}).get("duration")
            if duration_str:
                return float(duration_str)

    except (asyncio.TimeoutError, json.JSONDecodeError, ValueError):
        pass

    return None


def cleanup_temp_file(file_path: Optional[str]) -> None:
    """Safely remove a temporary file."""
    if file_path and os.path.exists(file_path):
        try:
            os.unlink(file_path)
        except OSError:
            pass


def cleanup_temp_files(*paths: Optional[str]) -> None:
    """Safely remove multiple temporary files."""
    for path in paths:
        cleanup_temp_file(path)
