from pathlib import Path

from app.schemas.content_defaults import default_survey
from app.schemas.survey import SurveyContent, SurveyOption, SurveyScreen
from app.services import cms_document_service

BASE_DIR = Path(__file__).resolve().parent.parent
SURVEY_FILE = BASE_DIR / "data" / "survey.json"
SURVEY_SLUG = "survey"


def load_survey() -> SurveyContent:
    return cms_document_service.load_model(
        slug=SURVEY_SLUG,
        model=SurveyContent,
        json_path=SURVEY_FILE,
        default_factory=default_survey,
    )


def save_survey(content: SurveyContent) -> SurveyContent:
    return cms_document_service.save_model(
        slug=SURVEY_SLUG,
        content=content,
        json_path=SURVEY_FILE,
    )


def delete_survey() -> bool:
    return cms_document_service.delete_document(slug=SURVEY_SLUG, json_path=SURVEY_FILE)


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
