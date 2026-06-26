from pathlib import Path

from app.schemas.content_defaults import default_navigation
from app.schemas.navigation import NavigationContent, NavLink
from app.services import cms_document_service

BASE_DIR = Path(__file__).resolve().parent.parent
NAVIGATION_FILE = BASE_DIR / "data" / "navigation.json"
NAVIGATION_SLUG = "navigation"


def load_navigation() -> NavigationContent:
    return cms_document_service.load_model(
        slug=NAVIGATION_SLUG,
        model=NavigationContent,
        json_path=NAVIGATION_FILE,
        default_factory=default_navigation,
    )


def save_navigation(content: NavigationContent) -> NavigationContent:
    return cms_document_service.save_model(
        slug=NAVIGATION_SLUG,
        content=content,
        json_path=NAVIGATION_FILE,
    )


def delete_navigation() -> bool:
    return cms_document_service.delete_document(slug=NAVIGATION_SLUG, json_path=NAVIGATION_FILE)


def sorted_header_links(content: NavigationContent) -> list[NavLink]:
    return sorted(
        [link for link in content.links if link.enabled and link.show_in_header],
        key=lambda link: (-link.sort_order, link.label.lower()),
    )


def sorted_footer_links(content: NavigationContent) -> list[NavLink]:
    return sorted(
        [link for link in content.links if link.enabled and link.show_in_footer],
        key=lambda link: (-link.sort_order, link.label.lower()),
    )
