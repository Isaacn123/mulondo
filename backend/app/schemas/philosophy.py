from pydantic import BaseModel, Field


class PhilosophyPillar(BaseModel):
    number: str
    title: str
    description: str
    highlighted: bool = False


class PhilosophyContent(BaseModel):
    eyebrow: str
    title_before: str
    title_highlight: str
    intro: str
    pullquote: str
    pillars: list[PhilosophyPillar] = Field(min_length=3, max_length=3)
