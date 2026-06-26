"""Seed cms_documents from JSON files in app/data.

Run after migration 025 when switching site settings to database storage:

    STORAGE_BACKEND=database python -m app.scripts.seed_cms_documents

Import only missing rows (safe for production):

    STORAGE_BACKEND=database python -m app.scripts.seed_cms_documents

Overwrite DB from JSON on disk (after updating app/data on the server):

    STORAGE_BACKEND=database python -m app.scripts.seed_cms_documents --overwrite
"""
from __future__ import annotations

import argparse
from pathlib import Path

from app.database import SessionLocal
from app.schemas.content_defaults import (
    default_credentials,
    default_homepage_layout,
    default_navigation,
    default_social,
    default_survey,
)
from app.schemas.credentials import CredentialsContent
from app.schemas.homepage_layout import HomepageLayout
from app.schemas.navigation import NavigationContent
from app.schemas.social import SocialContent
from app.schemas.survey import SurveyContent
from app.services import cms_document_service

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

MODEL_SEEDS = [
    ("navigation", "navigation.json", NavigationContent, default_navigation),
    ("homepage_layout", "homepage_layout.json", HomepageLayout, default_homepage_layout),
    ("social", "social.json", SocialContent, default_social),
    ("survey", "survey.json", SurveyContent, default_survey),
    ("credentials", "credentials.json", CredentialsContent, default_credentials),
]

DICT_SEEDS: list[tuple[str, str]] = [
    ("ai_banner", "ai_banner.json"),
    ("partner", "partner.json"),
]


def seed(*, overwrite: bool = False) -> list[str]:
    imported: list[str] = []
    db = SessionLocal()
    try:
        for slug, filename, model, _default in MODEL_SEEDS:
            path = DATA_DIR / filename
            if cms_document_service.seed_model_from_json(
                db,
                slug=slug,
                model=model,
                json_path=path,
                overwrite=overwrite,
            ):
                imported.append(slug)

        for slug, filename in DICT_SEEDS:
            path = DATA_DIR / filename
            if cms_document_service.seed_dict_from_json(
                db,
                slug=slug,
                json_path=path,
                overwrite=overwrite,
            ):
                imported.append(slug)
    finally:
        db.close()
    return imported


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed cms_documents from app/data JSON files.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing DB rows with content from JSON files.",
    )
    args = parser.parse_args()
    imported = seed(overwrite=args.overwrite)
    if imported:
        print("Imported into cms_documents:", ", ".join(imported))
    else:
        print("Nothing imported (JSON missing or rows already exist; use --overwrite to replace).")


if __name__ == "__main__":
    main()
