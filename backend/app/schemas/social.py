from pydantic import BaseModel, Field


class SocialLink(BaseModel):
    platform: str
    label: str
    url: str = ""
    enabled: bool = False


class SocialContent(BaseModel):
    links: list[SocialLink] = Field(default_factory=list)
