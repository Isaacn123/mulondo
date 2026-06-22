import json
from pathlib import Path

from app.schemas.content_defaults import default_social
from app.schemas.social import SocialContent

BASE_DIR = Path(__file__).resolve().parent.parent
SOCIAL_FILE = BASE_DIR / "data" / "social.json"


def load_social() -> SocialContent:
    if SOCIAL_FILE.is_file():
        try:
            return SocialContent.model_validate_json(SOCIAL_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            pass
    return default_social()


def save_social(content: SocialContent) -> SocialContent:
    SOCIAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SOCIAL_FILE.open("w", encoding="utf-8") as handle:
        json.dump(content.model_dump(), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return content
