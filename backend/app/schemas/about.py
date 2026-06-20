from pydantic import BaseModel, Field


class AboutImage(BaseModel):
    src: str
    alt: str
    width: int = 896
    height: int = 1195


class AboutContent(BaseModel):
    image: AboutImage
    badges: list[str] = Field(min_length=2, max_length=2)
    eyebrow: str
    title_before: str
    title_highlight: str
    lead: str
    role_prefix: str = "As "
    role_title: str
    company_name: str
    company_url: str
    body_after: str
    highlights: list[str] = Field(min_length=1)
    cta_text: str
    cta_link: str
