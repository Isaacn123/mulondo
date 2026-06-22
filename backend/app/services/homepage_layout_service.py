import json
from pathlib import Path

from app.schemas.content_defaults import default_homepage_layout
from app.schemas.homepage_layout import HomepageLayout, HomepageSection

BASE_DIR = Path(__file__).resolve().parent.parent
LAYOUT_FILE = BASE_DIR / "data" / "homepage_layout.json"


def load_homepage_layout() -> HomepageLayout:
    if LAYOUT_FILE.is_file():
        try:
            return HomepageLayout.model_validate_json(LAYOUT_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            pass
    return default_homepage_layout()


def save_homepage_layout(content: HomepageLayout) -> HomepageLayout:
    LAYOUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LAYOUT_FILE.open("w", encoding="utf-8") as handle:
        json.dump(content.model_dump(), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return content


def sorted_sections(content: HomepageLayout) -> list[HomepageSection]:
    return sorted(content.sections, key=lambda section: (-section.sort_order, section.label.lower()))
