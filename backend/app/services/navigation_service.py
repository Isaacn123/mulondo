import json
from pathlib import Path

from app.schemas.content_defaults import default_navigation
from app.schemas.navigation import NavigationContent, NavLink

BASE_DIR = Path(__file__).resolve().parent.parent
NAVIGATION_FILE = BASE_DIR / "data" / "navigation.json"


def load_navigation() -> NavigationContent:
    if NAVIGATION_FILE.is_file():
        try:
            return NavigationContent.model_validate_json(NAVIGATION_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            pass
    return default_navigation()


def save_navigation(content: NavigationContent) -> NavigationContent:
    NAVIGATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with NAVIGATION_FILE.open("w", encoding="utf-8") as handle:
        json.dump(content.model_dump(), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return content


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
