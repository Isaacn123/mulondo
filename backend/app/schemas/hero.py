from pydantic import BaseModel, Field, model_validator


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
    show_meta_stats: bool = False
    meta_stats: list[MetaStat]
    show_extras_image: bool = True
    extras_caption: str = "Global markets & Africa-native perspective"
    extras_image: HeroImage = Field(default_factory=HeroImage)
    panel: HeroPanel
    float_cards: list[FloatCard]
    image: HeroImage = Field(default_factory=HeroImage)

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_globe_fields(cls, data):
        if not isinstance(data, dict):
            return data
        if "show_extras_image" not in data:
            if "show_globe" in data:
                data["show_extras_image"] = bool(data.get("show_globe"))
            else:
                data["show_extras_image"] = True
        if "extras_image" not in data:
            data["extras_image"] = {"src": "", "alt": "", "object_position": "center"}
        extras = data.get("extras_image") or {}
        extras_src = extras.get("src", "") if isinstance(extras, dict) else ""
        if extras_src and str(extras_src).strip() and data.get("show_extras_image") is False:
            data["show_extras_image"] = True
        if "extras_caption" not in data and "globe_caption" in data:
            data["extras_caption"] = data.get("globe_caption", "")
        return data
