from pydantic import BaseModel, Field


class CoverageContent(BaseModel):
    eyebrow: str
    title_before: str
    title_highlight: str
    title_after: str = ""
    countries: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
