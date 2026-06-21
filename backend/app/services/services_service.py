import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.content_storage import load_cms_content
from app.database import SessionLocal
from app.models.services import ServicesSection
from app.schemas.content_defaults import default_services
from app.schemas.services import SERVICE_SLUGS, ServiceCard, ServicesContent

BASE_DIR = Path(__file__).resolve().parent.parent
SERVICES_FILE = BASE_DIR / "data" / "services.json"
SERVICES_SLUG = "homepage"


def _load_services_from_db(db: Session) -> ServicesContent | None:
    row = db.query(ServicesSection).filter(ServicesSection.slug == SERVICES_SLUG).one_or_none()
    if row is None:
        return None
    return ServicesContent.model_validate(row.content)


def _save_services_to_json(services: ServicesContent) -> ServicesContent:
    SERVICES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SERVICES_FILE.open("w", encoding="utf-8") as f:
        json.dump(services.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return services


def _save_services_to_db(db: Session, services: ServicesContent) -> ServicesContent:
    row = db.query(ServicesSection).filter(ServicesSection.slug == SERVICES_SLUG).one_or_none()
    payload = services.model_dump()
    if row is None:
        row = ServicesSection(slug=SERVICES_SLUG, content=payload)
        db.add(row)
    else:
        row.content = payload
    db.commit()
    db.refresh(row)
    return ServicesContent.model_validate(row.content)


def load_services() -> ServicesContent:
    return load_cms_content(
        model=ServicesContent,
        json_path=SERVICES_FILE,
        db_loader=_load_services_from_db,
        default_factory=default_services,
    )


def save_services(services: ServicesContent) -> ServicesContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_services_to_db(db, services)
        finally:
            db.close()
    return _save_services_to_json(services)


def get_service_card(slug: str) -> ServiceCard:
    if slug not in SERVICE_SLUGS:
        raise KeyError(slug)
    services = load_services()
    for card in services.cards:
        if card.slug == slug:
            return card
    raise KeyError(slug)


def update_service_card(slug: str, card: ServiceCard) -> ServicesContent:
    services = load_services()
    updated_cards = []
    found = False
    for existing in services.cards:
        if existing.slug == slug:
            updated_cards.append(card)
            found = True
        else:
            updated_cards.append(existing)
    if not found:
        raise KeyError(slug)
    return save_services(services.model_copy(update={"cards": updated_cards}))
