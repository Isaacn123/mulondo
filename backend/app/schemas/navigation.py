from typing import Literal

from pydantic import BaseModel, Field


class NavLink(BaseModel):
    key: str
    label: str
    href: str
    enabled: bool = True
    show_in_header: bool = True
    show_in_footer: bool = False
    sort_order: int = 0
    style: Literal["link", "cta"] = "link"


class NavigationContent(BaseModel):
    links: list[NavLink] = Field(default_factory=list)
