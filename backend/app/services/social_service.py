from pathlib import Path

from app.schemas.content_defaults import default_social
from app.schemas.social import SocialContent
from app.services import cms_document_service

BASE_DIR = Path(__file__).resolve().parent.parent
SOCIAL_FILE = BASE_DIR / "data" / "social.json"
SOCIAL_SLUG = "social"


def load_social() -> SocialContent:
    return cms_document_service.load_model(
        slug=SOCIAL_SLUG,
        model=SocialContent,
        json_path=SOCIAL_FILE,
        default_factory=default_social,
    )


def save_social(content: SocialContent) -> SocialContent:
    return cms_document_service.save_model(
        slug=SOCIAL_SLUG,
        content=content,
        json_path=SOCIAL_FILE,
    )


def delete_social() -> bool:
    return cms_document_service.delete_document(slug=SOCIAL_SLUG, json_path=SOCIAL_FILE)
