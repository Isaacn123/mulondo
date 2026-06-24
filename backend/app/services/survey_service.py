import json
from pathlib import Path

from app.schemas.content_defaults import default_survey
from app.schemas.survey import SurveyContent, SurveyOption, SurveyScreen

BASE_DIR = Path(__file__).resolve().parent.parent
SURVEY_FILE = BASE_DIR / "data" / "survey.json"


def load_survey() -> SurveyContent:
    if SURVEY_FILE.is_file():
        try:
            return SurveyContent.model_validate_json(SURVEY_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            pass
    return default_survey()


def save_survey(content: SurveyContent) -> SurveyContent:
    SURVEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SURVEY_FILE.open("w", encoding="utf-8") as handle:
        json.dump(content.model_dump(), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return content


def options_from_text(raw: str) -> list[SurveyOption]:
    options: list[SurveyOption] = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if "|" in line:
            label, value = line.split("|", 1)
            label = label.strip()
            value = value.strip() or label
        else:
            label = line
            value = line
        options.append(SurveyOption(label=label, value=value))
    return options


def options_to_text(options: list[SurveyOption]) -> str:
    return "\n".join(
        f"{option.label}|{option.value}" if option.value and option.value != option.label else option.label
        for option in options
    )


def screens_from_form(form) -> list[SurveyScreen]:
    keys = [key.strip() for key in form.getlist("screen_key") if key and str(key).strip()]
    screens: list[SurveyScreen] = []
    for key in keys:
        screen_type = (form.get(f"{key}_type") or "welcome").strip()
        if screen_type not in ("welcome", "choice", "text", "complete"):
            screen_type = "welcome"
        screens.append(
            SurveyScreen(
                key=key,
                type=screen_type,
                eyebrow=(form.get(f"{key}_eyebrow") or "").strip(),
                title=(form.get(f"{key}_title") or "").strip() or "Untitled screen",
                subtitle=(form.get(f"{key}_subtitle") or "").strip(),
                body=(form.get(f"{key}_body") or "").strip(),
                button_text=(form.get(f"{key}_button_text") or "Continue").strip(),
                placeholder=(form.get(f"{key}_placeholder") or "").strip(),
                options=options_from_text(form.get(f"{key}_options") or ""),
                allow_multiple=f"{key}_allow_multiple" in form,
                cta_link=(form.get(f"{key}_cta_link") or "").strip(),
            )
        )
    return screens
