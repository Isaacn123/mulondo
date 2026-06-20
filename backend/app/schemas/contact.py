from pydantic import BaseModel, Field


class ContactFormConfig(BaseModel):
    title: str
    subtitle: str
    action_url: str
    submit_text: str
    consent_text: str
    country_placeholder: str = "e.g. Uganda"
    message_placeholder: str = ""
    investor_types: list[str] = Field(default_factory=list)
    capital_ranges: list[str] = Field(default_factory=list)


class CalendlyConfig(BaseModel):
    title: str
    subtitle: str
    widget_url: str
    fallback_url: str
    widget_height: int = Field(default=680, ge=400, le=1200)


class ContactContent(BaseModel):
    eyebrow: str
    title_before: str
    title_highlight: str
    intro: str
    form: ContactFormConfig
    calendly: CalendlyConfig
