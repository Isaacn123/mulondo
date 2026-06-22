from pydantic import BaseModel, Field


class ButtonLink(BaseModel):
    text: str
    link: str


class MetaStat(BaseModel):
    value: int
    suffix: str = ""
    label: str


class Allocation(BaseModel):
    name: str
    percent: int = Field(ge=0, le=100)


class HeroPanel(BaseModel):
    tag: str
    live: str
    label: str
    value: str
    allocations: list[Allocation]
    foot_left: str
    foot_right: str


class FloatCard(BaseModel):
    key: str
    value: str


class HeroImage(BaseModel):
    src: str = ""
    alt: str = ""
    object_position: str = "center top"


class HeroContent(BaseModel):
    eyebrow_text: str
    title_before: str
    title_highlight: str
    subtitle: str
    primary_btn: ButtonLink
    secondary_btn: ButtonLink
    meta_stats: list[MetaStat]
    panel: HeroPanel
    float_cards: list[FloatCard]
    image: HeroImage = Field(default_factory=HeroImage)
