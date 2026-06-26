from pathlib import Path

from app.schemas.content_defaults import default_ai_banner
from app.services import cms_document_service

BASE_DIR = Path(__file__).resolve().parent.parent
AI_BANNER_FILE = BASE_DIR / "data" / "ai_banner.json"
AI_BANNER_SLUG = "ai_banner"


def load_ai_banner() -> dict:
    return cms_document_service.load_dict(
        slug=AI_BANNER_SLUG,
        json_path=AI_BANNER_FILE,
        default_factory=default_ai_banner,
    )


def save_ai_banner(data: dict) -> dict:
    return cms_document_service.save_dict(
        slug=AI_BANNER_SLUG,
        data=data,
        json_path=AI_BANNER_FILE,
    )


def delete_ai_banner() -> bool:
    return cms_document_service.delete_document(slug=AI_BANNER_SLUG, json_path=AI_BANNER_FILE)
