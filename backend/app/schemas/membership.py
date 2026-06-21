from pydantic import BaseModel, Field


class MembershipModule(BaseModel):
    title: str
    description: str


class MembershipTier(BaseModel):
    name: str
    price: str
    period: str = "/ year"
    features: list[str] = Field(default_factory=list)
    highlighted: bool = False
    cta_text: str = "Enroll Now"
    cta_link: str = "#enroll"


class MembershipContent(BaseModel):
    eyebrow: str
    title_before: str
    title_highlight: str
    intro: str
    page_description: str = ""
    overview_title: str
    overview_text: str
    modules: list[MembershipModule] = Field(default_factory=list)
    tiers: list[MembershipTier] = Field(min_length=1, max_length=3)
    benefits: list[str] = Field(default_factory=list)
    certification_title: str
    certification_text: str
    certification_outcomes: list[str] = Field(default_factory=list)
    enroll_title: str
    enroll_subtitle: str
    enroll_button_text: str
    enroll_link: str
