"""Extract video poster frames with ffmpeg and upload to R2."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException

from app.core.config import get_settings
from app.services import r2_service

THUMBNAIL_LABELS = ("Opening frame", "Mid-scene", "Highlight moment")
THUMBNAIL_FRACTIONS = (0.08, 0.42, 0.72)
MIN_OFFSET_SECONDS = 0.5
MAX_VIDEO_BYTES = 50 * 1024 * 1024
DOWNLOAD_TIMEOUT = 120.0


@dataclass
class ThumbnailOption:
    url: str
    label: str
    offset_seconds: float


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def _allowed_video_url(url: str) -> bool:
    cleaned = (url or "").strip()
    if not cleaned.startswith(("http://", "https://")):
        return False
    settings = get_settings()
    base = settings.r2_public_base_url.rstrip("/")
    if cleaned.startswith(base + "/") or cleaned == base:
        return True
    parsed = urlparse(cleaned)
    base_parsed = urlparse(base)
    return parsed.netloc == base_parsed.netloc


def _probe_duration_seconds(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=422, detail="Could not read video duration.")
    try:
        return max(float((result.stdout or "").strip()), 0.1)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Could not read video duration.") from exc


def _extract_frame_jpeg(path: Path, offset_seconds: float) -> bytes:
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{offset_seconds:.3f}",
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            "-f",
            "image2pipe",
            "-vcodec",
            "mjpeg",
            "pipe:1",
        ],
        capture_output=True,
        check=False,
        timeout=90,
    )
    if result.returncode != 0 or not result.stdout:
        stderr = (result.stderr or b"").decode("utf-8", errors="replace")[:200]
        raise HTTPException(status_code=422, detail=f"Could not extract frame: {stderr or 'ffmpeg failed'}")
    return result.stdout


def _pick_offsets(duration: float) -> list[float]:
    offsets: list[float] = []
    for fraction in THUMBNAIL_FRACTIONS:
        offset = max(MIN_OFFSET_SECONDS, duration * fraction)
        if duration > MIN_OFFSET_SECONDS * 2:
            offset = min(offset, max(duration - MIN_OFFSET_SECONDS, MIN_OFFSET_SECONDS))
        rounded = round(offset, 2)
        if rounded not in offsets:
            offsets.append(rounded)
    if not offsets:
        offsets = [MIN_OFFSET_SECONDS]
    return offsets[:3]


def _download_video(url: str, dest: Path) -> None:
    try:
        with httpx.stream("GET", url, follow_redirects=True, timeout=DOWNLOAD_TIMEOUT) as response:
            response.raise_for_status()
            length = response.headers.get("content-length")
            if length and int(length) > MAX_VIDEO_BYTES:
                raise HTTPException(status_code=400, detail="Video file is too large for thumbnail generation.")
            size = 0
            with dest.open("wb") as handle:
                for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                    size += len(chunk)
                    if size > MAX_VIDEO_BYTES:
                        raise HTTPException(status_code=400, detail="Video file is too large for thumbnail generation.")
                    handle.write(chunk)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Could not download video: {exc}") from exc
    if not dest.exists() or dest.stat().st_size == 0:
        raise HTTPException(status_code=422, detail="Downloaded video file is empty.")


def generate_thumbnail_options(video_url: str) -> list[ThumbnailOption]:
    if not r2_service.r2_configured():
        raise HTTPException(status_code=503, detail="Cloudflare R2 is not configured.")
    if not ffmpeg_available():
        raise HTTPException(
            status_code=503,
            detail="ffmpeg is not installed on the server. Rebuild the backend Docker image.",
        )
    cleaned = video_url.strip()
    if not _allowed_video_url(cleaned):
        raise HTTPException(status_code=400, detail="Video URL must be hosted on your R2 bucket.")

    suffix = Path(urlparse(cleaned).path).suffix.lower() or ".mp4"
    with tempfile.TemporaryDirectory(prefix="video-thumb-") as tmp:
        video_path = Path(tmp) / f"source{suffix}"
        _download_video(cleaned, video_path)
        duration = _probe_duration_seconds(video_path)
        offsets = _pick_offsets(duration)

        options: list[ThumbnailOption] = []
        for index, offset in enumerate(offsets):
            jpeg = _extract_frame_jpeg(video_path, offset)
            url = r2_service.upload_image_bytes(jpeg, folder="media/thumbnails", content_type="image/jpeg")
            label = THUMBNAIL_LABELS[index] if index < len(THUMBNAIL_LABELS) else f"Frame at {offset:.1f}s"
            options.append(ThumbnailOption(url=url, label=label, offset_seconds=offset))
        return options
