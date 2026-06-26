from pathlib import Path

from app.schemas.content_defaults import default_homepage_layout
from app.schemas.homepage_layout import HomepageLayout, HomepageSection
from app.services import cms_document_service

BASE_DIR = Path(__file__).resolve().parent.parent
LAYOUT_FILE = BASE_DIR / "data" / "homepage_layout.json"
LAYOUT_SLUG = "homepage_layout"


def load_homepage_layout() -> HomepageLayout:
    return cms_document_service.load_model(
        slug=LAYOUT_SLUG,
        model=HomepageLayout,
        json_path=LAYOUT_FILE,
        default_factory=default_homepage_layout,
    )


def save_homepage_layout(content: HomepageLayout) -> HomepageLayout:
    return cms_document_service.save_model(
        slug=LAYOUT_SLUG,
        content=content,
        json_path=LAYOUT_FILE,
    )


def delete_homepage_layout() -> bool:
    return cms_document_service.delete_document(slug=LAYOUT_SLUG, json_path=LAYOUT_FILE)


def sorted_sections(content: HomepageLayout) -> list[HomepageSection]:
    return sorted(content.sections, key=lambda section: (-section.sort_order, section.label.lower()))
