from typing import Literal

from pydantic import BaseModel, Field


class MediaItem(BaseModel):
    slug: str
    title: str
    description: str = ""
    location: str = ""
    event_date: str = ""
    category: str = ""
    media_type: Literal["image", "video"] = "image"
    media_url: str
    thumbnail_url: str = ""
    status: Literal["draft", "published"] = "draft"
    sort_order: int = 0


class MediaPageHeader(BaseModel):
    eyebrow: str
    title_before: str
    title_highlight: str
    intro: str
    page_description: str = ""


class MediaContent(MediaPageHeader):
    items: list[MediaItem] = Field(default_factory=list)
