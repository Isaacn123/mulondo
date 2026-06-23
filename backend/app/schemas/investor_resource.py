from typing import Literal

from pydantic import BaseModel, Field


class InvestorResource(BaseModel):
    slug: str
    title: str
    description: str = ""
    file_url: str
    file_name: str = ""
    file_size_bytes: int = 0
    status: Literal["draft", "published"] = "draft"
    sort_order: int = 0


class InvestorResourceList(BaseModel):
    items: list[InvestorResource] = Field(default_factory=list)
