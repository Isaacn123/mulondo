from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BlogPost(BaseModel):
    slug: str
    title: str
    excerpt: str = ""
    body: str = ""
    author: str = "Daniel Mulondo"
    published_at: str = ""
    status: Literal["draft", "published"] = "draft"
    created_at: str = ""
    updated_at: str = ""


class BlogStore(BaseModel):
    posts: list[BlogPost] = Field(default_factory=list)
