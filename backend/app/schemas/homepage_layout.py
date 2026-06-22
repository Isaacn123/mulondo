from pydantic import BaseModel, Field


class HomepageSection(BaseModel):
    key: str
    label: str
    element_id: str
    enabled: bool = True
    sort_order: int = 0


class HomepageLayout(BaseModel):
    sections: list[HomepageSection] = Field(default_factory=list)
