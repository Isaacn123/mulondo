from typing import Literal

from pydantic import BaseModel, Field


SurveyScreenType = Literal["welcome", "choice", "text", "complete"]


class SurveyOption(BaseModel):
    label: str
    value: str = ""


class SurveyScreen(BaseModel):
    key: str
    type: SurveyScreenType = "welcome"
    eyebrow: str = ""
    title: str
    subtitle: str = ""
    body: str = ""
    button_text: str = "Continue"
    placeholder: str = ""
    options: list[SurveyOption] = Field(default_factory=list)
    allow_multiple: bool = False
    cta_link: str = ""


class SurveyContent(BaseModel):
    eyebrow: str = "Money Academy"
    title_before: str = "Personalise Your"
    title_highlight: str = "Wealth Journey"
    intro: str = (
        "Answer a few quick questions and we'll help shape an action plan "
        "tailored to your goals."
    )
    cta_button_text: str = "Take the Survey"
    screens: list[SurveyScreen] = Field(default_factory=list)
