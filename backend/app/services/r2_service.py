import uuid
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, UploadFile

from app.core.config import get_settings

IMAGE_CONTENT_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}
VIDEO_CONTENT_TYPES: dict[str, str] = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_VIDEO_BYTES = 100 * 1024 * 1024
MAX_DOCUMENT_BYTES = 25 * 1024 * 1024
PDF_CONTENT_TYPES: dict[str, str] = {
    "application/pdf": ".pdf",
}


def r2_configured() -> bool:
    settings = get_settings()
    return bool(
        settings.r2_bucket_name
        and settings.r2_s3_endpoint_url
        and settings.r2_access_key_id
        and settings.r2_secret_access_key
        and settings.r2_public_base_url
    )


def _s3_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_s3_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def public_url(key: str) -> str:
    base = get_settings().r2_public_base_url.rstrip("/")
    return f"{base}/{key.lstrip('/')}"


def _extension(content_type: str, filename: str | None, default_ext: str) -> str:
    if filename:
        suffix = Path(filename).suffix.lower()
        if suffix:
            return suffix
    return default_ext


def _safe_folder(folder: str) -> str:
    cleaned = "".join(ch for ch in folder.strip().lower() if ch.isalnum() or ch in "-_")
    return cleaned or "cms"


async def _read_file(file: UploadFile, max_bytes: int) -> tuple[bytes, str]:
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")
    if len(data) > max_bytes:
        limit_mb = max_bytes // (1024 * 1024)
        raise HTTPException(status_code=400, detail=f"File too large (max {limit_mb} MB).")
    return data, content_type


def _put_object(key: str, body: bytes, content_type: str) -> str:
    settings = get_settings()
    try:
        _s3_client().put_object(
            Bucket=settings.r2_bucket_name,
            Key=key,
            Body=body,
            ContentType=content_type,
        )
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=502, detail=f"R2 upload failed: {exc}") from exc
    return public_url(key)


async def upload_image(file: UploadFile, *, folder: str = "cms") -> str:
    """Upload an image to Cloudflare R2 and return its public URL."""
    if not r2_configured():
        raise HTTPException(
            status_code=503,
            detail="Cloudflare R2 is not configured. Set R2_* environment variables.",
        )

    data, content_type = await _read_file(file, MAX_IMAGE_BYTES)
    if content_type not in IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image type. Use JPG, PNG, GIF, or WebP.",
        )

    ext = _extension(content_type, file.filename, IMAGE_CONTENT_TYPES[content_type])
    key = f"{_safe_folder(folder)}/{uuid.uuid4().hex}{ext}"
    return _put_object(key, data, content_type)


async def upload_article_media(file: UploadFile) -> tuple[str, str]:
    """Upload image or video for blog articles. Returns (public_url, media_type)."""
    if not r2_configured():
        raise HTTPException(
            status_code=503,
            detail="Cloudflare R2 is not configured. Set R2_* environment variables.",
        )

    data, content_type = await _read_file(file, MAX_VIDEO_BYTES)
    if content_type in IMAGE_CONTENT_TYPES:
        media_type = "image"
        max_bytes = MAX_IMAGE_BYTES
        ext = _extension(content_type, file.filename, IMAGE_CONTENT_TYPES[content_type])
        folder = "blog"
    elif content_type in VIDEO_CONTENT_TYPES:
        media_type = "video"
        max_bytes = MAX_VIDEO_BYTES
        ext = _extension(content_type, file.filename, VIDEO_CONTENT_TYPES[content_type])
        folder = "blog"
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use JPG, PNG, GIF, WebP, MP4, WebM, or MOV.",
        )

    if len(data) > max_bytes:
        limit_mb = max_bytes // (1024 * 1024)
        raise HTTPException(status_code=400, detail=f"File too large (max {limit_mb} MB).")

    key = f"{folder}/{uuid.uuid4().hex}{ext}"
    return _put_object(key, data, content_type), media_type


async def upload_document(file: UploadFile, *, folder: str = "mentorship") -> tuple[str, str, int]:
    """Upload a PDF document to Cloudflare R2. Returns (public_url, file_name, size_bytes)."""
    if not r2_configured():
        raise HTTPException(
            status_code=503,
            detail="Cloudflare R2 is not configured. Set R2_* environment variables.",
        )

    data, content_type = await _read_file(file, MAX_DOCUMENT_BYTES)
    if content_type not in PDF_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported document type. Use PDF only.",
        )

    ext = _extension(content_type, file.filename, PDF_CONTENT_TYPES[content_type])
    key = f"{_safe_folder(folder)}/{uuid.uuid4().hex}{ext}"
    url = _put_object(key, data, content_type)
    file_name = (file.filename or "").strip() or f"document{ext}"
    return url, file_name, len(data)
