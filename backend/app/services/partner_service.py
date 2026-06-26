from pathlib import Path

from app.schemas.content_defaults import default_partner
from app.services import cms_document_service

BASE_DIR = Path(__file__).resolve().parent.parent
PARTNER_FILE = BASE_DIR / "data" / "partner.json"
PARTNER_SLUG = "partner"


def load_partner() -> dict:
    return cms_document_service.load_dict(
        slug=PARTNER_SLUG,
        json_path=PARTNER_FILE,
        default_factory=default_partner,
    )


def save_partner(data: dict) -> dict:
    return cms_document_service.save_dict(
        slug=PARTNER_SLUG,
        data=data,
        json_path=PARTNER_FILE,
    )


def delete_partner() -> bool:
    return cms_document_service.delete_document(slug=PARTNER_SLUG, json_path=PARTNER_FILE)
