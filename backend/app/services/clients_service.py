import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.content_storage import load_cms_content
from app.database import SessionLocal
from app.models.clients import ClientsSection
from app.schemas.clients import ClientsContent
from app.schemas.content_defaults import default_clients

BASE_DIR = Path(__file__).resolve().parent.parent
CLIENTS_FILE = BASE_DIR / "data" / "clients.json"
CLIENTS_SLUG = "homepage"


def _load_clients_from_db(db: Session) -> ClientsContent | None:
    row = db.query(ClientsSection).filter(ClientsSection.slug == CLIENTS_SLUG).one_or_none()
    if row is None:
        return None
    return ClientsContent.model_validate(row.content)


def _save_clients_to_json(clients: ClientsContent) -> ClientsContent:
    CLIENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CLIENTS_FILE.open("w", encoding="utf-8") as f:
        json.dump(clients.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return clients


def _save_clients_to_db(db: Session, clients: ClientsContent) -> ClientsContent:
    row = db.query(ClientsSection).filter(ClientsSection.slug == CLIENTS_SLUG).one_or_none()
    payload = clients.model_dump()
    if row is None:
        row = ClientsSection(slug=CLIENTS_SLUG, content=payload)
        db.add(row)
    else:
        row.content = payload
    db.commit()
    db.refresh(row)
    return ClientsContent.model_validate(row.content)


def load_clients() -> ClientsContent:
    return load_cms_content(
        model=ClientsContent,
        json_path=CLIENTS_FILE,
        db_loader=_load_clients_from_db,
        default_factory=default_clients,
    )


def save_clients(clients: ClientsContent) -> ClientsContent:
    if get_settings().storage_backend == "database":
        db = SessionLocal()
        try:
            return _save_clients_to_db(db, clients)
        finally:
            db.close()
    return _save_clients_to_json(clients)
